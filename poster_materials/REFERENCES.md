# References: Memory X-Ray

These are the works cited by the Memory X-Ray poster and repository. Each one was checked against a publisher, proceedings, ACL Anthology, PMLR, JMLR, NeurIPS or arXiv page. The BibTeX entries are in [`references.bib`](references.bib), and the key for each entry is given in brackets. Page ranges and DOIs are listed only where an authoritative page showed them.

## Method foundations (Shapley values and removal-based attribution)

- `[shapley1953value]` Shapley, L. S. (1953). *A Value for n-Person Games*. In H. W. Kuhn & A. W. Tucker (Eds.), Contributions to the Theory of Games, Vol. II (Annals of Mathematics Studies 28), pp. 307–317. Princeton University Press. Reprinted in A. E. Roth (Ed.), *The Shapley Value* (Cambridge University Press, 1988), pp. 31–40: https://doi.org/10.1017/CBO9780511528446.003
    - Relevance: Defines the Shapley value, an axiomatic way to split a cooperative game's total payoff among its players. Memory X-Ray applies this definition directly when it computes exact attributions over all 16 subsets of the 4 evidence records.
- `[lundberg2017unified]` Lundberg, S. M., & Lee, S.-I. (2017). *A Unified Approach to Interpreting Model Predictions*. Advances in Neural Information Processing Systems 30 (NIPS 2017). https://papers.nips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html
    - Relevance: Brings several additive feature-attribution methods under one Shapley-value framework (SHAP), which made Shapley values a standard tool for explaining model predictions.
- `[strumbelj2014explaining]` Štrumbelj, E., & Kononenko, I. (2014). *Explaining Prediction Models and Individual Predictions with Feature Contributions*. Knowledge and Information Systems, 41(3), 647–665. https://doi.org/10.1007/s10115-013-0679-x
    - Relevance: A model-agnostic explanation method that perturbs all subsets of input features, so it accounts for interactions and redundancy between features. This is the property behind our finding that Shapley exposes redundancy that leave-one-out misses.
- `[covert2021explaining]` Covert, I., Lundberg, S., & Lee, S.-I. (2021). *Explaining by Removing: A Unified Framework for Model Explanation*. Journal of Machine Learning Research, 22(209), 1–90. https://jmlr.org/papers/v22/20-1316.html
    - Relevance: Treats 26 explanation methods (including SHAP, LIME and permutation tests) as simulations of feature removal and classifies them along three dimensions. This framework covers our record ablation, leave-one-out and Shapley scores.
- `[kumar2020problems]` Kumar, I. E., Venkatasubramanian, S., Scheidegger, C., & Friedler, S. (2020). *Problems with Shapley-value-based explanations as feature importance measures*. Proceedings of the 37th International Conference on Machine Learning (ICML 2020), PMLR 119, 5491–5500. https://proceedings.mlr.press/v119/kumar20e.html
    - Relevance: Argues that using Shapley values for feature importance creates mathematical problems, that fixing them needs extra machinery such as causal reasoning, and that the results may not serve human-centred explanation goals. It is a caveat for how far record-level Shapley scores can be read.
- `[sundararajan2020many]` Sundararajan, M., & Najmi, A. (2020). *The Many Shapley Values for Model Explanation*. Proceedings of the 37th International Conference on Machine Learning (ICML 2020), PMLR 119, 9269–9278. https://proceedings.mlr.press/v119/sundararajan20b.html
    - Relevance: Shows that different ways of putting the Shapley value into practice give different attributions, so the uniqueness result does not carry over, and introduces Baseline Shapley. This bears on our choice to use "record removed from the prompt" as the baseline.

## Faithfulness of explanations and self-reports

- `[jacovi2020towards]` Jacovi, A., & Goldberg, Y. (2020). *Towards Faithfully Interpretable NLP Systems: How Should We Define and Evaluate Faithfulness?* Proceedings of ACL 2020, 4198–4205. https://doi.org/10.18653/v1/2020.acl-main.386
    - Relevance: Calls for clearer separation of evaluation criteria (faithfulness vs. plausibility), offers guidelines for evaluating faithfulness, and argues for graded rather than binary faithfulness. These are the terms we use when we say plausible citations are not evidence of faithfulness.
