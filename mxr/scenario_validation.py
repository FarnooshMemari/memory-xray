"""Offline validation of scenario authoring (no model involved).

Checks that each scenario is well-formed, de-identified and self-contained;
that its designed answers and designed attributions have the intended
structure; that rubric totals, reference answers and flips are consistent; and
that the frozen pass/fail criteria are satisfiable by ideal behavior and
violated by clearly wrong behavior.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

from . import checks, design
from .analysis import analyze
from .metrics import leave_one_out, shapley

ROOT = Path(__file__).resolve().parents[1]
SCEN_DIR = ROOT / "scenarios"
EXPERIMENT_SCENARIOS = ("s_single", "s_redundant", "s_conflict", "macro_a", "macro_b", "macro_c")
FROZEN_FILES = tuple(f"scenarios/{s}.json" for s in EXPERIMENT_SCENARIOS) + (
    "scenarios/rubric_macro_v1.json", "scenarios/validation_criteria.json")

# --- de-identification lists (case-insensitive, whole words) ---
_MONTHS = ("january february march april may june july august september october november december "
           "monday tuesday wednesday thursday friday saturday sunday").split()
_CENTRAL_BANKS = ["federal reserve", "european central bank", "ecb", "bank of england", "boe",
                  "bank of japan", "boj", "pboc", "people's bank", "reserve bank", "rbi", "rba",
                  "bundesbank", "riksbank", "norges", "swiss national bank", "snb", "bank of canada",
                  "banxico", "copom", "fomc"]
_CURRENCIES = ["dollar", "dollars", "euro", "euros", "yen", "pound", "pounds", "sterling", "yuan",
               "renminbi", "rupee", "rupees", "franc", "francs", "won", "peso", "pesos", "rand",
               "lira", "krona", "krone", "ruble", "rouble", "real", "reais"]
_PLACES = ["united states", "america", "american", "usa", "u.s.", "uk", "britain", "british", "england",
           "europe", "european", "eurozone", "euro area", "germany", "german", "france", "french",
           "italy", "italian", "spain", "spanish", "japan", "japanese", "china", "chinese", "india",
           "indian", "brazil", "brazilian", "mexico", "mexican", "canada", "canadian", "australia",
           "australian", "korea", "korean", "russia", "russian", "turkey", "turkish", "argentina",
           "switzerland", "swiss", "sweden", "norway", "south africa", "indonesia", "saudi",
           "new york", "london", "tokyo", "frankfurt", "beijing", "shanghai", "paris", "washington",
           "hong kong", "singapore", "zurich", "mumbai", "sydney", "toronto"]
_INDICES = ["s&p", "nasdaq", "dow", "ftse", "dax", "nikkei", "cac", "hang seng", "msci", "stoxx",
            "kospi", "sensex", "nifty", "bovespa"]
_FORBIDDEN = _MONTHS + _CENTRAL_BANKS + _CURRENCIES + _PLACES + _INDICES
_YEAR = re.compile(r"\b(18|19|20)\d\d\b")
_CROSS_REF = [re.compile(p, re.I) for p in (
    r"\b[ER]\d\b", r"\brecord\s+[A-Z0-9]\b", r"\b(above|below)-mentioned\b", r"\bprevious (record|report|item)\b",
    r"\bthe (former|latter)\b", r"\bas (noted|mentioned|stated) (above|earlier|before)\b", r"\bsee (above|below)\b")]
_ECONOMY = re.compile(r"\bEconomy ([A-Z])\b")


def _issue(sid, code, msg):
    return {"scenario": sid, "code": code, "message": msg}


def load_scenario(sid):
    return json.loads((SCEN_DIR / f"{sid}.json").read_text())


def deidentification_issues(sid, texts):
    issues = []
    for label, text in texts.items():
        low = text.lower()
        for term in _FORBIDDEN:
            if re.search(r"(?<![a-z])" + re.escape(term) + r"(?![a-z])", low):
                issues.append(_issue(sid, "deid", f"{label}: forbidden identifying term {term!r}"))
        if _YEAR.search(text):
            issues.append(_issue(sid, "deid", f"{label}: contains a calendar year"))
    return issues


def selfcontainment_issues(sid, records):
    issues = []
    for rec, text in records.items():
        for pat in _CROSS_REF:
            if pat.search(text):
                issues.append(_issue(sid, "selfref", f"{rec}: refers to another record ({pat.pattern})"))
    return issues


def designed_attribution(scenario, flipped=False):
    """Shapley and LOO of the ideal 0/1 lattice v(S) = 1[designed(S) == designed(full)]."""
    full = frozenset(design.CANONICAL)
    target = design.designed_answer(scenario, full, flipped)
    v = {s: float(design.designed_answer(scenario, s, flipped) == target) for s in design.all_subsets()}
    return target, shapley(v, design.CANONICAL), leave_one_out(v, design.CANONICAL), v


def _ideal_cells(scenario, p_hit=0.98, flipped=False):
    """Synthetic 'ideal model' cells that follow the design exactly in every ordering."""
    cells = []
    for k in range(len(design.ORDERINGS)):
        for s in design.all_subsets():
            ans = design.designed_answer(scenario, s, flipped)
            rest = (1 - p_hit) / 2
            p = {l: (p_hit if l == ans else rest) for l in design.LABELS}
            cells.append({"subset": design.subset_key(s), "subset_members": sorted(s), "ordering": k,
                          "score": {"p_norm": p}})
    return cells


def _violating_cells(scenario):
    """An evidence-blind 'model' that always answers Neutral with the same probabilities."""
    cells = _ideal_cells(scenario)
    for c in cells:
        c["score"]["p_norm"] = {"Positive": 0.1, "Neutral": 0.8, "Negative": 0.1}
    return cells


def _swap_roles(scenario):
    """A 'model' that follows the rule but treats a distractor as decisive."""
    sc = copy.deepcopy(scenario)
    rule = sc["designed"]["answer_rule"]
    distractor = sc["designed"]["distractors"][0]
    if rule["type"] == "contains_any":
        rule["records"] = [distractor]
    elif rule["type"] == "precedence":
        rule["order"][0]["record"] = distractor
    return sc


def validate(sid, crit, rubric):
    sc = load_scenario(sid)
    issues, info = [], {"scenario_id": sid, "kind": sc.get("kind"), "structure": sc.get("structure")}

    # schema
    for key in ("scenario_id", "kind", "structure", "question", "records", "designed"):
        if key not in sc:
            issues.append(_issue(sid, "schema", f"missing {key}"))
    if sc.get("scenario_id") != sid:
        issues.append(_issue(sid, "schema", "scenario_id does not match file name"))
    if sorted(sc.get("records", {})) != list(design.CANONICAL):
        issues.append(_issue(sid, "schema", "records must be exactly E1-E4"))
    if len(set(sc["records"].values())) != 4:
        issues.append(_issue(sid, "schema", "duplicate record texts"))

    texts = {"question": sc["question"], **{k: v for k, v in sc["records"].items()}}
    if "flip" in sc:
        texts["flip"] = sc["flip"]["record"]
    issues += deidentification_issues(sid, texts)
    issues += selfcontainment_issues(sid, sc["records"])
    letters = {m for t in texts.values() for m in _ECONOMY.findall(t)}
    info["economy_label"] = sorted(letters)
    if len(letters) != 1:
        issues.append(_issue(sid, "deid", f"economy labels must be one letter per scenario, found {sorted(letters)}"))

    words = {k: len(v.split()) for k, v in sc["records"].items()}
    info["record_words"] = words

    # rendering
    prompts = set()
    for k in range(len(design.ORDERINGS)):
        for s in design.all_subsets():
            r = design.render(sc, s, k)
            prompts.add(r["user_msg"])
            for rid in r["shown_ids"]:
                if r["user_msg"].count(f"[{rid}]") != 1:
                    issues.append(_issue(sid, "render", f"id {rid} not shown exactly once"))
    # The empty-set prompt shows no records, so it is identical in all 3 orderings:
    # 16 x 3 cells give 46 distinct prompts.
    empties = {design.render(sc, frozenset(), k)["user_msg"] for k in range(len(design.ORDERINGS))}
    if len(empties) != 1:
        issues.append(_issue(sid, "render", "empty-set prompt differs across orderings"))
    if len(prompts) != 46:
        issues.append(_issue(sid, "render", f"expected 46 distinct prompts, got {len(prompts)}"))
    info["prompt_chars"] = [min(len(p) for p in prompts), max(len(p) for p in prompts)]

    # designed lattice and designed attribution
    full = frozenset(design.CANONICAL)
    answers = {design.subset_key(s): design.designed_answer(sc, s) for s in design.all_subsets()}
    info["designed_answers"] = answers
    info["designed_full"] = answers[design.subset_key(full)]
    info["designed_empty"] = answers["none"]
    if info["designed_full"] == "Neutral":
        issues.append(_issue(sid, "design", "designed full-set answer is Neutral (low identifiability)"))
    if info["designed_empty"] != "Neutral":
        issues.append(_issue(sid, "design", "designed empty-set answer should be Neutral"))
    target, phi, loo, _ = designed_attribution(sc)
    info["designed_shapley"] = {k: round(v, 4) for k, v in phi.items()}
    info["designed_loo"] = {k: round(v, 4) for k, v in loo.items()}

    structure = sc["structure"]
    d = sc["designed"]
    if structure == "single_decisive":
        expect = {r: (1.0 if r in d["decisive"] else 0.0) for r in design.CANONICAL}
    elif structure == "redundant":
        expect = {r: (0.5 if r in d["redundant"] else 0.0) for r in design.CANONICAL}
    elif structure == "conflict":
        expect = {r: (1.0 if r in d["dominant"] else 0.0) for r in design.CANONICAL}
    else:
        expect = None
    if expect is not None:
        for r in design.CANONICAL:
            if abs(phi[r] - expect[r]) > 1e-12:
                issues.append(_issue(sid, "design", f"designed Shapley of {r} is {phi[r]}, expected {expect[r]}"))
        for fc in d.get("faithful_citations", []):
            if not set(fc) <= set(design.CANONICAL):
                issues.append(_issue(sid, "design", f"faithful citation {fc} has unknown records"))

    # rubric and flip
    if structure == "rubric":
        rb = sc["rubric"]
        comps = [v["component"] for v in rb["scores"].values()]
        if sorted(rb["scores"]) != list(design.CANONICAL):
            issues.append(_issue(sid, "rubric", "rubric must score E1-E4"))
        if len(set(comps)) != 4 or not set(comps) <= set(rubric["components"]):
            issues.append(_issue(sid, "rubric", f"each record needs a distinct valid component, got {comps}"))
        if any(v["score"] not in (-1, 0, 1) for v in rb["scores"].values()):
            issues.append(_issue(sid, "rubric", "scores must be -1, 0 or +1"))
        if sc["designed"]["answer_rule"]["thresholds"] != rubric["thresholds"]:
            issues.append(_issue(sid, "rubric", "thresholds differ from the shared rubric"))
        total = design.rubric_total(sc, full)
        if total != rb["total"] or design.designed_answer(sc, full) != rb["reference_answer"]:
            issues.append(_issue(sid, "rubric", "stated total or reference answer does not follow from the scores"))
        fl = sc["flip"]
        if fl["target"] not in design.CANONICAL or fl["record"] == sc["records"][fl["target"]]:
            issues.append(_issue(sid, "flip", "flip must replace one existing record with new text"))
        if fl["score"] == rb["scores"][fl["target"]]["score"]:
            issues.append(_issue(sid, "flip", "flip does not change the target record's score"))
        ftotal = design.rubric_total(sc, full, flipped=True)
        fans = design.designed_answer(sc, full, flipped=True)
        if ftotal != fl["total"] or fans != fl["reference_answer"]:
            issues.append(_issue(sid, "flip", "stated flip total or answer does not follow from the scores"))
        if fans == rb["reference_answer"]:
            issues.append(_issue(sid, "flip", "flip does not change the rubric answer"))
        frender = design.render(sc, full, 0, records=design.flip_records(sc))["user_msg"]
        if fl["record"] not in frender or sc["records"][fl["target"]] in frender:
            issues.append(_issue(sid, "flip", "flip rendering failed"))
        info["rubric_total"] = total
        info["reference_answer"] = rb["reference_answer"]
        info["flip"] = {"target": fl["target"], "total": ftotal, "reference_answer": fans}
        _, fphi, _, _ = designed_attribution(sc, flipped=True)
        info["rubric_lattice_designed_shapley"] = {k: round(v, 4) for k, v in phi.items()}

    # criteria are satisfiable by ideal behavior and violated by wrong behavior
    if structure != "rubric":
        ideal = checks.behavioral_checks(analyze(_ideal_cells(sc), sc), sc, crit)
        blind = checks.behavioral_checks(analyze(_violating_cells(sc), sc), sc, crit)
        swapped = checks.behavioral_checks(analyze(_ideal_cells(_swap_roles(sc)), sc), sc, crit)
        info["criteria_ideal_pass"] = all(c["passed"] for c in ideal)
        info["criteria_blind_fail"] = [c["id"] for c in blind if not c["passed"]]
        info["criteria_swapped_fail"] = [c["id"] for c in swapped if not c["passed"]]
        if not info["criteria_ideal_pass"]:
            issues.append(_issue(sid, "criteria", "ideal behavior fails the frozen criteria: "
                                 + str([c["id"] for c in ideal if not c["passed"]])))
        if not info["criteria_blind_fail"]:
            issues.append(_issue(sid, "criteria", "evidence-blind behavior passes the criteria"))
        if not info["criteria_swapped_fail"]:
            issues.append(_issue(sid, "criteria", "distractor-driven behavior passes the criteria"))
    return sc, issues, info


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def freeze_manifest(root=ROOT):
    out = {}
    for rel in FROZEN_FILES:
        out[rel] = sha256(Path(root) / rel)
    return out


def verify_freeze(root=ROOT):
    """Return (ok, mismatches). Every frozen file must match its recorded hash."""
    frozen = json.loads((Path(root) / "scenarios" / "FREEZE.json").read_text())
    current = freeze_manifest(root)
    mismatches = [rel for rel, h in frozen["files"].items() if current.get(rel) != h]
    missing = [rel for rel in current if rel not in frozen["files"]]
    return (not mismatches and not missing), mismatches + missing
