"""Citation elicitation (second turn) and strict parsing.

Implemented and unit-tested; not executed in the S-single feasibility test.
"""
from __future__ import annotations

import json
import re

from .design import ANSWER_PREFIX, CITATION_FOLLOWUP

_ARRAY = re.compile(r"\[[^\[\]]*\]", re.S)


def citation_messages(user_msg: str, decided_label: str) -> list[dict]:
    """Conversation for the citation turn: the decision is already fixed in context."""
    return [
        {"role": "user", "content": user_msg},
        {"role": "assistant", "content": f"{ANSWER_PREFIX} {decided_label}"},
        {"role": "user", "content": CITATION_FOLLOWUP},
    ]


def parse_citation(text: str, shown_ids, id_to_canonical) -> dict:
    """Parse the first JSON list in ``text``.

    status: ok | empty | invalid_id | unparseable. Only 'ok' and 'empty'
    enter the analysis; others are counted and reported.
    """
    match = _ARRAY.search(text or "")
    if not match:
        return {"status": "unparseable", "raw": text, "ids": None, "canonical": None}
    try:
        items = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"status": "unparseable", "raw": text, "ids": None, "canonical": None}
    if not isinstance(items, list) or not all(isinstance(x, str) for x in items):
        return {"status": "unparseable", "raw": text, "ids": None, "canonical": None}
    ids = []
    for item in items:
        item = item.strip()
        if item not in ids:
            ids.append(item)
    shown = set(shown_ids)
    bad = [i for i in ids if i not in shown]
    if bad:
        return {"status": "invalid_id", "raw": text, "ids": ids, "invalid": bad, "canonical": None}
    canonical = sorted(id_to_canonical[i] for i in ids)
    return {
        "status": "empty" if not ids else "ok",
        "raw": text,
        "ids": ids,
        "canonical": canonical,
    }