- `[deyoung2020eraser]` DeYoung, J., et al. (2020). *ERASER: A Benchmark to Evaluate Rationalized NLP Models*. Proceedings of ACL 2020, 4443–4458. https://doi.org/10.18653/v1/2020.acl-main.408
    - Relevance: Introduces metrics for both agreement with human rationales and faithfulness. Its removal-based comprehensiveness and sufficiency metrics parallel our necessity and sufficiency tests on evidence subsets.
- `[turpin2023language]` Turpin, M., Michael, J., Perez, E., & Bowman, S. R. (2023). *Language Models Don't Always Say What They Think: Unfaithful Explanations in Chain-of-Thought Prompting*. Advances in Neural Information Processing Systems 36 (NeurIPS 2023), 74952–74965. https://doi.org/10.52202/075280-3275
    - Relevance: Shows that chain-of-thought explanations can be steered by biasing features the explanation never mentions, such as reordering multiple-choice options. The result is plausible but misleading rationales, which parallels the label-conditional self-citations we observe.
- `[lanham2023measuring]` Lanham, T., et al. (2023). *Measuring Faithfulness in Chain-of-Thought Reasoning*. arXiv:2307.13702. https://arxiv.org/abs/2307.13702
    - Relevance: Measures chain-of-thought faithfulness by intervening on the stated reasoning (for example, adding mistakes or paraphrasing it) and checking whether the answer changes. It finds that reliance on the reasoning varies by task and that larger models often reason less faithfully.
- `[madsen2024self]` Madsen, A., Chandar, S., & Reddy, S. (2024). *Are self-explanations from Large Language Models faithful?* Findings of ACL 2024, 295–337. https://doi.org/10.18653/v1/2024.findings-acl.19
    - Relevance: Proposes self-consistency checks for LLM self-explanations: if a model says certain inputs are important, it should not reach the same prediction without them. This is the same logic as testing whether the records the model cites are actually necessary. Faithfulness turned out to depend on model, task and explanation type.
- `[parcalabescu2024measuring]` Parcalabescu, L., & Frank, A. (2024). *On Measuring Faithfulness or Self-consistency of Natural Language Explanations*. Proceedings of ACL 2024 (Volume 1: Long Papers), 6048–6089. https://doi.org/10.18653/v1/2024.acl-long.329
    - Relevance: Argues that many "faithfulness" tests for LLM explanations measure output-level self-consistency, not faithfulness to the model's internals, and proposes the CC-SHAP measure. This is why we frame our measure as *consistency* between citations and behavioural influence.
- `[agarwal2024faithfulness]` Agarwal, C., Tanneru, S. H., & Lakkaraju, H. (2024). *Faithfulness vs. Plausibility: On the (Un)Reliability of Explanations from Large Language Models*. arXiv:2402.04614. https://arxiv.org/abs/2402.04614
    - Relevance: Argues that LLM self-explanations often sound convincing without reflecting the model's actual reasoning, and that optimizing for plausibility can work against faithfulness. Our post hoc content-only baseline raises the same concern: citations can score well without tracking the model's own behavior.
- `[atanasova2023faithfulness]` Atanasova, P., Camburu, O.-M., Lioma, C., Lukasiewicz, T., Simonsen, J. G., & Augenstein, I. (2023). *Faithfulness Tests for Natural Language Explanations*. Proceedings of ACL 2023 (Volume 2: Short Papers), 283–294. https://doi.org/10.18653/v1/2023.acl-short.25
    - Relevance: Proposes two tests of whether natural-language explanations reflect the model: a counterfactual input editor that inserts reasons which change the prediction but are missing from the explanation, and a check of whether inputs rebuilt from the stated reasons give the same prediction. The second test is analogous to our sufficiency check on cited evidence.
- `[lyu2024towards]` Lyu, Q., Apidianaki, M., & Callison-Burch, C. (2024). *Towards Faithful Model Explanation in NLP: A Survey*. Computational Linguistics, 50(2), 657–723. https://doi.org/10.1162/coli_a_00511
    - Relevance: Surveys more than 110 explanation methods in NLP through the lens of faithfulness and sorts them into five families. It gives background for placing a perturbation-based consistency check among existing approaches.
