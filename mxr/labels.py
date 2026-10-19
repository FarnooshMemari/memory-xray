"""Gate G2: complete, rubric-valid, independent labels from two distinct people.

Each labeler fills a separate file, so neither sees the other's answers:
records/labels/labeler_1.json and records/labels/labeler_2.json.

The gate is read-only: it never modifies a label file. It blocks when any of
the following holds:
  * a file is missing or is not valid JSON;
  * a name or date is missing, or the two names are the same person
    (case and spacing ignored);
  * the scenarios are not exactly macro_a, macro_b, macro_c, or the records
    are not exactly E1-E4;
  * any record component or score, flip score, signal or flip signal is
    missing or invalid (components P/I/G/E/F; scores the integers -1, 0, +1;
    signals Positive/Neutral/Negative);
  * a labeler's signal does not follow from that labeler's own scores under
    the frozen rubric (original or flip);
  * a signal or flip signal differs from the frozen reference answer.

Record-level differences from the frozen scores, and between the two
labelers, are reported but do not block. Nothing is changed or corrected.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .design import CANONICAL, LABELS

ROOT = Path(__file__).resolve().parents[1]
LABELS_DIR = ROOT / "records" / "labels"
LABELER_FILES = ("labeler_1.json", "labeler_2.json")
REALISTIC = ("macro_a", "macro_b", "macro_c")

# Amendment 4: what the two G2 label files are. Recorded in every run manifest.
RUBRIC_VALIDATION = {
    "kind": "independent AI-assisted rubric validation",
    "human_annotation": False,
    "declared_labelers": {"labeler_1": "GPT-6", "labeler_2": "Gemini"},
    "provenance_file": "records/AI_LABELING_PROVENANCE.txt",
    "protocol_amendment": 4,
    "statement": ("The two G2 labelers were AI models (GPT-6 and Gemini), each filling its own file "
                  "independently. This is AI-assisted rubric validation, not human annotation, and "
                  "does not establish human inter-rater reliability."),
}


def _norm_name(name):
    return " ".join(str(name).split()).casefold()


def _valid_score(x):
    return isinstance(x, int) and not isinstance(x, bool) and x in (-1, 0, 1)


def _filled_text(x):
    return isinstance(x, str) and x.strip() != ""


def rubric_signal(total, thresholds):
    if total >= thresholds["positive_min"]:
        return "Positive"
    if total <= thresholds["negative_max"]:
        return "Negative"
    return "Neutral"


def _load_frozen(scen_dir):
    rubric = json.loads((scen_dir / "rubric_macro_v1.json").read_text())
    scen = {sid: json.loads((scen_dir / f"{sid}.json").read_text()) for sid in REALISTIC}
    return rubric, scen


def validate_labeler(data, who, rubric, scen):
    """Return (blocking issues, normalized entries or None) for one labeler file."""
    blocking = []
    if not isinstance(data, dict):
        return [f"{who}: file must contain a JSON object"], None
    if not _filled_text(data.get("name")):
        blocking.append(f"{who}: name missing")
    if not _filled_text(data.get("date")):
        blocking.append(f"{who}: date missing")
    labels = data.get("labels")
    if not isinstance(labels, dict) or set(labels) != set(REALISTIC):
        got = sorted(labels) if isinstance(labels, dict) else labels
        return blocking + [f"{who}: labels must cover exactly {list(REALISTIC)}, got {got}"], None
    comps = set(rubric["components"])
    th = rubric["thresholds"]
    entries = {}
    for sid in REALISTIC:
        lbl = labels[sid]
        sc = scen[sid]
        where = f"{who} {sid}"
        if not isinstance(lbl, dict):
            blocking.append(f"{where}: entry must be an object")
            continue
        recs = lbl.get("records")
        if not isinstance(recs, dict) or set(recs) != set(CANONICAL):
            blocking.append(f"{where}: records must be exactly {list(CANONICAL)}")
            continue
        complete = True
        for rec in CANONICAL:
            v = recs[rec] if isinstance(recs[rec], dict) else {}
            if v.get("component") not in comps:
                blocking.append(f"{where} {rec}: component missing or invalid ({v.get('component')!r}; "
                                f"use one of {sorted(comps)})")
                complete = False
            if not _valid_score(v.get("score")):
                blocking.append(f"{where} {rec}: score missing or invalid ({v.get('score')!r}; use -1, 0 or 1)")
                complete = False
        fts = lbl.get("flip_target_score")
        if not _valid_score(fts):
            blocking.append(f"{where}: flip_target_score missing or invalid ({fts!r}; use -1, 0 or 1) "
                            f"for flipped record {sc['flip']['target']}")
            complete = False
        for field in ("signal", "flip_signal"):
            if lbl.get(field) not in LABELS:
                blocking.append(f"{where}: {field} missing or invalid ({lbl.get(field)!r}; use one of {list(LABELS)})")
                complete = False
        if not complete:
            continue
        scores = {rec: recs[rec]["score"] for rec in CANONICAL}
        own = rubric_signal(sum(scores.values()), th)
        flipped = dict(scores, **{sc["flip"]["target"]: fts})
        own_flip = rubric_signal(sum(flipped.values()), th)
        if lbl["signal"] != own:
            blocking.append(f"{where}: signal {lbl['signal']} does not follow from this labeler's own scores "
                            f"(total {sum(scores.values()):+d} -> {own})")
        if lbl["flip_signal"] != own_flip:
            blocking.append(f"{where}: flip_signal {lbl['flip_signal']} does not follow from this labeler's own "
                            f"scores (flip total {sum(flipped.values()):+d} -> {own_flip})")
        if lbl["signal"] != sc["rubric"]["reference_answer"]:
            blocking.append(f"{where}: signal {lbl['signal']} differs from frozen reference "
                            f"{sc['rubric']['reference_answer']}")
        if lbl["flip_signal"] != sc["flip"]["reference_answer"]:
            blocking.append(f"{where}: flip_signal {lbl['flip_signal']} differs from frozen reference "
                            f"{sc['flip']['reference_answer']}")
        entries[sid] = {"records": {rec: (recs[rec]["component"], recs[rec]["score"]) for rec in CANONICAL},
                        "flip_target_score": fts}
    return blocking, (entries if len(entries) == len(REALISTIC) else None)


def label_gate(labels_dir=LABELS_DIR, scen_dir=ROOT / "scenarios"):
    """Read-only G2 check. Returns (ok, report)."""
    labels_dir, scen_dir = Path(labels_dir), Path(scen_dir)
    rubric, scen = _load_frozen(scen_dir)
    report = {"blocking": [], "record_disagreements": [], "inter_labeler_disagreements": [],
              "agreement": {}, "labelers": {}, "files": {}}
    entries, names = {}, {}
    for fname in LABELER_FILES:
        who = fname[:-5]
        path = labels_dir / fname
        if not path.exists():
            report["blocking"].append(f"{who}: file {path.name} missing")
            continue
        raw = path.read_bytes()
        report["files"][fname] = hashlib.sha256(raw).hexdigest()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            report["blocking"].append(f"{who}: not valid JSON ({exc.msg} at line {exc.lineno})")
            continue
        blocking, ent = validate_labeler(data, who, rubric, scen)
        report["blocking"] += blocking
        report["labelers"][who] = {"name": data.get("name") if isinstance(data, dict) else None,
                                   "date": data.get("date") if isinstance(data, dict) else None}
        if isinstance(data, dict) and _filled_text(data.get("name")):
            names[who] = _norm_name(data["name"])
        if ent is not None:
            entries[who] = ent
    if len(names) == 2 and len(set(names.values())) == 1:
        report["blocking"].append("labeler_1 and labeler_2 have the same name: two distinct people are required")

    # Disagreements: reported, never blocking, never changed.
    n_items = len(REALISTIC) * (len(CANONICAL) + 1)
    for who, ent in entries.items():
        agree = 0
        for sid in REALISTIC:
            frozen = scen[sid]["rubric"]["scores"]
            for rec in CANONICAL:
                comp, score = ent[sid]["records"][rec]
                if (comp, score) == (frozen[rec]["component"], frozen[rec]["score"]):
                    agree += 1
                else:
                    report["record_disagreements"].append(
                        f"{who} {sid} {rec}: {comp}/{score:+d} vs frozen {frozen[rec]['component']}/{frozen[rec]['score']:+d}")
            ffs = scen[sid]["flip"]["score"]
            if ent[sid]["flip_target_score"] == ffs:
                agree += 1
            else:
                report["record_disagreements"].append(
                    f"{who} {sid} flip {scen[sid]['flip']['target']}: {ent[sid]['flip_target_score']:+d} vs frozen {ffs:+d}")
        report["agreement"][f"{who}_vs_frozen"] = f"{agree}/{n_items}"
    if len(entries) == 2:
        a, b = entries["labeler_1"], entries["labeler_2"]
        agree = 0
        for sid in REALISTIC:
            for rec in CANONICAL:
                if a[sid]["records"][rec] == b[sid]["records"][rec]:
                    agree += 1
                else:
                    ca, sa = a[sid]["records"][rec]
                    cb, sb = b[sid]["records"][rec]
                    report["inter_labeler_disagreements"].append(
                        f"{sid} {rec}: labeler_1 {ca}/{sa:+d} vs labeler_2 {cb}/{sb:+d}")
            if a[sid]["flip_target_score"] == b[sid]["flip_target_score"]:
                agree += 1
            else:
                report["inter_labeler_disagreements"].append(
                    f"{sid} flip: labeler_1 {a[sid]['flip_target_score']:+d} vs labeler_2 {b[sid]['flip_target_score']:+d}")
        report["agreement"]["labeler_1_vs_labeler_2"] = f"{agree}/{n_items}"
    declared = RUBRIC_VALIDATION["declared_labelers"]
    report["validation_kind"] = RUBRIC_VALIDATION["kind"]
    report["human_annotation"] = RUBRIC_VALIDATION["human_annotation"]
    report["declared_labelers_match"] = all(
        _norm_name(report["labelers"].get(w, {}).get("name") or "") == _norm_name(n) for w, n in declared.items())
    return not report["blocking"], report


def blank_labeler_file():
    return {
        "name": None,
        "date": None,
        "instructions": ("Fill every null. component: one of P, I, G, E, F. score: -1, 0 or 1 (a number, "
                         "not text). flip_target_score: the score of the flipped record's new text. "
                         "signal / flip_signal: Positive, Neutral or Negative, following the rubric."),
        "labels": {sid: {"records": {rec: {"component": None, "score": None} for rec in CANONICAL},
                         "flip_target_score": None, "signal": None, "flip_signal": None}
                   for sid in REALISTIC},
    }
