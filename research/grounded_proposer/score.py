"""Score P1: grounding is exact by contract, then compile+verify."""
from __future__ import annotations

from research.grounded_proposer.schema import OK, PARSE_FAILURE
from research.obligation_ir.grounding import Binding, EXACT_BIND
from research.obligation_ir.repr_compile import compile_confluence, compile_dd, compile_derivative_identities
from research.obligation_ir.source_index import SourceIndex


def binds_from_p1(hyp: dict, index: SourceIndex) -> list[Binding]:
    ids = []
    for m in hyp.get("member_maps") or []:
        if isinstance(m, dict) and m.get("source_node_id"):
            ids.append(m["source_node_id"])
    for k in ("generic_member", "degenerate_member"):
        if hyp.get(k):
            ids.append(hyp[k])
    out = []
    seen = set()
    for nid in ids:
        if nid in seen:
            continue
        seen.add(nid)
        n = index.by_gid.get(nid)
        if n is None:
            out.append(Binding(alias=nid, confidence="NO_BIND", evidence="missing_catalog"))
            continue
        out.append(Binding(
            alias=nid, confidence=EXACT_BIND, gid=n.gid,
            sol_node_id=n.sol_node_id, text=n.text, srepr=n.srepr,
            kind=n.kind, cond=n.cond, evidence="p1_catalog_id",
            unique_kind="UNIQUE_BY_SOL_ID", n_candidates=1,
        ))
    return out


def score_p1_hyp(hyp: dict, index: SourceIndex, *, symbols, functions) -> dict:
    if hyp.get("parse_status") == PARSE_FAILURE:
        return {"layer": "G", "detail": "parse_failure", "verdicts": []}
    binds = binds_from_p1(hyp, index)
    if not binds or any(not b.admissible for b in binds):
        return {"layer": "G", "detail": "id_not_in_index", "verdicts": []}
    htype = hyp.get("representation_type") or ""
    fake = {
        "hypothesis_type": htype,
        "latent_object": hyp.get("latent_object") or "",
        "instance_maps": [
            {"member": b.alias, "theta": {"nodes": ["epsilon(m)", "epsilon(n)"],
                                          "collision": "True" if "true" in (b.cond or "").lower() else "Eq(m,n)"}}
            for b in binds
        ],
    }
    rows = []
    if htype == "divided_difference":
        rows += compile_dd(fake, binds, index, symbols=symbols, functions=functions)
    if htype in {"confluent_representation", "divided_difference"}:
        rows += compile_confluence(fake, binds, index, symbols=symbols, functions=functions)
    if htype in {"derivative_family", "master_function"}:
        rows += compile_derivative_identities(fake, binds, symbols=symbols, functions=functions)
    verdicts = [v.verdict for _, v in rows]
    if not rows:
        return {"layer": "C", "detail": "bound_not_compiled", "verdicts": [], "n_bind": len(binds)}
    if "ZERO" in verdicts and "NONZERO" not in verdicts and "UNKNOWN" not in verdicts:
        return {"layer": "OK", "detail": "certified", "verdicts": verdicts, "n_bind": len(binds)}
    if "NONZERO" in verdicts and "ZERO" not in verdicts:
        return {"layer": "D", "detail": "wrong_structure", "verdicts": verdicts, "n_bind": len(binds)}
    if "UNKNOWN" in verdicts:
        return {"layer": "V", "detail": "unknown", "verdicts": verdicts, "n_bind": len(binds)}
    return {"layer": "V", "detail": "mixed", "verdicts": verdicts, "n_bind": len(binds)}
