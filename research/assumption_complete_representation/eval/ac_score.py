"""D/G/C/V/Q scoring. Hidden gold is evaluator-only."""
from __future__ import annotations

import re
from typing import Any

from research.assumption_complete_representation.eval.ac_compile import (
    catalog_map,
    compile_and_verify,
    member_text,
)
from research.assumption_complete_representation.eval.pack_data import R_LEVEL

_GID = re.compile(r"G\d{4}")
SCORER_VERSION = "ac-score-v1.2"

TYPE_TO_R = [
    (tuple("hermite repeated_node repeated-node confluent multiplicity".split()), 3),
    (tuple("divided_difference newton difference_quotient newton_dd".split()), 2),
    (tuple("piecewise degeneracy unification".split()), 4),
    (tuple("master_library library_learning".split()), 7),
    (tuple("master".split()), 6),
    (tuple("invariant generator young basis projector".split()), 8),
    (tuple("special_function polygamma digamma trigamma tanh reflection series dlmf".split()), 5),
    (tuple("parameterized_family family".split()), 1),
    (tuple("repeated_kernel repeated_structure cse".split()), 0),
]


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")


def proposed_depth(hyp: dict) -> int | None:
    blob = _norm(
        " ".join([
            str(hyp.get("representation_type") or ""),
            str(hyp.get("rationale") or ""),
            str(hyp.get("reconstruction_rule") or ""),
        ])
    )
    for keys, n in TYPE_TO_R:
        if any(k in blob for k in keys):
            return n
    return None


def type_match(hyp: dict, hidden: dict) -> bool:
    blob = _norm(
        " ".join([
            str(hyp.get("representation_type") or ""),
            str(hyp.get("rationale") or ""),
            str(hyp.get("reconstruction_rule") or ""),
            str(hyp.get("latent_object") or ""),
        ])
    )
    fam = hidden.get("representation_family") or []
    return any(_norm(f) and _norm(f) in blob for f in fam)


def is_operational(hyp: dict) -> bool:
    if hyp.get("parse_status") != "OK":
        return False
    F = (hyp.get("latent_object") or "").strip()
    recon = (hyp.get("reconstruction_rule") or "").strip()
    maps = hyp.get("member_maps") or []
    ops = hyp.get("operators") or []
    gids = []
    for m in maps:
        if isinstance(m, dict) and m.get("source_node_id"):
            gids.append(str(m["source_node_id"]))
    return bool(F) and bool(recon) and bool(gids) and bool(ops)


def grounded(hyp: dict, pack: dict) -> str:
    cmap = catalog_map(pack)
    ids = set(cmap)
    got = set()
    for m in hyp.get("member_maps") or []:
        if not isinstance(m, dict):
            return "G_FAIL"
        gid = str(m.get("source_node_id") or "")
        if not gid:
            return "G_FAIL"
        if gid not in ids:
            return "G_FAIL"
        got.add(gid)
    if not got:
        return "G_FAIL"
    return "G_OK"


def residual_ids(pack: dict) -> set[str]:
    cur = "".join((pack.get("current") or "").split())
    out = set()
    if not cur:
        return out
    for e in pack.get("catalog") or []:
        if "".join((e.get("text") or "").split()) == cur:
            out.add(e["source_node_id"])
    return out


def n_nontrivial_zero(compiled: dict, pack: dict) -> int:
    """ZERO obligations that are not F-specialization renames or residual restatements."""
    residual = residual_ids(pack)
    n = 0
    for o in compiled.get("obligations") or []:
        if o.get("verdict") != "ZERO" or o.get("note") != "parsed_eq":
            continue
        text = o.get("text") or ""
        gids = set(_GID.findall(text))
        if gids and gids <= residual:
            continue
        if gids & residual:
            continue
        nF = len(re.findall(r"\bF\s*\(", text))
        nG = len(_GID.findall(text))
        if nF >= 2:
            n += 1
            continue
        if nG >= 2:
            n += 1
            continue
        if nF >= 1 and ("/" in text or "*" in text):
            n += 1
            continue
        # raw special-function identity with two distinct heads, e.g. psi vs tanh
        # counted only when not a single F(arg) rename
        if nF <= 1 and nG <= 1 and "/" not in text and "*" not in text:
            continue
        n += 1
    return n


