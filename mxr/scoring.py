"""Label-probability scoring with explicit tokenization validation.

For each prompt the assistant turn is forced to begin with ANSWER_PREFIX, and
each label continuation (" Positive", " Neutral", " Negative") is scored as the
sum of its token log-probabilities. This is the same kind of quantity that
ContextCite and SelfCite score: the probability of a fixed response under a
given context. Nothing is sampled.

The validation built into this module:
  * chat-template round trip: tokenizing the rendered template string gives the
    same ids as the tokenizer's own templated tokenization;
  * token-boundary check: tokenize(prompt + prefix + label) must start with
    tokenize(prompt + prefix), so the label ids are exactly the appended part;
  * the label token sequences must be prefix-free (otherwise their
    probabilities are not disjoint and cannot be summed or normalized);
  * multi-token labels: the first-token log-prob from the prompt forward pass
    must equal the one recomputed in the full-sequence pass;
  * everything finite; label mass and top next tokens recorded for diagnosis.

Precision (amendment 1): float16 arithmetic rounds Phi-3's logits (~30-60) to
steps of 2**-5 nats, which made feasibility run 1 fail check I3. Weights may be
stored in float16, but all arithmetic runs in float32 (``enable_float32_compute``)
and logits are float32. The model commit is pinned and verified after loading.
"""
from __future__ import annotations

import math
import platform

from .design import ANSWER_PREFIX, LABEL_CONTINUATIONS, LABELS

import os
import re

# Pinned model (protocol v0.2, amendment 1). The commit is immutable; runs
# against the Hub abort if this exact commit cannot be loaded and verified.
PINNED_MODEL = "microsoft/Phi-3-mini-4k-instruct"
PINNED_REVISION = "f39ac1d28e925b323eae81227eaba4464caced4e"

_SHA = re.compile(r"[0-9a-f]{40}")
FP16_MIN_NORMAL = 6.103515625e-05  # 2**-14


class RevisionError(RuntimeError):
    pass


def resolve_revision(model_name, revision):
    """Resolve the requested revision to an immutable 40-hex commit.

    Local directories (used only by tests) have no commit. A branch or tag is
    resolved through the Hub API; failure to resolve raises RevisionError,
    because an unpinned run is not allowed.
    """
    if os.path.isdir(model_name):
        return {"sha": None, "source": "local_path", "requested": revision}
    if revision and _SHA.fullmatch(revision):
        return {"sha": revision, "source": "pinned_sha", "requested": revision}
    try:
        from huggingface_hub import HfApi

        sha = HfApi().model_info(model_name, revision=revision or "main").sha
    except Exception as exc:  # network, auth, unknown repo
        raise RevisionError(f"could not resolve {model_name}@{revision or 'main'} to a commit: {exc}")
    if not sha or not _SHA.fullmatch(sha):
        raise RevisionError(f"Hub returned no valid commit for {model_name}@{revision or 'main'}: {sha!r}")
    return {"sha": sha, "source": f"resolved_from:{revision or 'main'}", "requested": revision}


def verify_revision_in_cache(model_name, sha, cache_dir=None):
    """True if the config actually loaded lives in the snapshot folder of ``sha``."""
    from huggingface_hub import try_to_load_from_cache

    path = try_to_load_from_cache(repo_id=model_name, filename="config.json",
                                  cache_dir=cache_dir, revision=sha)
    return isinstance(path, str) and f"/snapshots/{sha}/" in path.replace("\\", "/")


def enable_float32_compute(model, storage_dtype):
    """Keep weights in ``storage_dtype`` but run every computation in float32.

    Each decoder layer is cast to float32 just before its forward pass and back
    to ``storage_dtype`` right after, so peak memory grows by one layer. The
    embedding output is upcast; the final norm and the output head are kept in
    float32 permanently, so logits are float32. Casting float16 -> float32 ->
    float16 is exact, so stored weights never change.
    """
    import torch

    dec = model.get_decoder()

    def to_f32(module, args, kwargs):
        module.to(torch.float32)

    def back(module, args, kwargs, output):
        module.to(storage_dtype)
        return output

    handles = []
    for layer in dec.layers:
        handles.append(layer.register_forward_pre_hook(to_f32, with_kwargs=True))
        handles.append(layer.register_forward_hook(back, with_kwargs=True))
    handles.append(dec.embed_tokens.register_forward_hook(lambda m, a, out: out.float()))
    dec.norm.to(torch.float32)
    model.get_output_embeddings().to(torch.float32)
    return handles