- `[doshivelez2017towards]` Doshi-Velez, F., & Kim, B. (2017). *Towards A Rigorous Science of Interpretable Machine Learning*. arXiv:1702.08608. https://arxiv.org/abs/1702.08608
    - Relevance: Defines interpretability, discusses when it is needed, and proposes a taxonomy for evaluating it rigorously (application-, human- and functionally-grounded). Memory X-Ray is a functionally-grounded evaluation with no human study.

## Context attribution and citations in LLMs

- `[cohenwang2024contextcite]` Cohen-Wang, B., Shah, H., Georgiev, K., & Mądry, A. (2024). *ContextCite: Attributing Model Generation to Context*. Advances in Neural Information Processing Systems 37 (NeurIPS 2024), 95764–95807. https://doi.org/10.52202/079017-3035
    - Relevance: Defines context attribution (finding which parts of the context led a model to a given statement) and estimates it by fitting a sparse linear surrogate to the model's outputs under context ablations. It is the closest ablation-based counterpart to our record-level attribution.
- `[chuang2025selfcite]` Chuang, Y.-S., et al. (2025). *SelfCite: Self-Supervised Alignment for Context Attribution in Large Language Models*. Proceedings of the 42nd International Conference on Machine Learning (ICML 2025), PMLR 267, 10839–10858. https://proceedings.mlr.press/v267/chuang25a.html
    - Relevance: Uses context ablation as a self-supervised reward for citations. A necessary citation should change the response when removed, and a sufficient one should preserve it when kept alone. These are the same necessity and sufficiency criteria we apply to cited record sets.
