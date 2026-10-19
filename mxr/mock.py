"""Deterministic MOCK scorer for exercising the pipeline without a model.

It is a test double only: its probabilities are hand-written rules, not model
outputs. Runs made with it are labeled MOCK everywhere and must never be
reported as results.
"""
from __future__ import annotations

import hashlib
import json
import math

from .design import LABELS
from .scoring import summarize_label_logprobs


class MockLabelScorer:
    def __init__(self, decisive_text: str, positive_label="Positive"):
        self.decisive_text = decisive_text
        self.positive_label = positive_label
        self.meta = {"backend": "MOCK", "model_name": "MOCK-rule-scorer",
                     "note": "test double; not a language model"}

    def _jitter(self, user_msg):
        h = int(hashlib.sha256(user_msg.encode()).hexdigest()[:8], 16)
        return (h / 0xFFFFFFFF - 0.5) * 0.04

    def template_roundtrip(self, user_msg):
        return {"ok": True, "len_template": None, "len_string": None, "mock": True}

    def label_tokenization(self, user_msg):
        return {"prompt_len": None, "label_ids": {l: [i] for i, l in enumerate(LABELS)},
                "label_tokens": {l: [l] for l in LABELS}, "mock": True}

    def score(self, user_msg, top_n=5):
        j = self._jitter(user_msg)
        if self.decisive_text in user_msg:
            p = {"Positive": 0.90 + j, "Neutral": 0.07 - j, "Negative": 0.02}
        else:
            p = {"Positive": 0.06 + j, "Neutral": 0.90 - j, "Negative": 0.03}
        out = summarize_label_logprobs({k: math.log(v) for k, v in p.items()})
        out.update({
            "labels": {k: {"token_ids": [i], "token_logprobs": [math.log(p[k])],
                           "logprob": math.log(p[k])} for i, k in enumerate(LABELS)},
            "prompt_len": None, "n_forward": 1,
            "first_token_mass": out["label_mass"],
            "max_first_token_recompute_diff": 0.0, "top_next_tokens": [], "mock": True,
        })
        return out

    def greedy(self, user_msg, max_new_tokens=6):
        best = self.score(user_msg)["argmax"]
        return {"token_ids": [LABELS.index(best)], "text": " " + best, "mock": True}


class DesignMockScorer:
    """MOCK scorer that follows every scenario's designed answer (rubric for realistic).

    Plumbing tests only. Citation replies cycle through faithful, all-record,
    empty and unparseable outputs so that every parser status is exercised.
    """

    def __init__(self, scenarios):
        import re

        from . import design

        self._re = re
        self._design = design
        self.meta = {"backend": "MOCK", "model_name": "MOCK-design-scorer",
                     "note": "test double; not a language model"}
        self._texts = {}
        self._scen = {}
        for sc in scenarios:
            self._scen[sc["scenario_id"]] = sc
            for rec, text in sc["records"].items():
                self._texts[text] = (sc["scenario_id"], rec, False)
            if "flip" in sc:
                self._texts[sc["flip"]["record"]] = (sc["scenario_id"], sc["flip"]["target"], True)

    def _parse(self, user_msg):
        found, sid, flipped, id_map = set(), None, False, {}
        for line in user_msg.splitlines():
            m = self._re.match(r"\[(R\d)\] (.*)$", line)
            if m and m.group(2) in self._texts:
                sid, rec, fl = self._texts[m.group(2)]
                found.add(rec)
                flipped = flipped or fl
                id_map[m.group(1)] = rec
        if sid is None:
            for sc in self._scen.values():
                if sc["question"] in user_msg:
                    sid = sc["scenario_id"]
        return sid, frozenset(found), flipped, id_map

    def template_roundtrip(self, user_msg):
        return {"ok": True, "len_template": None, "len_string": None, "mock": True}

    def label_tokenization(self, user_msg):
        return {"prompt_len": None, "label_ids": {l: [i] for i, l in enumerate(LABELS)},
                "label_tokens": {l: [l] for l in LABELS}, "mock": True}

    def score(self, user_msg, top_n=5):
        sid, recs, flipped, _ = self._parse(user_msg)
        ans = self._design.designed_answer(self._scen[sid], recs, flipped)
        j = (int(hashlib.sha256(user_msg.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF - 0.5) * 0.02
        p = {l: (0.90 + j if l == ans else (0.10 - j) / 2) for l in LABELS}
        out = summarize_label_logprobs({k: math.log(v) for k, v in p.items()})
        out.update({
            "labels": {k: {"token_ids": [i], "token_logprobs": [math.log(p[k])], "logprob": math.log(p[k])}
                       for i, k in enumerate(LABELS)},
            "prompt_len": None, "n_forward": 1, "first_token_mass": out["label_mass"],
            "max_first_token_recompute_diff": 0.0, "top_next_tokens": [], "mock": True,
        })
        return out

    def greedy(self, user_msg, max_new_tokens=6):
        best = self.score(user_msg)["argmax"]
        return {"token_ids": [LABELS.index(best)], "text": " " + best, "mock": True}

    def generate_chat(self, messages, max_new_tokens=40, temperature=1.0, seed=0):
        sid, recs, _, id_map = self._parse(messages[0]["content"])
        sc = self._scen[sid]
        inv = {rec: rid for rid, rec in id_map.items()}
        fcs = self._design.faithful_citations(sc)
        if fcs:
            faithful = fcs[0]
        else:
            ref = sc["rubric"]["reference_answer"]
            sign = 1 if ref == "Positive" else -1
            faithful = [r for r, v in sc["rubric"]["scores"].items() if v["score"] == sign]
        mode = 0 if temperature == 0 else (seed % 4)
        if mode == 0:
            return json.dumps([inv[r] for r in faithful])
        if mode == 1:
            return json.dumps(sorted(id_map))
        if mode == 2:
            return "[]"
        return "I relied on the policy record."
