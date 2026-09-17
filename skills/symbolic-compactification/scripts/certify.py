#!/usr/bin/env python3
"""Assemble canonical audit.json from a proposal.

The proposal may contain reconstructed edges and commentary. Machine
statuses are overwritten from engine receipts. Without the engine, no
edge is allowed to stay EXACT / EXACT_IF_ASSUMPTIONS.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def _load_ledger():
    path = Path(__file__).resolve().parent / "ledger.py"
    spec = importlib.util.spec_from_file_location("ssc_skill_ledger", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _kind_status(kind: str, fallback: str) -> str:
    kind_u = (kind or "").upper()
    if kind_u in {"STRUCTURAL", "DEFINITION", "BOOKKEEPING"}:
        return "STRUCTURAL"
    if kind_u in {"CITED_RULE"}:
        return "CITED_RULE"
    if kind_u in {"ASYMPTOTIC", "LIMIT", "INTEGRAL"}:
        return "ASYMPTOTIC_UNCERTIFIED"
    return fallback


def certify(proposal: dict, *, inventory: dict | None = None) -> dict:
    ledger = _load_ledger()
    data = json.loads(json.dumps(proposal))
    if inventory is not None:
        data["inventory"] = inventory
    receipts: dict[str, dict] = {}
    verify = ledger.load_verify_equivalent()
    identity = ledger.engine_identity()
    for edge in data.get("edges") or []:
        kind = str(edge.get("kind") or "")
        model_status = edge.get("status")
        if model_status in ledger.MACHINE_GREEN:
            edge["status"] = "GAP"
        structural = _kind_status(kind, "")
        if structural:
            edge["status"] = structural
            continue
        lhs = edge.get("lhs")
        rhs = edge.get("rhs")
        symbols = edge.get("symbols") or []
        assumptions = edge.get("assumptions") or []
        if not (lhs and rhs and symbols and verify is not None):
            if edge.get("status") in ledger.MACHINE_GREEN or not edge.get("status"):
                edge["status"] = "GAP"
            continue
        result = verify(
            lhs,
            rhs,
            symbols,
            assumptions={"declared": assumptions},
            functions=edge.get("functions"),
        )
        verdict = result.verdict
        receipt = ledger.make_receipt(
            edge_id=edge.get("id") or "",
            lhs=lhs,
            rhs=rhs,
            assumptions=assumptions,
            symbols=symbols,
            domain=str(edge.get("domain") or ""),
            kind=kind,
            verdict=verdict,
            residual=getattr(result, "residual", "") or "",
            counterexample=getattr(result, "counterexample", None),
            functions=edge.get("functions") or [],
            from_eq=str(edge.get("from_eq") or ""),
            to_eq=str(edge.get("to_eq") or ""),
            from_source_hash=ledger.equation_source_hash(
                data, str(edge.get("from_eq") or "")
            ),
            to_source_hash=ledger.equation_source_hash(
                data, str(edge.get("to_eq") or "")
            ),
        )
        receipts[edge["id"]] = receipt
        edge["status"] = ledger.status_from_verdict(
            verdict, assumptions=assumptions, kind=kind
        )
        if ledger.remainder_language(str(edge.get("transformation") or "")):
            if edge["status"] in ledger.MACHINE_GREEN:
                edge["status"] = "ASYMPTOTIC_UNCERTIFIED"
    for claim in data.get("claims") or []:
        related = ledger.supporting_edges(claim, data.get("edges") or [])
        claim["related_edge_ids"] = [
            edge.get("id") for edge in related if edge.get("id")
        ]
        compiled = bool(
            claim.get("lhs") and claim.get("rhs") and claim.get("symbols")
        )
        if ledger.remainder_language(str(claim.get("statement") or "")):
            claim["status"] = "ASYMPTOTIC_UNCERTIFIED"
            continue
        if any(edge.get("status") == "NONZERO_RESIDUAL" for edge in related):
            claim["status"] = "NONZERO_RESIDUAL"
            continue
        if not compiled:
            if claim.get("status") in ledger.MACHINE_GREEN:
                claim["status"] = "GAP"
            continue
        if verify is None:
            claim["status"] = "GAP"
            continue
        result = verify(
            claim["lhs"],
            claim["rhs"],
            claim["symbols"],
            assumptions={"declared": claim.get("assumptions") or []},
            functions=claim.get("functions"),
        )
        receipts[claim["id"]] = ledger.make_receipt(
            edge_id=claim.get("id") or "",
            lhs=claim["lhs"],
            rhs=claim["rhs"],
            assumptions=claim.get("assumptions") or [],
            symbols=claim["symbols"],
            domain=str(claim.get("domain") or ""),
            kind=str(claim.get("kind") or ""),
            verdict=result.verdict,
            residual=getattr(result, "residual", "") or "",
            counterexample=getattr(result, "counterexample", None),
            functions=claim.get("functions") or [],
        )
        claim["status"] = ledger.status_from_verdict(
            result.verdict,
            assumptions=claim.get("assumptions") or [],
            kind=str(claim.get("kind") or ""),
        )
    data["certification"] = {
        "issuer": ledger.CERTIFY_ISSUER,
        "engine": identity,
        "engine_available": verify is not None,
        "receipts": receipts,
    }
    data["summary"] = ledger.compute_summary(data)
    if data["summary"]["overall_state"] not in ledger.ALLOWED_OVERALL:
        data["summary"]["overall_state"] = "AUDIT_INCOMPLETE"
    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Derive machine statuses from engine receipts"
    )
    parser.add_argument("--proposal", type=Path, help="proposal JSON (statuses ignored)")
    parser.add_argument("--audit", type=Path, help="existing audit.json to recertify")
    parser.add_argument("--inventory", type=Path, default=None)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    source = args.proposal or args.audit
    if source is None:
        parser.error("provide --proposal or --audit")
    proposal = json.loads(source.read_text(encoding="utf-8"))
    inventory = None
    if args.inventory:
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    data = certify(proposal, inventory=inventory)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    ledger = _load_ledger()
    err = ledger.check_ledger(data)
    if err:
        print("CERTIFY_FAIL")
        for item in err:
            print(" -", item)
        return 1
    print("CERTIFY_OK", args.out)
    print("engine_available", data["certification"]["engine_available"])
    print("machine_certified_edges", data["summary"]["machine_certified_edges"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
