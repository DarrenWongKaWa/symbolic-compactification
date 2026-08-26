"""Deterministic Structure Hypothesis Agent.

Maps observations → typed hypotheses. Does not construct a full expression
and does not decide truth. Aggressive hypotheses are allowed; the verifier
rejects them.
"""
from __future__ import annotations

from research.structure_discovery.prototype.hypothesis import (
    Auxiliary,
    StructureHypothesis,
)


def _aux(name: str, definition: str, role: str) -> Auxiliary:
    return Auxiliary(name=name, definition=definition, role=role)


def hypotheses_from_observations(
    obs: dict,
    *,
    aggressive: bool = True,
    max_hypotheses: int = 10,
    feature_mask: dict | None = None,
) -> list[StructureHypothesis]:
    """feature_mask keys (all default True): repeated, permutation,
    denominators, piecewise, divided_difference, families, polygamma.
    """
    mask = {
        "repeated": True,
        "permutation": True,
        "denominators": True,
        "piecewise": True,
        "divided_difference": True,
        "families": True,
        "polygamma": True,
    }
    if feature_mask:
        mask.update(feature_mask)
    out: list[StructureHypothesis] = []

    if mask["repeated"]:
        for i, cf in enumerate(obs.get("common_factors") or []):
            name = f"C{i}"
            out.append(StructureHypothesis(
                hypothesis_type="repeated_kernel",
                target_subexpressions=[cf["text"]],
                claimed_structure=(
                    f"factor {cf['text']} is common to {cf['n_terms']} terms"
                ),
                proposed_auxiliaries=[_aux(name, cf["text"], "kernel")],
                expected_benefit="collect a shared prefactor",
                construction_plan="factor the common multiplicative piece",
                verification_obligations=["E - E[C:=def] = 0"],
                confidence=0.75,
                observation_support=["common_factors"],
            ))
        for i, r in enumerate(obs.get("repeated_subtrees") or []):
            if r["count"] < 2:
                continue
            name = f"K{i}"
            out.append(StructureHypothesis(
                hypothesis_type="repeated_kernel",
                target_subexpressions=[r["text"]],
                claimed_structure=(
                    f"subtree {r['text']} occurs {r['count']} times and "
                    "can be named as a reusable kernel"
                ),
                proposed_auxiliaries=[_aux(name, r["text"], "kernel")],
                expected_benefit="expose a repeated mathematical object",
                construction_plan="replace each occurrence with the named kernel",
                verification_obligations=["E - E[K:=def] = 0"],
                confidence=min(0.9, 0.4 + 0.15 * r["count"]),
                observation_support=["repeated_subtrees"],
            ))

    if mask["permutation"]:
        for i, p in enumerate(obs.get("permutation_pairs") or []):
            swap = None
            la, ra = p.get("left_args") or [], p.get("right_args") or []
            if len(la) == 2 and la[::-1] == ra:
                swap = [la[0], la[1]]
            out.append(StructureHypothesis(
                hypothesis_type="permutation_orbit",
                target_subexpressions=[p["left"], p["right"]],
                claimed_structure=(
                    f"{p['name']} appears with permuted arguments; "
                    "terms form a swap orbit"
                ),
                proposed_auxiliaries=[
                    _aux(f"P{i}", p["left"], "generator"),
                    _aux(f"Pswap{i}", p["right"], "generator"),
                ],
                expected_benefit="expose index-exchange symmetry",
                construction_plan=(
                    "reconstruct as first_term + swap(first_term) "
                    "with equal weight (pure orbit)"
                ),
                verification_obligations=["E - (T + swap(T)) = 0"],
                confidence=0.7,
                swap_pair=swap,
                observation_support=["permutation_pairs"],
                aggressive=True,
            ))
            out.append(StructureHypothesis(
                hypothesis_type="symmetry_invariant",
                target_subexpressions=[p["left"], p["right"]],
                claimed_structure="pair is a symmetry-adapted generator and its image",
                proposed_auxiliaries=[_aux(f"G{i}", p["left"], "generator")],
                expected_benefit="make the generating object explicit",
                construction_plan="same as permutation_orbit",
                confidence=0.55,
                swap_pair=swap,
                observation_support=["permutation_pairs"],
            ))

    if mask["families"]:
        family_source = list(obs.get("function_families") or []) + list(
            obs.get("builtin_families") or []
        )
        for i, fam in enumerate(family_source):
            if fam["n_distinct"] >= 3 and fam["n_occurrences"] >= 3:
                examples = fam["examples"]
                out.append(StructureHypothesis(
                    hypothesis_type="master_function",
                    target_subexpressions=examples[:6],
                    claimed_structure=(
                        f"{fam['name']} is specialized at several arguments; "
                        "one master object generates the family"
                    ),
                    proposed_auxiliaries=[
                        _aux(f"Phi{i}", examples[0], "master"),
                    ],
                    expected_benefit="collapse a family to one generator",
                    construction_plan="write the sum as Phi at each observed argument",
                    confidence=0.6,
                    observation_support=["function_families"],
                ))
            if fam["n_distinct"] >= 2 and any(
                "epsilon" in ex or "e(" in ex or "omega" in ex
                for ex in fam["examples"]
            ):
                out.append(StructureHypothesis(
                    hypothesis_type="spectral_family",
                    target_subexpressions=fam["examples"][:6],
                    claimed_structure="repeated spectral / resolvent-like calls",
                    proposed_auxiliaries=[_aux(f"Res{i}", fam["examples"][0], "kernel")],
                    construction_plan="name the resolvent and reuse it",
                    confidence=0.45,
                    observation_support=["function_families"],
                ))

    if mask["divided_difference"]:
        for i, hit in enumerate(obs.get("divided_difference_hits") or []):
            out.append(StructureHypothesis(
                hypothesis_type="divided_difference",
                target_subexpressions=[hit["term"]],
                claimed_structure=(
                    f"( {hit['function']}({hit['u']}) - {hit['function']}({hit['v']}) ) "
                    f"/ ({hit['u']} - {hit['v']}) is a divided difference"
                ),
                proposed_auxiliaries=[_aux(f"DD{i}", hit["term"], "divided_difference")],
                expected_benefit="change representation from explicit difference quotient",
                construction_plan="name the quotient; reconstruction is the quotient itself",
                confidence=0.8,
                observation_support=["divided_difference_hits"],
            ))

    if mask["piecewise"]:
        for i, pw in enumerate(obs.get("piecewise") or []):
            values = [b["value"] for b in pw["branches"]]
            out.append(StructureHypothesis(
                hypothesis_type="confluent_representation",
                target_subexpressions=[pw["text"]] + values,
                claimed_structure=(
                    "Piecewise branches come from one object"
                    + (" (identical values)" if pw["all_values_equal"] else
                       " (aggressive: first branch as the unified form)")
                ),
                proposed_auxiliaries=[_aux(f"U{i}", values[0], "confluent")],
                expected_benefit="unify branch language",
                construction_plan=(
                    "if all values equal, drop Piecewise; else replace by first value"
                ),
                confidence=0.85 if pw["all_values_equal"] else 0.35,
                observation_support=["piecewise"],
                aggressive=not pw["all_values_equal"],
            ))

    if mask["polygamma"] and len(obs.get("polygamma_calls") or []) >= 2:
        zs = {p["z"] for p in obs["polygamma_calls"]}
        ns = {p["n"] for p in obs["polygamma_calls"]}
        if len(zs) <= 2 and len(ns) >= 2:
            texts = [p["text"] for p in obs["polygamma_calls"]]
            out.append(StructureHypothesis(
                hypothesis_type="derivative_family",
                target_subexpressions=texts,
                claimed_structure="polygamma orders at related arguments form one family",
                proposed_auxiliaries=[_aux("PsiMaster", texts[0], "master")],
                construction_plan="name the lowest-order polygamma as master",
                confidence=0.5,
                observation_support=["polygamma_calls"],
            ))

    dens = obs.get("denominators") or []
    if mask["denominators"] and len(dens) >= 2:
        out.append(StructureHypothesis(
            hypothesis_type="spectral_family",
            target_subexpressions=[f"1/({d['text']})" for d in dens[:6]],
            claimed_structure=(
                "several denominators share a resolvent-like skeleton and "
                "may be specializations of one spectral object"
            ),
            proposed_auxiliaries=[_aux("ResFam", f"1/({dens[0]['text']})", "kernel")],
            expected_benefit="expose a shared resolvent generator",
            construction_plan="keep each pole distinct; name the family, do not collapse",
            confidence=0.5,
            observation_support=["denominators"],
        ))
    if aggressive and mask["denominators"]:
        if len(dens) >= 2:
            # similar poles: share a symbol and comparable ops
            for i, a in enumerate(dens):
                for b in dens[i + 1:]:
                    sa, sb = set(a["free_symbols"]), set(b["free_symbols"])
                    if not sa.intersection(sb):
                        continue
                    if a["text"] == b["text"]:
                        continue
                    if abs(a["ops"] - b["ops"]) > 2:
                        continue
                    out.append(StructureHypothesis(
                        hypothesis_type="identical_kernel_merge",
                        target_subexpressions=[
                            f"1/({a['text']})", f"1/({b['text']})",
                        ],
                        claimed_structure=(
                            "two denominators look similar and might be one kernel "
                            "(aggressive; often false)"
                        ),
                        proposed_auxiliaries=[
                            _aux(f"Kmerge{i}", f"1/({a['text']})", "kernel"),
                        ],
                        expected_benefit="collapse two poles to one channel",
                        construction_plan=(
                            "replace the expression by n_terms * first_named_kernel "
                            "when the top-level is a sum of two similar pole terms"
                        ),
                        required_assumptions=["denominators are algebraically identical"],
                        verification_obligations=["must fail if poles actually differ"],
                        confidence=0.25,
                        observation_support=["denominators"],
                        aggressive=True,
                    ))

    # de-dup by (type, first target)
    uniq = []
    seen = set()
    for h in out:
        key = (h.hypothesis_type, tuple(h.target_subexpressions[:2]))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(h)
    uniq.sort(key=lambda h: (-h.confidence, h.hypothesis_type))
    return uniq[:max_hypotheses]
