import math

import pytest

from mxr.scoring import TokenizationError, split_label_tokens, summarize_label_logprobs


def char_tokenizer(text):
    return [ord(c) for c in text]


def merging_tokenizer(text):
    """Merges ': P' into one token, so the label boundary is not clean."""
    out, i = [], 0
    while i < len(text):
        if text.startswith(": P", i):
            out.append(9999)
            i += 3
        else:
            out.append(ord(text[i]))
            i += 1
    return out


def test_clean_boundary_passes():
    prompt_ids, labels = split_label_tokens(char_tokenizer, "PROMPT")
    assert prompt_ids == char_tokenizer("PROMPTSignal:")
    assert labels["Positive"] == char_tokenizer(" Positive")


def test_boundary_merge_is_detected():
    with pytest.raises(TokenizationError, match="boundary"):
        split_label_tokens(merging_tokenizer, "PROMPT", prefix="Signal:",
                           labels=("Positive", "Neutral"), continuations=(" Positive", " Neutral"))
    # Without a leading space the merge happens at the boundary itself.
    with pytest.raises(TokenizationError, match="boundary"):
        split_label_tokens(merging_tokenizer, "PROMPT", prefix="Signal: ",
                           labels=("Positive",), continuations=("Positive",))


def test_prefix_collision_is_detected():
    with pytest.raises(TokenizationError, match="prefix"):
        split_label_tokens(char_tokenizer, "X", labels=("Pos", "Positive"),
                           continuations=(" Pos", " Positive"))


def test_zero_token_label_is_detected():
    with pytest.raises(TokenizationError, match="zero tokens"):
        split_label_tokens(char_tokenizer, "X", labels=("A",), continuations=("",))


def test_summary_normalizes_and_reports_mass():
    lp = {"Positive": math.log(0.6), "Neutral": math.log(0.3), "Negative": math.log(0.05)}
    s = summarize_label_logprobs(lp)
    assert s["label_mass"] == pytest.approx(0.95)
    assert s["p_norm"]["Positive"] == pytest.approx(0.6 / 0.95)
    assert s["argmax"] == "Positive"
    assert s["top2_margin"] == pytest.approx((0.6 - 0.3) / 0.95)


def test_summary_flags_nonfinite():
    s = summarize_label_logprobs({"Positive": float("nan"), "Neutral": -1.0, "Negative": -2.0})
    assert s["finite"] is False
