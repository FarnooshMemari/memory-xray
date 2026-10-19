"""Gate G2: complete, rubric-valid, independent labels from two distinct people."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from mxr.labels import LABELER_FILES, REALISTIC, blank_labeler_file, label_gate

ROOT = Path(__file__).parents[1]
SCEN = {s: json.loads((ROOT / "scenarios" / f"{s}.json").read_text()) for s in REALISTIC}


def complete_labels(name):
    """A labeler who applies the rubric exactly as frozen."""
    d = blank_labeler_file()
    d["name"], d["date"] = name, "2026-10-17"
    for sid, lbl in d["labels"].items():
        sc = SCEN[sid]
        for rec, v in sc["rubric"]["scores"].items():
            lbl["records"][rec] = {"component": v["component"], "score": v["score"]}
        lbl["flip_target_score"] = sc["flip"]["score"]
        lbl["signal"] = sc["rubric"]["reference_answer"]
        lbl["flip_signal"] = sc["flip"]["reference_answer"]
    return d


def write(tmp_path, l1, l2):
    d = tmp_path / "labels"
    d.mkdir(parents=True, exist_ok=True)
    for f, data in zip(LABELER_FILES, (l1, l2)):
        if data is not None:
            (d / f).write_text(json.dumps(data) if not isinstance(data, str) else data)
    return d


def blocked(tmp_path, l1, l2):
    ok, rep = label_gate(write(tmp_path, l1, l2))
    assert not ok
    return rep["blocking"]


# ---- regression: the reported bug ----
def test_regression_null_record_labels_and_flip_scores_do_not_pass(tmp_path):
    """Before the fix this passed: names and signals filled, every record label and flip score null."""
    l1, l2 = blank_labeler_file(), blank_labeler_file()
    for d, name in ((l1, "Alice Example"), (l2, "Bob Example")):
        d["name"], d["date"] = name, "2026-10-17"
        for sid, lbl in d["labels"].items():
            lbl["signal"] = SCEN[sid]["rubric"]["reference_answer"]
            lbl["flip_signal"] = SCEN[sid]["flip"]["reference_answer"]
    b = blocked(tmp_path, l1, l2)
    assert sum(": component missing" in x for x in b) == 24   # 2 labelers x 3 scenarios x 4 records
    assert sum(": score missing" in x for x in b) == 24
    assert sum("flip_target_score missing" in x for x in b) == 6


def test_regression_same_person_twice_does_not_pass(tmp_path):
    b = blocked(tmp_path, complete_labels("Alice Example"), complete_labels("  alice   EXAMPLE "))
    assert any("same name" in x for x in b)


# ---- complete, valid labels pass ----
def test_two_complete_distinct_labelers_pass(tmp_path):
    ok, rep = label_gate(write(tmp_path, complete_labels("Alice Example"), complete_labels("Bob Example")))
    assert ok, rep["blocking"]
    assert rep["agreement"] == {"labeler_1_vs_frozen": "15/15", "labeler_2_vs_frozen": "15/15",
                                "labeler_1_vs_labeler_2": "15/15"}
    assert not rep["record_disagreements"] and not rep["inter_labeler_disagreements"]


def test_blank_files_block(tmp_path):
    ok, rep = label_gate(write(tmp_path, blank_labeler_file(), blank_labeler_file()))
    assert not ok and any("name missing" in b for b in rep["blocking"])


def test_shipped_ai_label_files_pass_and_match_amendment_4():
    ok, rep = label_gate()
    assert ok, rep["blocking"]
    assert rep["agreement"] == {"labeler_1_vs_frozen": "15/15", "labeler_2_vs_frozen": "15/15",
                                "labeler_1_vs_labeler_2": "15/15"}
    assert rep["validation_kind"] == "independent AI-assisted rubric validation"
    assert rep["human_annotation"] is False and rep["declared_labelers_match"] is True
    sums = dict(line.split()[::-1] for line in (ROOT / "records" / "labels_SHA256SUMS.txt").read_text().splitlines())
    assert rep["files"] == {f: sums[f"labels/{f}"] for f in LABELER_FILES}
    prov = (ROOT / "records" / "AI_LABELING_PROVENANCE.txt").read_bytes()
    assert hashlib.sha256(prov).hexdigest() == sums["AI_LABELING_PROVENANCE.txt"]
    assert b"NOT by human annotators" in prov


def test_declared_labeler_mismatch_is_reported(tmp_path):
    ok, rep = label_gate(write(tmp_path, complete_labels("Alice Example"), complete_labels("Bob Example")))
    assert ok and rep["declared_labelers_match"] is False


# ---- completeness and validity ----
@pytest.mark.parametrize("field,value,needle", [
    ("component", "X", "component missing or invalid"),
    ("component", None, "component missing or invalid"),
    ("score", 2, "score missing or invalid"),
    ("score", "1", "score missing or invalid"),
    ("score", True, "score missing or invalid"),
    ("score", 1.0, "score missing or invalid"),
    ("score", None, "score missing or invalid"),
])
def test_invalid_record_entries_block(tmp_path, field, value, needle):
    l2 = complete_labels("Bob Example")
    l2["labels"]["macro_b"]["records"]["E3"][field] = value
    b = blocked(tmp_path, complete_labels("Alice Example"), l2)
    assert any(needle in x and "labeler_2 macro_b E3" in x for x in b)


@pytest.mark.parametrize("field,value", [("signal", None), ("signal", "positive"),
                                         ("flip_signal", None), ("flip_target_score", None),
                                         ("flip_target_score", "+1")])
def test_missing_or_invalid_signals_and_flip_scores_block(tmp_path, field, value):
    l1 = complete_labels("Alice Example")
    l1["labels"]["macro_a"][field] = value
    b = blocked(tmp_path, l1, complete_labels("Bob Example"))
    assert any(field in x and "labeler_1 macro_a" in x for x in b)


def test_missing_name_date_file_or_scenario_blocks(tmp_path):
    l1 = complete_labels("Alice Example"); l1["date"] = ""
    assert any("date missing" in x for x in blocked(tmp_path, l1, complete_labels("Bob Example")))
    l1 = complete_labels("Alice Example"); del l1["labels"]["macro_c"]
    assert any("labels must cover exactly" in x for x in blocked(tmp_path / "a", l1, complete_labels("Bob Example")))
    assert any("labeler_2.json missing" in x for x in blocked(tmp_path / "b", complete_labels("Alice Example"), None))
    assert any("not valid JSON" in x for x in blocked(tmp_path / "c", complete_labels("Alice Example"), "{not json"))


def test_records_must_be_exactly_E1_to_E4(tmp_path):
    l1 = complete_labels("Alice Example")
    l1["labels"]["macro_a"]["records"]["E5"] = {"component": "P", "score": 1}
    assert any("records must be exactly" in x for x in blocked(tmp_path, l1, complete_labels("Bob Example")))


# ---- validation against the rubric ----
def test_signal_must_follow_from_the_labelers_own_scores(tmp_path):
    l1 = complete_labels("Alice Example")
    l1["labels"]["macro_c"]["records"]["E3"]["score"] = 0     # own total -1 -> Neutral, but signal says Negative
    b = blocked(tmp_path, l1, complete_labels("Bob Example"))
    assert any("does not follow from this labeler's own scores" in x and "macro_c" in x for x in b)


def test_flip_signal_must_follow_from_the_labelers_own_flip_score(tmp_path):
    l1 = complete_labels("Alice Example")
    l1["labels"]["macro_a"]["flip_target_score"] = 1          # flip total +2 -> Positive, but flip_signal says Neutral
    b = blocked(tmp_path, l1, complete_labels("Bob Example"))
    assert any("flip_signal Neutral does not follow" in x for x in b)


def test_signal_different_from_frozen_reference_blocks(tmp_path):
    l2 = complete_labels("Bob Example")
    for rec in ("E1", "E2", "E4"):                            # consistent with own scores (total -1 -> Neutral)
        l2["labels"]["macro_a"]["records"][rec]["score"] = 0
    l2["labels"]["macro_a"]["records"]["E3"]["score"] = -1
    l2["labels"]["macro_a"]["signal"] = "Neutral"
    l2["labels"]["macro_a"]["flip_target_score"] = 0
    l2["labels"]["macro_a"]["flip_signal"] = "Neutral"
    b = blocked(tmp_path, complete_labels("Alice Example"), l2)
    assert any("signal Neutral differs from frozen reference Positive" in x for x in b)
    assert not any("does not follow" in x for x in b)


# ---- disagreements are reported, not blocking, and nothing is changed ----
def test_record_disagreement_consistent_with_signal_is_reported_not_blocking(tmp_path):
    l2 = complete_labels("Bob Example")
    l2["labels"]["macro_a"]["records"]["E3"] = {"component": "G", "score": 0}   # total +3: still Positive
    l2["labels"]["macro_b"]["records"]["E3"]["component"] = "E"                # component only
    d = write(tmp_path, complete_labels("Alice Example"), l2)
    before = {f: hashlib.sha256((d / f).read_bytes()).hexdigest() for f in LABELER_FILES}
    ok, rep = label_gate(d)
    after = {f: hashlib.sha256((d / f).read_bytes()).hexdigest() for f in LABELER_FILES}
    assert ok, rep["blocking"]
    assert before == after and rep["files"] == before                         # read-only, hashes reported
    assert rep["record_disagreements"] == ["labeler_2 macro_a E3: G/+0 vs frozen G/-1",
                                           "labeler_2 macro_b E3: E/+1 vs frozen G/+1"]
    assert len(rep["inter_labeler_disagreements"]) == 2
    assert rep["agreement"]["labeler_2_vs_frozen"] == "13/15"
    assert rep["agreement"]["labeler_1_vs_labeler_2"] == "13/15"


def test_flip_score_disagreement_reported(tmp_path):
    l2 = complete_labels("Bob Example")
    l2["labels"]["macro_c"]["flip_target_score"] = 0           # flip total -1 -> Neutral, still consistent
    ok, rep = label_gate(write(tmp_path, complete_labels("Alice Example"), l2))
    assert ok and "labeler_2 macro_c flip E4: +0 vs frozen +1" in rep["record_disagreements"]


def test_frozen_scenarios_and_runs_untouched():
    from mxr.scenario_validation import verify_freeze
    assert verify_freeze()[0]