- `[wallat2025correctness]` Wallat, J., Heuss, M., de Rijke, M., & Anand, A. (2025). *Correctness is not Faithfulness in Retrieval Augmented Generation Attributions*. Proceedings of the 2025 ACM SIGIR International Conference on Innovative Concepts and Theories in Information Retrieval (ICTIR '25), 22–32. https://doi.org/10.1145/3731120.3744592 (preprint: arXiv:2412.18004, "Correctness is not Faithfulness in RAG Attributions")
    - Relevance: Separates citation *correctness* (the cited source supports the statement) from citation *faithfulness* (the model actually relied on it) and reports that up to 57% of citations lack faithfulness. Our post hoc content-only baseline points to the same gap, in a much smaller setting (6 scenarios, one model).
- `[qi2024model]` Qi, J., Sarti, G., Fernández, R., & Bisazza, A. (2024). *Model Internals-based Answer Attribution for Trustworthy Retrieval-Augmented Generation*. Proceedings of EMNLP 2024, 6037–6053. https://doi.org/10.18653/v1/2024.emnlp-main.347
    - Relevance: MIRAGE uses the model's internal signals to link answer tokens to the retrieved documents that influenced them, and its citations are more faithful than self-citation prompting. It is an alternative to asking the model which evidence it used.
- `[gao2023enabling]` Gao, T., Yen, H., Yu, J., & Chen, D. (2023). *Enabling Large Language Models to Generate Text with Citations*. Proceedings of EMNLP 2023, 6465–6488. https://doi.org/10.18653/v1/2023.emnlp-main.398
    - Relevance: The ALCE benchmark evaluates LLM-generated citations by whether the cited passages support the text, and finds that support is often incomplete. Its evaluation is support-based (correctness), not influence-based.
- `[rashkin2023measuring]` Rashkin, H., et al. (2023). *Measuring Attribution in Natural Language Generation Models*. Computational Linguistics, 49(4), 777–840. https://doi.org/10.1162/coli_a_00486
    - Relevance: Introduces the Attributable to Identified Sources (AIS) framework for judging whether generated text is supported by its sources. It is the standard "is the citation supported" notion that we contrast with behavioural reliance.
- `[lewis2020retrieval]` Lewis, P., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. Advances in Neural Information Processing Systems 33 (NeurIPS 2020), 9459–9474. https://papers.nips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html
    - Relevance: Introduces retrieval-augmented generation, in which a generator conditions on retrieved passages. This is the general setting of an LLM deciding from evidence or memory records placed in its prompt.

## Position and order sensitivity

- `[liu2024lost]` Liu, N. F., et al. (2024). *Lost in the Middle: How Language Models Use Long Contexts*. Transactions of the Association for Computational Linguistics, 12, 157–173. https://doi.org/10.1162/tacl_a_00638
    - Relevance: Shows that LLM performance depends on where relevant information sits in the context. Performance is highest when it is at the beginning or end and drops when it is in the middle. This is the background for our fixed-ordering design and order effects.
- `[zhao2021calibrate]` Zhao, Z., Wallace, E., Feng, S., Klein, D., & Singh, S. (2021). *Calibrate Before Use: Improving Few-shot Performance of Language Models*. Proceedings of the 38th International Conference on Machine Learning (ICML 2021), PMLR 139, 12697–12706. https://proceedings.mlr.press/v139/zhao21c.html
    - Relevance: Finds that few-shot predictions are biased toward certain answers, including a recency bias toward answers near the end of the prompt, and proposes contextual calibration. This matches the recency sensitivity we see when two rules conflict.
- `[lu2022fantastically]` Lu, Y., Bartolo, M., Moore, A., Riedel, S., & Stenetorp, P. (2022). *Fantastically Ordered Prompts and Where to Find Them: Overcoming Few-Shot Prompt Order Sensitivity*. Proceedings of ACL 2022 (Volume 1: Long Papers), 8086–8098. https://doi.org/10.18653/v1/2022.acl-long.556
    - Relevance: Shows that the order of the same few-shot examples alone can change performance drastically, which supports evaluating every evidence subset under several fixed orderings.

## Model and software

- `[abdin2024phi3]` Abdin, M., et al. (2024). *Phi-3 Technical Report: A Highly Capable Language Model Locally on Your Phone*. arXiv:2404.14219. https://arxiv.org/abs/2404.14219
    - Relevance: Introduces phi-3-mini, a 3.8-billion-parameter language model trained on 3.3 trillion tokens. Memory X-Ray studies its instruction-tuned 4k-context variant (Phi-3-mini-4k-instruct).
- `[wolf2020transformers]` Wolf, T., et al. (2020). *Transformers: State-of-the-Art Natural Language Processing*. Proceedings of EMNLP 2020: System Demonstrations, 38–45. https://doi.org/10.18653/v1/2020.emnlp-demos.6
    - Relevance: The open-source library used to load the model and score label probabilities.
- `[paszke2019pytorch]` Paszke, A., et al. (2019). *PyTorch: An Imperative Style, High-Performance Deep Learning Library*. Advances in Neural Information Processing Systems 32 (NeurIPS 2019). https://papers.nips.cc/paper_files/paper/2019/hash/bdbca288fee7f92f2bfa9f7012727740-Abstract.html
    - Relevance: The deep learning framework the experiments run on.

## Suggested short list for the poster (6–8 refs)

Eight references cover the method, the faithfulness framing, the closest related work, the order effect and the model:

1. `shapley1953value`: the attribution method (swap in `lundberg2017unified` if the audience knows SHAP better)
2. `jacovi2020towards`: the faithfulness vs. plausibility distinction
3. `turpin2023language`: self-explanations shaped by cues they do not mention (label-conditional rationales)
4. `madsen2024self`: self-consistency tests of LLM self-explanations (`parcalabescu2024measuring` is the alternative if the poster stresses "consistency, not faithfulness")
5. `cohenwang2024contextcite`: ablation-based context attribution
6. `wallat2025correctness`: correct citations are not necessarily faithful (matches the content-only baseline result)
7. `liu2024lost`: position sensitivity (use `zhao2021calibrate` instead if the poster stresses *recency* specifically)
8. `abdin2024phi3`: the model studied

## Could not verify (excluded)

None. All 27 candidate references were verified, and 2 more were added (29 in total).

Notes on details deliberately left out:

- No DOI could be confirmed for the original 1953 Shapley chapter, so the link points to the verified Cambridge University Press reprint instead.
- Page ranges for `lundberg2017unified` and `paszke2019pytorch` are omitted. The NeurIPS proceedings pages do not list them, and secondary sources disagree for PyTorch.