def _tautological(hyp: dict, pack: dict) -> bool:
    maps = hyp.get("member_maps") or []
    F = (hyp.get("latent_object") or "").strip()
    recon = (hyp.get("reconstruction_rule") or "").strip()
    if len(maps) <= 1 and F and pack.get("current") and F.replace(" ", "") in (
        pack.get("current") or ""
    ).replace(" ", ""):
        return True
    if recon.replace(" ", "") in {F.replace(" ", ""), (pack.get("current") or "").replace(" ", "")}:
        if len(maps) <= 1:
            return True
    blob = (F + " " + recon).lower()
    if "equals itself" in blob or "identical to itself" in blob:
        return True
    return False


def _shallow_repack(hyp: dict, pack: dict, hidden: dict) -> bool:
    if hidden.get("nontrivial") is False:
        # defining-series restatement
        if type_match(hyp, hidden) or "series" in _norm(hyp.get("representation_type") or ""):
            return True
    rtype = _norm(hyp.get("representation_type") or "")
    if any(k in rtype for k in (
        "algebraic_cancellation", "term_sum", "addition", "cse",
        "cataloged_pair", "residual",
    )):
        return True
    ops = hyp.get("operators") or []
    names = " ".join(
        str(o.get("name") or o.get("O") or o) if isinstance(o, dict) else str(o)
        for o in ops
    ).lower()
    if names.strip() in {"addition", "add", "sum"} and len(ops) <= 3:
        if not type_match(hyp, hidden):
            return True
    return False


def score_hypothesis(hyp: dict, pack: dict, hidden: dict, compiled: dict) -> dict:
    op = is_operational(hyp)
    tmatch = type_match(hyp, hidden)
    g = grounded(hyp, pack) if hyp.get("parse_status") == "OK" else "G_FAIL"
    cstat = compiled.get("compile_status") or "C_FAIL"
    n_zero = int(compiled.get("n_zero") or 0)
    n_nz = int(compiled.get("n_nonzero") or 0)
    n_unk = int(compiled.get("n_unknown") or 0)
    if n_nz > 0:
        v = "NONZERO"
    elif n_zero > 0 and n_unk == 0:
        v = "ZERO"
    elif n_zero > 0 and n_unk > 0:
        v = "UNKNOWN"
    elif cstat == "C_FAIL":
        v = "UNKNOWN"
    else:
        v = "UNKNOWN"

    taut = _tautological(hyp, pack)
    shallow = _shallow_repack(hyp, pack, hidden)
    n_ntz = n_nontrivial_zero(compiled, pack)
    if n_zero > 0 and n_ntz == 0:
        taut = True

    if hyp.get("parse_status") != "OK":
        d = "D_WRONG"
        q = "COMPILE_FAILURE"
    elif taut:
        d = "D_SHALLOW"
        q = "TAUTOLOGICAL"
    elif shallow and not (tmatch and op):
        d = "D_SHALLOW"
        q = "SHALLOW_REPACKAGING"
    elif tmatch and op:
        d = "D_CORRECT"
        q = "OPERATIONAL_CORRECT" if (g == "G_OK" and cstat == "C_OK" and v == "ZERO" and not taut) else (
            "TYPE_ONLY" if not op else
            "WRONG_MEMBER" if g == "G_FAIL" else
            "COMPILE_FAILURE" if cstat == "C_FAIL" else
            "VERIFIER_UNKNOWN" if v == "UNKNOWN" else
            "WRONG_REPRESENTATION" if v == "NONZERO" else
            "OPERATIONAL_CORRECT"
        )
        if tmatch and op and not (g == "G_OK" and cstat == "C_OK" and v == "ZERO"):
            if q == "OPERATIONAL_CORRECT":
                q = "VERIFIER_UNKNOWN"
    elif tmatch and not op:
        d = "D_TYPE_ONLY"
        q = "TYPE_ONLY"
    else:
        d = "D_WRONG"
        q = "WRONG_REPRESENTATION"

    if d == "D_CORRECT" and g == "G_FAIL":
        q = "WRONG_MEMBER"
    if cstat == "C_FAIL" and q not in {"TAUTOLOGICAL", "SHALLOW_REPACKAGING", "TYPE_ONLY"}:
        if d != "D_TYPE_ONLY":
            q = "COMPILE_FAILURE"

    pdepth = proposed_depth(hyp)
    gold_n = hidden.get("ladder_n")
    cdepth = None
    if v == "ZERO" and d == "D_CORRECT" and g == "G_OK" and cstat == "C_OK" and not taut:
        cdepth = gold_n
    elif v == "ZERO" and not taut:
        # certified something weaker than the gold class
        cdepth = min(pdepth or 0, gold_n or 0)

    operational_success = (
        d == "D_CORRECT"
        and g == "G_OK"
        and cstat == "C_OK"
        and v == "ZERO"
        and not taut
        and hidden.get("nontrivial", True)
        and op
        and n_ntz > 0
    )
    if hidden.get("nontrivial") is False:
        operational_success = False
        if q == "OPERATIONAL_CORRECT":
            q = "SHALLOW_REPACKAGING"
            d = "D_SHALLOW"
    return {
        "D": d,
        "G": g,
        "C": cstat,
        "V": v,
        "Q": q,
        "type_match": tmatch,
        "operational": op,
        "tautological": taut,
        "shallow": shallow,
        "operational_success": operational_success,
        "PROPOSED_DEPTH": pdepth,
        "CERTIFIED_DEPTH": cdepth,
        "n_zero": n_zero,
        "n_nonzero": n_nz,
        "n_unknown": n_unk,
        "n_zero_nontrivial": n_ntz,
        "F_parsed": bool(compiled.get("F_parsed")),
        "scorer_version": SCORER_VERSION,
    }


