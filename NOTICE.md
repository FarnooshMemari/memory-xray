# Third-party material and redistribution notice

This repository contains code, documents, synthetic scenario texts, saved run outputs, derived
results and figures created for this project (licensed as described in [`LICENSE`](LICENSE) and
[`LICENSE-CONTENT.md`](LICENSE-CONTENT.md)). It does **not** contain, and does not grant any rights
in, the third-party items below.

## Model weights — not included

| Item | Where it comes from | In this repository? |
|---|---|---|
| `microsoft/Phi-3-mini-4k-instruct`, commit `f39ac1d28e925b323eae81227eaba4464caced4e` | Downloaded by the user from Hugging Face at run time (`run_experiment.py`, Colab notebooks) under the license stated on its model card (MIT, as checked on 2026-10-18): <https://huggingface.co/microsoft/Phi-3-mini-4k-instruct> | **No.** No weights, tokenizer files or model caches are included, and `.gitignore` excludes them. |

Anyone who re-runs the experiment obtains the model directly from its publisher and is responsible for
complying with its license and terms. Nothing in this repository needs the model to explore, reanalyze
or verify the saved results.

**Model outputs that are included.** The saved runs in `runs/` contain numbers produced by the model
(per-token log-probabilities, label probabilities) and the short text replies it generated in the
citation stage (`citations.jsonl`, at most 40 tokens each). These are research outputs of this study.
Check the model's license before reusing them outside this project.

## AI-assisted rubric labels

`records/labels/labeler_1.json` and `records/labels/labeler_2.json` (and the original upload
`records/memory_xray_ai_labels_ready.zip`) were produced with two AI systems — recorded by the
investigator as **GPT-6** (OpenAI) and **Gemini** (Google) — on 2026-10-17. They are AI-assisted
rubric validation, **not human annotation** (protocol amendment 4). Use of those services' outputs is
subject to the providers' terms of use. Model versions and prompts were not recorded.

## Software dependencies — not redistributed

Installed by the user with `pip`; none is vendored in this repository.

| Package | Used for | License (as published by the project) |
|---|---|---|
| PyTorch | model inference; tiny-model tests | BSD-style (see pytorch.org) |
| Hugging Face `transformers` | model loading and tokenization | Apache-2.0 |
| Hugging Face `accelerate` | device placement (experiment only) | Apache-2.0 |
| matplotlib | figures | Matplotlib license (PSF-based) |
| pytest | tests | MIT |

Figures are drawn with matplotlib's bundled DejaVu Sans font; the PDF exports embed font subsets,
which the DejaVu font license permits.

## Scenario texts

All six scenarios (`scenarios/*.json`) are synthetic texts written for this study. The three
macro-finance scenarios are de-identified ("Economy A/B/C") and are not real market data, news or
proprietary content. The rubric (`scenarios/rubric_macro_v1.json`) is an authored reference, not
financial advice and not a claim about the "correct" financial answer.

## Execution platform

The experiment was run on Google Colab (Tesla T4). No Colab or Google assets are included.