class TokenizationError(RuntimeError):
    pass


def split_label_tokens(tokenize, prompt_text, prefix=ANSWER_PREFIX,
                       labels=LABELS, continuations=LABEL_CONTINUATIONS):
    """Return (prompt_ids, {label: label_ids}) or raise TokenizationError.

    ``tokenize`` maps a string to a list of token ids without adding special
    tokens.
    """
    base = prompt_text + prefix
    prompt_ids = list(tokenize(base))
    label_ids = {}
    for label, cont in zip(labels, continuations):
        full = list(tokenize(base + cont))
        if full[: len(prompt_ids)] != prompt_ids:
            raise TokenizationError(
                f"boundary merge for {label!r}: tokenization of prompt+prefix "
                f"is not a prefix of tokenization of prompt+prefix+label"
            )
        tail = full[len(prompt_ids):]
        if not tail:
            raise TokenizationError(f"label {label!r} tokenized to zero tokens")
        label_ids[label] = tail
    names = list(label_ids)
    for a in names:
        for b in names:
            if a == b:
                continue
            ia, ib = label_ids[a], label_ids[b]
            if ib[: len(ia)] == ia:
                raise TokenizationError(
                    f"label {a!r} ids {ia} are a prefix of label {b!r} ids {ib}"
                )
    return prompt_ids, label_ids


def summarize_label_logprobs(label_logprobs: dict) -> dict:
    """Raw probabilities, label mass, normalized probabilities, argmax, margin."""
    finite = all(math.isfinite(x) for x in label_logprobs.values())
    raw = {k: math.exp(v) for k, v in label_logprobs.items()}
    mass = sum(raw.values())
    if mass <= 0 or not finite:
        norm = {k: float("nan") for k in raw}
    else:
        norm = {k: raw[k] / mass for k in raw}
    ordered = sorted(norm.items(), key=lambda kv: kv[1], reverse=True)
    return {
        "finite": finite,
        "p_raw": raw,
        "label_mass": mass,
        "p_norm": norm,
        "argmax": ordered[0][0],
        "top2_margin": ordered[0][1] - ordered[1][1],
    }


def _ids_from_template_output(out):
    """apply_chat_template(tokenize=True) returns different types by version."""
    if hasattr(out, "keys") and "input_ids" in out:
        out = out["input_ids"]
    if hasattr(out, "tolist"):
        out = out.tolist()
    if out and isinstance(out[0], list):
        if len(out) != 1:
            raise ValueError("expected a single templated sequence")
        out = out[0]
    return list(out)


