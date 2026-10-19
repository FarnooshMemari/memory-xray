"""Float16 numerics: reproduce the run-1 error mechanism and verify the fix.

Phi-3's logits are ~30-60. In float16 those values are spaced 2**-5 = 0.03125
apart, so log-probs computed from float16 logits carry errors of that size.
The fix (amendment 1) keeps weights in float16 but computes in float32.
"""
import copy
import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")

from mxr import design  # noqa: E402
from mxr.scoring import HFLabelScorer, enable_float32_compute  # noqa: E402
from tests.tiny_hf import build  # noqa: E402

SCEN = json.loads((Path(__file__).parents[1] / "scenarios" / "s_single.json").read_text())
CELLS = [(frozenset(), 0), (frozenset({"E2"}), 1), (frozenset(design.CANONICAL), 2),
         (frozenset({"E1", "E3"}), 0)]


def _scorer(model, tok):
    return HFLabelScorer(model, tok, device="cpu", meta={"backend": "hf"})


def _scores(sc):
    out = []
    for s, k in CELLS:
        res = sc.score(design.render(SCEN, s, k)["user_msg"])
        out.append(res)
    return out


@pytest.fixture(scope="module", params=["phi3", "llama"])
def models(request):
    base, tok = build(vocab_size=300, arch=request.param, max_logit=50.0)
    stored16 = copy.deepcopy(base).half()                     # what the T4 holds
    reference = copy.deepcopy(stored16).float()               # same weights, all-float32 math
    fixed = copy.deepcopy(stored16)
    enable_float32_compute(fixed, torch.float16)              # amendment-1 setup
    plain16 = copy.deepcopy(stored16)                         # run-1 setup (float16 math)
    return {"tok": tok, "reference": reference, "fixed": fixed, "plain16": plain16}


def _max_err(a, b):
    return max(abs(x["labels"][l]["logprob"] - y["labels"][l]["logprob"])
               for x, y in zip(a, b) for l in design.LABELS)


def test_float32_compute_matches_float32_reference(models):
    ref = _scores(_scorer(models["reference"], models["tok"]))
    fixed = _scores(_scorer(models["fixed"], models["tok"]))
    assert _max_err(fixed, ref) < 1e-4
    assert max(r["max_first_token_recompute_diff"] for r in fixed) < 1e-4


def test_float16_math_is_measurably_off_at_phi3_logit_scale(models):
    ref = _scores(_scorer(models["reference"], models["tok"]))
    plain = _scores(_scorer(models["plain16"], models["tok"]))
    fixed = _scores(_scorer(models["fixed"], models["tok"]))
    err16, err32 = _max_err(plain, ref), _max_err(fixed, ref)
    assert err16 > 1e-3, err16
    assert err16 > 50 * err32, (err16, err32)


def test_float16_math_reproduces_run1_I3_failure_where_the_host_shows_it(models):
    """The preserved original assertion, applied wherever the host can exhibit the effect.

    Publication copy (see CHANGES.md). Run 1 failed I3 because float16 math rounded the prompt pass and the
    longer recompute pass differently. Whether these tiny CPU models show that depends on the host's float16
    kernels (oneDNN ISA, ATen dispatch) and on the architecture: on some hosts one architecture gives a
    difference of exactly 0.0, and the original test then failed although nothing was wrong. Exactly 0.0 means
    the effect cannot be reproduced on this host, so the case is skipped (not passed); any other value must
    exceed the 1e-3 threshold, as in the original test."""
    plain = _scores(_scorer(models["plain16"], models["tok"]))
    diff = max(r["max_first_token_recompute_diff"] for r in plain)
    if diff == 0.0:
        pytest.skip("this host's float16 kernels round both passes identically (difference 0.0), so run 1's I3 "
                    "failure cannot be reproduced here; see test_I3_recompute_check_detects_a_length_dependent_difference")
    assert diff > 1e-3, diff


def test_fix_clears_I3_recompute_difference(models):
    """Float32 compute (amendment 1) keeps the I3 recompute difference far below its 1e-3 threshold
    (the second assertion of the preserved original test, which holds on every host)."""
    fixed = _scores(_scorer(models["fixed"], models["tok"]))
    assert max(r["max_first_token_recompute_diff"] for r in fixed) < 1e-4


def test_I3_recompute_check_detects_a_length_dependent_difference(models):
    """The I3 check is live: a logit shift that grows with sequence length (what differing float16
    rounding between the two passes amounts to) is detected above the 1e-3 threshold."""
    model, tok = models["fixed"], models["tok"]
    sc = _scorer(model, tok)
    msg = design.render(SCEN, *CELLS[2])["user_msg"]
    multi = [ids for ids in sc.label_tokenization(msg)["label_ids"].values() if len(ids) > 1]
    assert multi, "the test needs a multi-token label"
    t = multi[0][0]

    def shift(module, args, out):
        out = out.clone()
        out[..., t] = out[..., t] + 0.05 * out.shape[-2]
        return out

    h = model.get_output_embeddings().register_forward_hook(shift)
    try:
        res = sc.score(msg)
    finally:
        h.remove()
    assert res["n_forward"] > 1
    assert res["max_first_token_recompute_diff"] > 1e-3


def test_fixed_model_keeps_float16_storage_and_returns_float32_logits(models):
    sc = _scorer(models["fixed"], models["tok"])
    probe = sc.precision_probe()
    assert probe["logits_dtype"] == "torch.float32"
    assert probe["layer_weight_dtypes_after"] == ["torch.float16"]
    sc.greedy(design.render(SCEN, frozenset(design.CANONICAL), 0)["user_msg"], max_new_tokens=3)
    assert {str(p.dtype) for p in models["fixed"].get_decoder().layers.parameters()} == {"torch.float16"}


def test_fixed_greedy_matches_reference_greedy(models):
    msg = design.render(SCEN, frozenset({"E2"}), 0)["user_msg"]
    a = _scorer(models["fixed"], models["tok"]).greedy(msg, max_new_tokens=4)
    b = _scorer(models["reference"], models["tok"]).greedy(msg, max_new_tokens=4)
    assert a["token_ids"] == b["token_ids"]
