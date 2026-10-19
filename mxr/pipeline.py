"""Per-scenario stages for the full experiment (protocol v0.2, amendments 1-2).

The tokenization, scoring, greedy and repeatability stages follow
run_feasibility.py exactly (an equivalence test checks this); the flip and
citation stages are new.
"""
from __future__ import annotations

from . import design
from .citations import citation_messages, parse_citation
from .scoring import TokenizationError

REPEAT_CELLS = (("E1+E2+E3+E4", 0), ("none", 1), ("E2", 2))


def cell_spec():
    return [(s, k) for k in range(len(design.ORDERINGS)) for s in design.all_subsets()]


def tokenization_stage(scorer, scenario):
    """Validate every prompt this scenario will score (lattice cells and, if present, flip cells)."""
    rows = []
    prompts = [(design.subset_key(s), k, False, design.render(scenario, s, k)["user_msg"]) for s, k in cell_spec()]
    if "flip" in scenario:
        fr = design.flip_records(scenario)
        full = frozenset(design.CANONICAL)
        prompts += [(design.subset_key(full), k, True, design.render(scenario, full, k, records=fr)["user_msg"])
                    for k in range(len(design.ORDERINGS))]
    for key, k, flipped, msg in prompts:
        row = {"subset": key, "ordering": k, "flipped": flipped}
        try:
            rt = scorer.template_roundtrip(msg)
            lt = scorer.label_tokenization(msg)
            row.update(roundtrip_ok=bool(rt["ok"]), roundtrip=rt, label_ids=lt["label_ids"],
                       label_tokens=lt["label_tokens"], prompt_len=lt["prompt_len"])
        except TokenizationError as exc:
            row.update(roundtrip_ok=False, error=str(exc), label_ids={})
        rows.append(row)
    bad = [t for t in rows if t.get("error") or not t["roundtrip_ok"]]
    label_sets = {repr(sorted((k, tuple(v)) for k, v in t["label_ids"].items()))
                  for t in rows if not t.get("error")}
    ok = not bad and len(label_sets) == 1
    lattice_rows = [t for t in rows if not t["flipped"]]
    return rows, lattice_rows, ok


def scoring_stage(scorer, scenario, sink=None, log=print):
    cells = []
    for i, (s, k) in enumerate(cell_spec(), 1):
        r = design.render(scenario, s, k)
        sc = scorer.score(r["user_msg"])
        rec = {
            "scenario_id": scenario["scenario_id"],
            "subset": design.subset_key(s),
            "subset_members": sorted(s),
            "mask": design.subset_mask(s),
            "ordering": k,
            "shown_canonical": r["shown_canonical"],
            "shown_ids": r["shown_ids"],
            "designed_answer": design.designed_answer(scenario, s),
            "user_msg": r["user_msg"],
            "score": sc,
        }
        if sink is not None:
            sink(rec)
        cells.append(rec)
        if log:
            log(f"  [{i:2d}/48] ordering {k} {rec['subset']:<12} argmax={sc['argmax']:<8} "
                f"mass={sc['label_mass']:.3f}")
    return cells


def greedy_stage(scorer, cells, max_label_len):
    rows = []
    for rec in cells:
        g = scorer.greedy(rec["user_msg"], max_new_tokens=max_label_len + 1)
        arg = rec["score"]["argmax"]
        arg_ids = rec["score"]["labels"][arg]["token_ids"]
        rows.append({
            "subset": rec["subset"], "ordering": rec["ordering"], "argmax": arg,
            "argmax_ids": arg_ids, "greedy_ids": g["token_ids"], "greedy_text": g["text"],
            "token_match": list(g["token_ids"][: len(arg_ids)]) == list(arg_ids),
            "margin": rec["score"]["top2_margin"],
        })
    return rows


def repeat_stage(scorer, cells):
    index = {(c["subset"], c["ordering"]): c for c in cells}
    rows = []
    for key, k in REPEAT_CELLS:
        rec = index[(key, k)]
        sc2 = scorer.score(rec["user_msg"])
        diff = max(abs(sc2["labels"][l]["logprob"] - rec["score"]["labels"][l]["logprob"])
                   for l in design.LABELS)
        rows.append({"subset": key, "ordering": k, "max_abs_diff": diff})
    return rows


def flip_stage(scorer, scenario, analysis, max_label_len):
    """Full-set cells with the pre-specified flip applied, in all 3 orderings."""
    d_star = analysis["d_star"]
    full = frozenset(design.CANONICAL)
    fr = design.flip_records(scenario)
    rows = []
    for k in range(len(design.ORDERINGS)):
        r = design.render(scenario, full, k, records=fr)
        sc = scorer.score(r["user_msg"])
        g = scorer.greedy(r["user_msg"], max_new_tokens=max_label_len + 1)
        arg_ids = sc["labels"][sc["argmax"]]["token_ids"]
        rows.append({
            "ordering": k, "flip_target": scenario["flip"]["target"], "user_msg": r["user_msg"],
            "p_norm": sc["p_norm"], "argmax": sc["argmax"], "label_mass": sc["label_mass"],
            "finite": sc["finite"], "top2_margin": sc["top2_margin"],
            "greedy_text": g["text"], "greedy_token_match": list(g["token_ids"][: len(arg_ids)]) == list(arg_ids),
            "p_d_star_flipped": sc["p_norm"][d_star],
            "p_d_star_original": analysis["per_ordering"][k]["v_full"],
            "moved_away_from_d_star": sc["argmax"] != d_star,
            "rubric_reference_flipped": scenario["flip"]["reference_answer"],
            "score": sc,
        })
    return rows


def citation_stage(scorer, scenario, analysis, scenario_index, cfg):
    """Greedy reference citation per ordering plus seeded sampled citations (amendment 2)."""
    d_star = analysis["d_star"]
    full = frozenset(design.CANONICAL)
    rows = []
    sample_index = 0
    for k, n_samples in enumerate(cfg["samples_per_ordering"]):
        r = design.render(scenario, full, k)
        msgs = citation_messages(r["user_msg"], d_star)
        plan = [("greedy", None)] * cfg["greedy_reference_per_ordering"]
        for _ in range(n_samples):
            plan.append(("sampled", 10000 + 100 * scenario_index + sample_index))
            sample_index += 1
        for kind, seed in plan:
            temperature = 0.0 if kind == "greedy" else cfg["temperature"]
            text = scorer.generate_chat(msgs, max_new_tokens=cfg["max_new_tokens"],
                                        temperature=temperature, seed=seed if seed is not None else 0)
            parsed = parse_citation(text, r["shown_ids"], r["id_to_canonical"])
            rows.append({"scenario_id": scenario["scenario_id"], "ordering": k, "kind": kind,
                         "seed": seed, "temperature": temperature, "decision_in_context": d_star,
                         "shown_ids": r["shown_ids"], "id_to_canonical": r["id_to_canonical"],
                         "raw": text, "parse": parsed})
    return rows
