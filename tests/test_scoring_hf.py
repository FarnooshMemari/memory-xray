"""Real Hugging Face code path on a tiny random model (offline)."""
import json
import math
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")

from mxr import design  # noqa: E402
from tests.tiny_hf import tiny_scorer  # noqa: E402

SCEN = json.loads((Path(__file__).parents[1] / "scenarios" / "s_single.json").read_text())


@pytest.fixture(scope="module", params=[300, 2000], ids=["multi-token-labels", "larger-vocab"])
def scorer(request):
    return tiny_scorer(vocab_size=request.param)


def _msg(subset=frozenset(design.CANONICAL), k=0):
    return design.render(SCEN, subset, k)["user_msg"]


def independent_label_logprob(sc, user_msg, label_ids):
    """One full-sequence forward pass, gathered independently of HFLabelScorer.score."""
    ids = sc._tokenize(sc.prompt_text(user_msg) + design.ANSWER_PREFIX)
    seq = torch.tensor([ids + label_ids])
    with torch.inference_mode():
        logits = sc.model(input_ids=seq).logits[0].float()
    lp = torch.log_softmax(logits, dim=-1)
    n = len(ids)
    return sum(float(lp[n - 1 + j, t]) for j, t in enumerate(label_ids))


def test_template_roundtrip(scorer):
    assert scorer.template_roundtrip(_msg())["ok"]


def test_label_tokens_are_suffixes_and_decode_back(scorer):
    info = scorer.label_tokenization(_msg())
    for label, ids in info["label_ids"].items():
        assert scorer.tok.decode(ids) == " " + label


def test_scores_match_independent_full_sequence_computation(scorer):
    for subset in (frozenset(), frozenset({"E2"}), frozenset(design.CANONICAL)):
        msg = _msg(subset, 1)
        res = scorer.score(msg)
        assert res["finite"]
        for label, entry in res["labels"].items():
            ref = independent_label_logprob(scorer, msg, entry["token_ids"])
            assert math.isclose(entry["logprob"], ref, abs_tol=1e-4), label
        assert res["max_first_token_recompute_diff"] < 1e-4
        assert math.isclose(sum(res["p_norm"].values()), 1.0, abs_tol=1e-9)
        assert math.isclose(res["label_mass"], sum(math.exp(e["logprob"]) for e in res["labels"].values()))


def test_scored_position_is_the_position_generate_uses(scorer):
    """The next-token argmax at the scored position must equal generate()'s first token."""
    msg = _msg()
    ids = scorer._tokenize(scorer.prompt_text(msg) + design.ANSWER_PREFIX)
    n = len(ids)
    first = scorer._logprobs_at(ids, [n - 1])[n - 1]
    g = scorer.greedy(msg, max_new_tokens=3)
    assert int(torch.argmax(first)) == g["token_ids"][0]


def test_rescoring_is_repeatable(scorer):
    a, b = scorer.score(_msg()), scorer.score(_msg())
    for label in design.LABELS:
        assert a["labels"][label]["logprob"] == b["labels"][label]["logprob"]


def test_load_from_pretrained_path(tmp_path):
    """Exercise HFLabelScorer.load (from_pretrained, dtype handling) on a saved tiny model."""
    from mxr.scoring import HFLabelScorer
    from tests.tiny_hf import build

    model, tok = build(vocab_size=300)
    model.save_pretrained(tmp_path)
    tok.save_pretrained(tmp_path)
    sc = HFLabelScorer.load(str(tmp_path), revision=None, storage_dtype="float32",
                            compute_dtype="float32", device="cpu")
    assert sc.meta["storage_dtype"] == "float32" and next(sc.model.parameters()).dtype == torch.float32
    assert sc.meta["revision_source"] == "local_path" and sc.meta["logits_dtype"] == "torch.float32"
    ref = HFLabelScorer(model, tok)
    a, b = sc.score(_msg()), ref.score(_msg())
    for label in design.LABELS:
        assert math.isclose(a["labels"][label]["logprob"], b["labels"][label]["logprob"], abs_tol=1e-5)
    assert sc.template_roundtrip(_msg())["ok"]


def test_citation_turn_generation_runs_and_is_seeded():
    from mxr.citations import citation_messages

    sc = tiny_scorer(vocab_size=300)
    msgs = citation_messages(_msg(), "Positive")
    a = sc.generate_chat(msgs, max_new_tokens=6, temperature=1.0, seed=3)
    b = sc.generate_chat(msgs, max_new_tokens=6, temperature=1.0, seed=3)
    assert isinstance(a, str) and a == b


def test_multi_token_path_exercised():
    sc = tiny_scorer(vocab_size=300)
    lens = {len(v) for v in sc.label_tokenization(_msg())["label_ids"].values()}
    assert max(lens) > 1, "small vocab should split at least one label into several tokens"