class HFLabelScorer:
    """Scores label continuations with a Hugging Face causal LM."""

    def __init__(self, model, tokenizer, device="cpu", meta=None):
        import torch

        self.torch = torch
        self.model = model.eval()
        self.tok = tokenizer
        self.device = device
        self.meta = dict(meta or {})
        pad = tokenizer.pad_token_id
        if pad is None:
            pad = tokenizer.eos_token_id
        self.pad_id = pad

    @classmethod
    def load(cls, model_name=PINNED_MODEL, revision=PINNED_REVISION, storage_dtype="auto",
             compute_dtype="float32", device=None, attn_implementation="eager"):
        import torch
        import transformers
        from packaging import version
        from transformers import AutoModelForCausalLM, AutoTokenizer

        rev = resolve_revision(model_name, revision)
        sha = rev["sha"]

        torch.manual_seed(0)
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        if storage_dtype == "auto":
            storage_dtype = "float16" if device == "cuda" else "float32"
        if compute_dtype not in ("float32", storage_dtype):
            raise ValueError("compute_dtype must be float32 or equal to storage_dtype")
        storage_torch = getattr(torch, storage_dtype)
        if device == "cuda":
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False

        # Tokenizer and weights both come from the same immutable commit.
        tok = AutoTokenizer.from_pretrained(model_name, revision=sha)
        kwargs = {"revision": sha, "attn_implementation": attn_implementation}
        if version.parse(transformers.__version__) >= version.parse("5.0.0"):
            kwargs["dtype"] = storage_torch
        else:
            kwargs["torch_dtype"] = storage_torch
        model = AutoModelForCausalLM.from_pretrained(model_name, **kwargs)

        verified = None
        if sha is not None:
            verified = verify_revision_in_cache(model_name, sha)
            if not verified:
                raise RevisionError(f"loaded files are not from snapshot {sha}")

        model.to(device)
        loaded = next(model.get_decoder().layers.parameters()).dtype
        if loaded != storage_torch:
            raise RuntimeError(f"model loaded as {loaded}, requested {storage_torch}")

        subnormal = None
        if storage_dtype == "float16":
            # Only weights below the float16 normal range can differ from the
            # bf16 checkpoint after conversion; record how many there are.
            n_sub = n_all = 0
            with torch.no_grad():
                for p in model.parameters():
                    n_all += p.numel()
                    n_sub += int(((p != 0) & (p.abs() < FP16_MIN_NORMAL)).sum())
            subnormal = n_sub / n_all

        if compute_dtype == "float32" and storage_dtype != "float32":
            enable_float32_compute(model, storage_torch)

        meta = {
            "backend": "hf",
            "model_name": model_name,
            "revision_requested": revision,
            "revision_source": rev["source"],
            "commit_hash": sha,
            "revision_verified": verified,
            "config_commit_hash": getattr(model.config, "_commit_hash", None),
            "storage_dtype": storage_dtype,
            "compute_dtype": compute_dtype,
            "dtype": f"{storage_dtype} storage / {compute_dtype} compute",
            "fp16_subnormal_weight_fraction": subnormal,
            "device": device,
            "device_name": torch.cuda.get_device_name(0) if device == "cuda" else platform.processor(),
            "attn_implementation": attn_implementation,
            "torch_version": torch.__version__,
            "transformers_version": transformers.__version__,
            "python_version": platform.python_version(),
        }
        scorer = cls(model, tok, device=device, meta=meta)
        scorer.meta.update(scorer.precision_probe())
        if compute_dtype == "float32" and scorer.meta["logits_dtype"] != "torch.float32":
            raise RuntimeError(f"float32 compute requested but logits are {scorer.meta['logits_dtype']}")
        return scorer

    def precision_probe(self):
        """One short forward pass: record logit dtype and that stored weights are unchanged."""
        torch = self.torch
        ids = self._tokenize("precision probe")
        inp = torch.tensor([ids], device=self.device)
        layers = self.model.get_decoder().layers
        before = {p.dtype for p in layers.parameters()}
        with torch.inference_mode():
            logits = self.model(input_ids=inp, attention_mask=torch.ones_like(inp)).logits
        after = {p.dtype for p in layers.parameters()}
        return {
            "logits_dtype": str(logits.dtype),
            "layer_weight_dtypes_before": sorted(str(d) for d in before),
            "layer_weight_dtypes_after": sorted(str(d) for d in after),
            "weights_unchanged_dtype": before == after,
        }

    # ---------- tokenization ----------
    def _tokenize(self, text):
        return list(self.tok(text, add_special_tokens=False)["input_ids"])

    def prompt_text(self, user_msg):
        msgs = [{"role": "user", "content": user_msg}]
        return self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

    def template_roundtrip(self, user_msg):
        msgs = [{"role": "user", "content": user_msg}]
        via_template = _ids_from_template_output(
            self.tok.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True)
        )
        via_string = self._tokenize(self.prompt_text(user_msg))
        return {"ok": via_template == via_string,
                "len_template": len(via_template), "len_string": len(via_string)}

    def label_tokenization(self, user_msg):
        prompt_ids, label_ids = split_label_tokens(self._tokenize, self.prompt_text(user_msg))
        return {
            "prompt_len": len(prompt_ids),
            "label_ids": label_ids,
            "label_tokens": {k: self.tok.convert_ids_to_tokens(v) for k, v in label_ids.items()},
        }

    # ---------- scoring ----------
    def _logprobs_at(self, ids, positions):
        torch = self.torch
        inp = torch.tensor([ids], device=self.device)
        with torch.inference_mode():
            logits = self.model(input_ids=inp, attention_mask=torch.ones_like(inp)).logits
        return {p: torch.log_softmax(logits[0, p].float(), dim=-1) for p in positions}

    def score(self, user_msg, top_n=5):
        torch = self.torch
        prompt_ids, label_ids = split_label_tokens(self._tokenize, self.prompt_text(user_msg))
        n = len(prompt_ids)
        first = self._logprobs_at(prompt_ids, [n - 1])[n - 1]
        n_forward = 1
        top = torch.topk(first, top_n)
        top_next = [
            {"token": self.tok.convert_ids_to_tokens(int(i)), "logprob": float(lp)}
            for lp, i in zip(top.values.tolist(), top.indices.tolist())
        ]
        labels_out = {}
        first_token_consistency = []
        for label, ids in label_ids.items():
            token_lps = [float(first[ids[0]])]
            if len(ids) > 1:
                seq = prompt_ids + ids[:-1]
                pos = list(range(n - 1, n - 1 + len(ids)))
                lps = self._logprobs_at(seq, pos)
                n_forward += 1
                recomputed_first = float(lps[pos[0]][ids[0]])
                first_token_consistency.append(abs(recomputed_first - token_lps[0]))
                token_lps += [float(lps[p][t]) for p, t in zip(pos[1:], ids[1:])]
            labels_out[label] = {
                "token_ids": ids,
                "token_logprobs": token_lps,
                "logprob": sum(token_lps),
            }
        summary = summarize_label_logprobs({k: v["logprob"] for k, v in labels_out.items()})
        summary.update({
            "labels": labels_out,
            "prompt_len": n,
            "n_forward": n_forward,
            "first_token_mass": float(sum(math.exp(labels_out[k]["token_logprobs"][0]) for k in labels_out)),
            "max_first_token_recompute_diff": max(first_token_consistency) if first_token_consistency else 0.0,
            "top_next_tokens": top_next,
        })
        return summary

    def greedy(self, user_msg, max_new_tokens=6):
        torch = self.torch
        from transformers import GenerationConfig

        ids = self._tokenize(self.prompt_text(user_msg) + ANSWER_PREFIX)
        inp = torch.tensor([ids], device=self.device)
        cfg = GenerationConfig(max_new_tokens=max_new_tokens, do_sample=False,
                               pad_token_id=self.pad_id,
                               eos_token_id=getattr(self.model.generation_config, "eos_token_id", None))
        with torch.inference_mode():
            out = self.model.generate(input_ids=inp, attention_mask=torch.ones_like(inp),
                                      generation_config=cfg)
        new = out[0, len(ids):].tolist()
        return {"token_ids": new, "text": self.tok.decode(new, skip_special_tokens=False)}

    def generate_chat(self, messages, max_new_tokens=40, temperature=1.0, seed=0):
        """Sampled continuation of a multi-turn chat (used for the citation turn)."""
        torch = self.torch
        from transformers import GenerationConfig

        text = self.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        ids = self._tokenize(text)
        inp = torch.tensor([ids], device=self.device)
        torch.manual_seed(seed)
        cfg = GenerationConfig(max_new_tokens=max_new_tokens, do_sample=temperature > 0,
                               temperature=temperature if temperature > 0 else None,
                               top_p=1.0, top_k=0, pad_token_id=self.pad_id,
                               eos_token_id=getattr(self.model.generation_config, "eos_token_id", None))
        with torch.inference_mode():
            out = self.model.generate(input_ids=inp, attention_mask=torch.ones_like(inp),
                                      generation_config=cfg)
        new = out[0, len(ids):].tolist()
        return self.tok.decode(new, skip_special_tokens=True)
