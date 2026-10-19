import json
from pathlib import Path

from mxr import design

SCENARIO = json.loads((Path(__file__).parents[1] / "scenarios" / "s_single.json").read_text())


def test_sixteen_unique_subsets():
    subs = design.all_subsets()
    assert len(subs) == 16 and len(set(subs)) == 16
    assert {design.subset_mask(s) for s in subs} == set(range(16))
    for s in subs:
        assert design.parse_subset_key(design.subset_key(s)) == s


def test_each_record_takes_three_distinct_positions():
    for i in range(4):
        positions = [order.index(i) for order in design.ORDERINGS]
        assert len(set(positions)) == 3


def test_opaque_ids_unique_within_ordering_and_remapped_across():
    for ids in design.OPAQUE_IDS:
        assert len(set(ids.values())) == 4
    for rec in design.CANONICAL:
        assert len({ids[rec] for ids in design.OPAQUE_IDS}) == 3


def test_render_deletes_removed_records_and_keeps_relative_order():
    for k in range(3):
        for s in design.all_subsets():
            r = design.render(SCENARIO, s, k)
            for rec in design.CANONICAL:
                text = SCENARIO["records"][rec]
                assert (text in r["user_msg"]) == (rec in s)
            order = [design.CANONICAL[i] for i in design.ORDERINGS[k]]
            assert r["shown_canonical"] == [x for x in order if x in s]
            if not s:
                assert design.EMPTY_RECORDS_LINE in r["user_msg"]
            else:
                assert design.EMPTY_RECORDS_LINE not in r["user_msg"]
                offsets = [r["user_msg"].index(f"[{i}]") for i in r["shown_ids"]]
                assert offsets == sorted(offsets)


def test_instructions_identical_across_cells():
    head = design.USER_TEMPLATE.split("{records_block}")[0].format(question=SCENARIO["question"])
    tail = design.USER_TEMPLATE.split("{records_block}")[1]
    for k in range(3):
        for s in design.all_subsets():
            msg = design.render(SCENARIO, s, k)["user_msg"]
            assert msg.startswith(head) and msg.endswith(tail)


def test_designed_answer_rule():
    for s in design.all_subsets():
        expected = "Positive" if "E2" in s else "Neutral"
        assert design.designed_answer(SCENARIO, s) == expected


def test_fingerprint_is_stable_and_sensitive():
    a = design.design_fingerprint(SCENARIO)
    assert a == design.design_fingerprint(json.loads(json.dumps(SCENARIO)))
    changed = json.loads(json.dumps(SCENARIO))
    changed["records"]["E1"] += " "
    assert design.design_fingerprint(changed) != a
