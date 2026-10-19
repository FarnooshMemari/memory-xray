from mxr.citations import citation_messages, parse_citation

SHOWN = ["R7", "R3"]
MAP = {"R7": "E1", "R3": "E2", "R9": "E3", "R5": "E4"}


def test_ok_and_mapping():
    r = parse_citation('["R3"]', SHOWN, MAP)
    assert r["status"] == "ok" and r["canonical"] == ["E2"]


def test_surrounding_text_and_duplicates():
    r = parse_citation('Sure. ["R3", "R7", "R3"] is the list.', SHOWN, MAP)
    assert r["status"] == "ok" and r["ids"] == ["R3", "R7"] and r["canonical"] == ["E1", "E2"]


def test_empty_list_is_its_own_status():
    r = parse_citation("[]", SHOWN, MAP)
    assert r["status"] == "empty" and r["canonical"] == []


def test_id_not_shown_is_invalid():
    r = parse_citation('["R9"]', SHOWN, MAP)
    assert r["status"] == "invalid_id" and r["invalid"] == ["R9"]


def test_unparseable():
    assert parse_citation("I relied on R3.", SHOWN, MAP)["status"] == "unparseable"
    assert parse_citation("[R3]", SHOWN, MAP)["status"] == "unparseable"
    assert parse_citation("[1, 2]", SHOWN, MAP)["status"] == "unparseable"


def test_messages_fix_the_decision_in_context():
    m = citation_messages("Q", "Positive")
    assert [x["role"] for x in m] == ["user", "assistant", "user"]
    assert m[1]["content"] == "Signal: Positive"
