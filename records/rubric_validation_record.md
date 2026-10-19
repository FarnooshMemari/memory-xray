# Rubric validation record (amendment 4)

**Kind:** independent AI-assisted rubric validation. **Not human annotation.**

| | labeler_1 | labeler_2 |
|---|---|---|
| Labeler | GPT-6 (AI model) | Gemini (AI model) |
| Date | 2026-10-17 | 2026-10-17 |
| File | `records/labels/labeler_1.json` | `records/labels/labeler_2.json` |
| SHA-256 | `e6434405c028400bb45dc7d380a7c3810c1a64d342151f5525430072000274b2` | `38f8ae33421014509b64cce5cd2a8415e238134f90e0d21d8813453ee9b8a6b7` |
| Agreement with frozen scores | 15/15 | 15/15 |

- **Agreement between the two labelers:** 15/15. The files are identical apart from `name`.
- **G2 (`python check_labels.py`):** OK, with no blocking issues, no record-level disagreements, and files matching the declared labelers.
- **Provenance:** the investigator's note, `records/AI_LABELING_PROVENANCE.txt`, is kept verbatim. The original upload `records/memory_xray_ai_labels_ready.zip` is kept as well. Checksums for all four files are in `records/labels_SHA256SUMS.txt`.
- **Integration:** the files replaced the untouched blank templates in `records/labels/`, after confirming they were still blank. Nothing in the uploaded files was edited.

**Limitations** (see protocol §17, amendment 4):
- correlated AI errors;
- the frozen scores were also AI-authored;
- model versions and prompts are not recorded;
- blindness is as reported by the investigator.