def score_run(parsed: dict, pack: dict, hidden: dict) -> dict:
    hyps = parsed.get("hypotheses") or []
    scored = []
    for h in hyps:
        compiled = compile_and_verify(h, pack)
        sc = score_hypothesis(h, pack, hidden, compiled)
        scored.append({"hypothesis": h, "compile": compiled, "score": sc})
    ok = [s for s in scored if s["hypothesis"].get("parse_status") == "OK"]
    best = None
    for s in scored:
        if s["score"].get("operational_success"):
            best = s
            break
    if best is None and scored:
        order = ["OPERATIONAL_CORRECT", "TYPE_ONLY", "SHALLOW_REPACKAGING",
                 "TAUTOLOGICAL", "VERIFIER_UNKNOWN", "COMPILE_FAILURE",
                 "WRONG_MEMBER", "WRONG_REPRESENTATION"]
        scored_sorted = sorted(
            scored,
            key=lambda s: order.index(s["score"]["Q"]) if s["score"]["Q"] in order else 99,
        )
        best = scored_sorted[0]
    return {
        "parse_status": parsed.get("parse_status"),
        "format_wrap": parsed.get("format_wrap"),
        "n_hypotheses": len(ok),
        "abstain": parsed.get("abstain"),
        "items": scored,
        "best": None if best is None else {
            "Q": best["score"]["Q"],
            "D": best["score"]["D"],
            "G": best["score"]["G"],
            "C": best["score"]["C"],
            "V": best["score"]["V"],
            "operational_success": best["score"]["operational_success"],
            "type_match": best["score"]["type_match"],
            "PROPOSED_DEPTH": best["score"]["PROPOSED_DEPTH"],
            "CERTIFIED_DEPTH": best["score"]["CERTIFIED_DEPTH"],
        },
        "any_operational_success": any(s["score"]["operational_success"] for s in scored),
        "any_type_match": any(s["score"]["type_match"] for s in scored),
        "any_type_only": any(s["score"]["Q"] == "TYPE_ONLY" for s in scored),
        "any_tautological": any(s["score"]["tautological"] for s in scored),
        "max_proposed_depth": max(
            (s["score"]["PROPOSED_DEPTH"] for s in scored
             if s["score"]["PROPOSED_DEPTH"] is not None),
            default=None,
        ),
        "max_certified_depth": max(
            (s["score"]["CERTIFIED_DEPTH"] for s in scored
             if s["score"]["CERTIFIED_DEPTH"] is not None),
            default=None,
        ),
    }
