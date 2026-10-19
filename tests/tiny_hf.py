"""Build a tiny random causal LM and a locally trained tokenizer (no downloads).

Used to exercise the real Hugging Face scoring path offline. Its outputs are
meaningless; only indexing, tokenization and consistency are tested.
"""
from __future__ import annotations

import json
from pathlib import Path

CHAT_TEMPLATE = (
    "{% for m in messages %}{{ '<|' + m['role'] + '|>\n' + m['content'] + '<|end|>\n' }}"
    "{% endfor %}{% if add_generation_prompt %}{{ '<|assistant|>\n' }}{% endif %}"
)
SPECIALS = ["<unk>", "<pad>", "<s>", "</s>", "<|user|>", "<|assistant|>", "<|end|>"]


def _corpus():
    from mxr import design

    scen = json.loads((Path(__file__).parents[1] / "scenarios" / "s_single.json").read_text())
    texts = []
    for k in range(3):
        for s in design.all_subsets():
            texts.append(design.render(scen, s, k)["user_msg"])
    texts += ["Signal: Positive Signal: Neutral Signal: Negative"] * 50
    return texts


def build(vocab_size=400, seed=0, arch="llama", max_logit=None):
    """Tiny random model + tokenizer. ``max_logit`` rescales the output head so the
    largest logit on a probe prompt has that magnitude (Phi-3 logits are ~30-60,
    where float16 values are spaced 2**-5 apart)."""
    import torch
    from tokenizers import AddedToken, Tokenizer, decoders, models, pre_tokenizers, trainers
    from transformers import (LlamaConfig, LlamaForCausalLM, Phi3Config, Phi3ForCausalLM,
                              PreTrainedTokenizerFast)

    tk = Tokenizer(models.BPE(unk_token="<unk>"))
    tk.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tk.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(vocab_size=vocab_size, special_tokens=SPECIALS,
                                  initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
                                  show_progress=False)
    tk.train_from_iterator(_corpus(), trainer)
    tk.add_special_tokens([AddedToken(t, special=True) for t in SPECIALS])
    tok = PreTrainedTokenizerFast(tokenizer_object=tk, unk_token="<unk>", pad_token="<pad>",
                                  bos_token="<s>", eos_token="</s>")
    tok.chat_template = CHAT_TEMPLATE

    torch.manual_seed(seed)
    common = dict(vocab_size=len(tok), hidden_size=64, intermediate_size=128,
                  num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=4,
                  max_position_embeddings=2048, pad_token_id=tok.pad_token_id,
                  bos_token_id=tok.bos_token_id, eos_token_id=tok.eos_token_id)
    if arch == "llama":
        model = LlamaForCausalLM(LlamaConfig(**common)).eval()
    elif arch == "phi3":
        model = Phi3ForCausalLM(Phi3Config(original_max_position_embeddings=2048, **common)).eval()
    else:
        raise ValueError(arch)
    if max_logit is not None:
        ids = tok("probe text Signal: Positive", add_special_tokens=False)["input_ids"]
        with torch.no_grad():
            peak = model(input_ids=torch.tensor([ids])).logits.abs().max().item()
            model.get_output_embeddings().weight.mul_(max_logit / peak)
    return model, tok


def tiny_scorer(vocab_size=400, seed=0, arch="llama", max_logit=None, storage="float32", compute="float32"):
    """Tiny scorer. storage float16 + compute float32 mirrors the amended Colab setup."""
    import torch

    from mxr.scoring import HFLabelScorer, enable_float32_compute

    model, tok = build(vocab_size=vocab_size, seed=seed, arch=arch, max_logit=max_logit)
    if storage == "float16":
        model = model.half()
        if compute == "float32":
            enable_float32_compute(model, torch.float16)
    sc = HFLabelScorer(model, tok, device="cpu",
                       meta={"backend": "hf", "model_name": f"tiny-random-{arch}-v{vocab_size}",
                             "commit_hash": None, "revision_source": "local_path",
                             "storage_dtype": storage, "compute_dtype": compute,
                             "dtype": f"{storage} storage / {compute} compute", "device_name": "cpu",
                             "note": "random weights; plumbing test only"})
    sc.meta.update(sc.precision_probe())
    return sc
