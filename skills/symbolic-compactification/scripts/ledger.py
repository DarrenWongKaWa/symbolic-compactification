#!/usr/bin/env python3
"""Evidence-chain helpers. Stdlib-only.

The model may propose expressions, edges, and commentary. It does not
issue machine statuses. EXACT / EXACT_IF_ASSUMPTIONS are derived from a
bound receipt after independent engine recomputation.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable, Optional

RECEIPT_SCHEMA = "VerificationReceiptV1"
CERTIFY_ISSUER = "scripts/certify.py"

ALLOWED_STATUSES = frozenset(
    {
        "EXACT",
        "EXACT_IF_ASSUMPTIONS",
        "STRUCTURAL",
        "CITED_RULE",
        "ASYMPTOTIC_UNCERTIFIED",
        "HUMAN_REVIEW",
        "GAP",
        "NONZERO_RESIDUAL",
        "NUMERICAL_SUPPORT",
        "UNCERTIFIED",
    }
)

MACHINE_GREEN = frozenset({"EXACT", "EXACT_IF_ASSUMPTIONS"})
STRUCTURAL_STATUSES = frozenset({"STRUCTURAL", "CITED_RULE"})
BLOCKING_STATUSES = frozenset(
    {
        "NONZERO_RESIDUAL",
        "GAP",
        "HUMAN_REVIEW",
        "ASYMPTOTIC_UNCERTIFIED",
        "NUMERICAL_SUPPORT",
        "UNCERTIFIED",
    }
)
ALLOWED_OVERALL = frozenset(
    {"AUDIT_INCOMPLETE", "DRAFT", "LOCAL_RESIDUALS_ONLY"}
)

EQ_TOKEN_RE = re.compile(r"\((\d+[a-z]?)\)|([A-Z]-\d+)|(M-\d+)")
REMAINDER_RE = re.compile(
    r"asymptotic|\bremainder\b|\bO\s*\(|\\mathcal\{O\}|uniform(?:ly)?\s+in",
    re.I,
)
_HASH_RE = re.compile(r"[0-9a-f]{64}\Z")


def canonical_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def binding_fields(payload: dict) -> dict:
    """Fields that bind a receipt to one scientific input."""
    return {
        "edge_id": payload.get("edge_id"),
        "lhs": payload.get("lhs"),
        "rhs": payload.get("rhs"),
        "assumptions": payload.get("assumptions") or [],
        "symbols": payload.get("symbols") or [],
        "functions": payload.get("functions") or [],
        "domain": payload.get("domain") or "",
        "kind": payload.get("kind") or "",
        "from_eq": payload.get("from_eq") or "",
        "to_eq": payload.get("to_eq") or "",
        "from_source_hash": payload.get("from_source_hash") or "",
        "to_source_hash": payload.get("to_source_hash") or "",
    }


def binding_hash(payload: dict) -> str:
    return sha256_text(canonical_dumps(binding_fields(payload)))


def eq_tokens(text: str) -> list[str]:
    out = []
    for match in EQ_TOKEN_RE.finditer(text or ""):
        out.append(
            f"({match.group(1)})"
            if match.group(1)
            else (match.group(2) or match.group(3))
        )
    return out


def lookup_equation(data: dict, token: str) -> dict | None:
    needle = (token or "").strip()
    if not needle:
        return None
    for eq in (data.get("inventory") or {}).get("equations") or []:
        if eq.get("public") == needle or eq.get("id") == needle:
            return eq
    return None


def equation_source_hash(data: dict, token: str) -> str:
    eq = lookup_equation(data, token)
    if not eq:
        return ""
    return sha256_text((eq.get("tex") or eq.get("cue") or "").strip())


def inventory_keys(data: dict) -> set[str]:
    keys: set[str] = set()
    equations = (data.get("inventory") or {}).get("equations") or []
    for eq in equations:
        for field in ("id", "public"):
            value = eq.get(field)
            if isinstance(value, str) and value.strip():
                keys.add(value.strip())
    return keys


def remainder_language(*texts: str) -> bool:
    return any(REMAINDER_RE.search(text or "") for text in texts)


def load_verify_equivalent() -> Optional[Callable[..., Any]]:
    try:
        from symbolic_compactification.verifier import verify_equivalent
    except ImportError:
        return None
    return verify_equivalent


def engine_identity() -> dict:
    identity = {
        "name": "python_sympy_exact_v1",
        "engine_version": "unavailable",
        "package_version": "unavailable",
        "git_sha": "unknown",
    }
    try:
        from symbolic_compactification.models import (
            ENGINE_VERSION,
            PACKAGE_VERSION,
            VERIFIER_NAME,
            engine_git_sha,
        )

        identity.update(
            {
                "name": VERIFIER_NAME,
                "engine_version": ENGINE_VERSION,
                "package_version": PACKAGE_VERSION,
                "git_sha": engine_git_sha(),
            }
        )
    except ImportError:
        pass
    return identity


def compute_summary(data: dict) -> dict:
    claims = data.get("claims") or []
    edges = data.get("edges") or []
    machine = sum(1 for edge in edges if edge.get("status") == "EXACT")
    conditional = sum(
        1 for edge in edges if edge.get("status") == "EXACT_IF_ASSUMPTIONS"
    )
    unresolved = 0
    for edge in edges:
        if edge.get("status") in MACHINE_GREEN | STRUCTURAL_STATUSES:
            continue
        unresolved += 1
    overall = "AUDIT_INCOMPLETE"
    if not claims and not edges:
        overall = "DRAFT"
    elif unresolved == 0 and machine > 0:
        overall = "LOCAL_RESIDUALS_ONLY"
    return {
        "overall_state": overall,
        "claim_count": len(claims),
        "relations_reconstructed": len(edges),
        "machine_certified_edges": machine,
        "assumption_dependent_edges": conditional,
        "unresolved_load_bearing": unresolved,
    }


def supporting_edges(claim: dict, edges: list) -> list[dict]:
    claimed = set(claim.get("supporting_equations") or [])
    unresolved = set(claim.get("unresolved") or [])
    related: list[dict] = []
    seen: set[str] = set()
    for edge in edges:
        eid = edge.get("id")
        tokens = set(
            eq_tokens(str(edge.get("from_eq") or ""))
            + eq_tokens(str(edge.get("to_eq") or ""))
        )
        if eid in unresolved or (claimed and tokens & claimed):
            if eid not in seen:
                related.append(edge)
                seen.add(eid)
    return related


def _receipts(data: dict) -> dict:
    cert = data.get("certification") or {}
    receipts = cert.get("receipts") or {}
    return receipts if isinstance(receipts, dict) else {}


def _recompute_verdict(receipt: dict) -> Optional[str]:
    verify = load_verify_equivalent()
    if verify is None:
        return None
    lhs = receipt.get("lhs")
    rhs = receipt.get("rhs")
    symbols = receipt.get("symbols") or []
    if not lhs or not rhs or not symbols:
        return "ERROR"
    result = verify(
        lhs,
        rhs,
        symbols,
        assumptions={"declared": receipt.get("assumptions") or []},
        functions=receipt.get("functions"),
    )
    return getattr(result, "verdict", None) or "ERROR"


def check_ledger(data: dict) -> list[str]:
    """Fail-closed structural + evidence-chain check. Does not trust model statuses."""
    err: list[str] = []
    if not isinstance(data, dict):
        return ["audit is not an object"]

    paper = data.get("paper")
    if not isinstance(paper, dict) or not paper.get("id") or not paper.get("title"):
        err.append("missing paper.id/title")
    if "claims" not in data:
        err.append("missing claims")
    if "edges" not in data:
        err.append("missing edges")
    inventory = data.get("inventory") or {}
    if "equations" not in inventory:
        err.append("missing inventory.equations")

    known = inventory_keys(data)
    claims = data.get("claims") or []
    edges = data.get("edges") or []
    obligations = data.get("reviewer_obligations") or []
    receipts = _receipts(data)
    by_id: dict[str, dict] = {}

    if not known and (claims or edges):
        err.append("inventory.equations is empty while claims/edges are present")

    for edge in edges:
        eid = edge.get("id")
        if not eid:
            err.append("edge missing id")
            continue
        if eid in by_id:
            err.append(f"duplicate edge id {eid}")
        by_id[eid] = edge
        status = edge.get("status")
        if status not in ALLOWED_STATUSES:
            err.append(f"edge {eid} bad status {status}")
            continue
        for token in eq_tokens(str(edge.get("from_eq") or "")) + eq_tokens(
            str(edge.get("to_eq") or "")
        ):
            if token not in known:
                err.append(f"edge {eid} unknown equation {token}")
        transform = str(edge.get("transformation") or "")
        if status in MACHINE_GREEN and remainder_language(transform):
            err.append(f"edge {eid} Exact on remainder/asymptotic language")
        if status == "EXACT_IF_ASSUMPTIONS" and not (edge.get("assumptions") or []):
            err.append(f"edge {eid} EXACT_IF_ASSUMPTIONS without assumptions")
        if status in MACHINE_GREEN:
            err.extend(_check_machine_green(edge, receipts.get(eid), data))

    seen_claims: set[str] = set()
    for claim in claims:
        cid = claim.get("id") or "?"
        if cid in seen_claims:
            err.append(f"duplicate claim id {cid}")
        seen_claims.add(cid)
        status = claim.get("status")
        if status not in ALLOWED_STATUSES:
            err.append(f"claim {cid} bad status {status}")
            continue
        statement = str(claim.get("statement") or "")
        if status in MACHINE_GREEN and remainder_language(statement):
            err.append(f"claim {cid} Exact on remainder/asymptotic language")
        for token in claim.get("supporting_equations") or []:
            if token not in known:
                err.append(f"claim {cid} unknown equation {token}")
        unresolved = claim.get("unresolved") or []
        if status in MACHINE_GREEN and unresolved:
            err.append(f"claim {cid} {status} lists unresolved items")
        compiled = bool(
            claim.get("lhs") and claim.get("rhs") and claim.get("symbols")
        )
        if status in MACHINE_GREEN and not compiled:
            err.append(
                f"claim {cid} {status} is a textual conclusion; "
                "related edges cannot stamp Exact on uncompiled prose"
            )
        if status in MACHINE_GREEN and compiled:
            related = supporting_edges(claim, edges)
            if not related:
                err.append(f"claim {cid} {status} without supporting edges")
            for edge in related:
                est = edge.get("status")
                if est not in MACHINE_GREEN | STRUCTURAL_STATUSES:
                    err.append(
                        f"claim {cid} {status} depends on {edge.get('id')} {est}"
                    )
                if est in MACHINE_GREEN:
                    err.extend(
                        _check_machine_green(edge, receipts.get(edge.get("id")), data)
                    )
            receipt = receipts.get(cid)
            err.extend(
                _check_machine_green(
                    {
                        "id": cid,
                        "lhs": claim.get("lhs"),
                        "rhs": claim.get("rhs"),
                        "symbols": claim.get("symbols"),
                        "functions": claim.get("functions") or [],
                        "assumptions": claim.get("assumptions") or [],
                        "domain": claim.get("domain") or "",
                        "kind": claim.get("kind") or "",
                        "from_eq": "",
                        "to_eq": "",
                        "status": status,
                    },
                    receipt,
                    data,
                )
            )

    for obligation in obligations:
        oid = obligation.get("id") or "?"
        if obligation.get("status") not in ALLOWED_STATUSES:
            err.append(f"obligation {oid} bad status {obligation.get('status')}")

    summary = data.get("summary")
    if isinstance(summary, dict):
        computed = compute_summary(data)
        if summary.get("overall_state") and summary.get("overall_state") not in ALLOWED_OVERALL:
            err.append(
                f"summary.overall_state {summary.get('overall_state')} is not a legal overall state"
            )
        for key in (
            "machine_certified_edges",
            "assumption_dependent_edges",
            "unresolved_load_bearing",
            "claim_count",
            "relations_reconstructed",
        ):
            if key in summary and summary[key] != computed[key]:
                err.append(
                    f"summary.{key} is {summary[key]}, computed {computed[key]}"
                )
    return err


def _check_machine_green(edge: dict, receipt: Any, data: dict) -> list[str]:
    eid = edge.get("id")
    err: list[str] = []
    if not (edge.get("lhs") and edge.get("rhs") and edge.get("symbols")):
        err.append(
            f"edge {eid} {edge.get('status')} without compiled lhs/rhs/symbols"
        )
        return err
    if not isinstance(receipt, dict):
        err.append(f"edge {eid} {edge.get('status')} without a bound receipt")
        return err
    if receipt.get("schema") not in {None, RECEIPT_SCHEMA}:
        err.append(f"edge {eid} receipt schema {receipt.get('schema')}")
    if receipt.get("edge_id") != eid:
        err.append(f"edge {eid} receipt edge_id is {receipt.get('edge_id')}")
    for key in ("lhs", "rhs"):
        if edge.get(key) != receipt.get(key):
            err.append(f"edge {eid} {key} does not match receipt")
    if (edge.get("symbols") or []) != (receipt.get("symbols") or []):
        err.append(f"edge {eid} symbols do not match receipt")
    if (edge.get("functions") or []) != (receipt.get("functions") or []):
        err.append(f"edge {eid} functions do not match receipt")
    if (edge.get("assumptions") or []) != (receipt.get("assumptions") or []):
        err.append(f"edge {eid} assumptions do not match receipt")
    if (edge.get("domain") or "") != (receipt.get("domain") or ""):
        err.append(f"edge {eid} domain does not match receipt")
    if (edge.get("kind") or "") != (receipt.get("kind") or ""):
        err.append(f"edge {eid} kind does not match receipt")
    if (edge.get("from_eq") or "") != (receipt.get("from_eq") or "") or (
        edge.get("to_eq") or ""
    ) != (receipt.get("to_eq") or ""):
        err.append(f"edge {eid} equation endpoints do not match receipt")
    from_h = equation_source_hash(data, str(edge.get("from_eq") or ""))
    to_h = equation_source_hash(data, str(edge.get("to_eq") or ""))
    if from_h and (receipt.get("from_source_hash") or "") != from_h:
        err.append(f"edge {eid} from_eq source no longer matches the receipt")
    if to_h and (receipt.get("to_source_hash") or "") != to_h:
        err.append(f"edge {eid} to_eq source no longer matches the receipt")
    stored = receipt.get("input_hash")
    expected = binding_hash(receipt)
    if not (isinstance(stored, str) and _HASH_RE.fullmatch(stored)):
        err.append(f"edge {eid} receipt missing input_hash")
    elif stored != expected:
        err.append(f"edge {eid} receipt input_hash does not bind current inputs")
    if receipt.get("verdict") != "ZERO":
        err.append(
            f"edge {eid} {edge.get('status')} but receipt verdict is {receipt.get('verdict')}"
        )
    if load_verify_equivalent() is None:
        err.append(
            f"edge {eid} {edge.get('status')} requires engine recomputation; engine missing"
        )
        return err
    recomputed = _recompute_verdict(
        {
            "lhs": edge["lhs"],
            "rhs": edge["rhs"],
            "symbols": edge["symbols"],
            "functions": edge.get("functions") or [],
            "assumptions": edge.get("assumptions") or [],
        }
    )
    if recomputed != "ZERO":
        err.append(f"edge {eid} recomputation is {recomputed}, not ZERO")
    return err


def status_from_verdict(
    verdict: str,
    *,
    assumptions: list,
    kind: str = "",
) -> str:
    kind_u = (kind or "").upper()
    if kind_u in {"STRUCTURAL", "DEFINITION", "BOOKKEEPING"}:
        return "STRUCTURAL"
    if kind_u in {"CITED_RULE"}:
        return "CITED_RULE"
    if verdict == "ZERO":
        return "EXACT_IF_ASSUMPTIONS" if assumptions else "EXACT"
    if verdict == "NONZERO":
        return "NONZERO_RESIDUAL"
    if verdict == "UNKNOWN":
        return "UNCERTIFIED"
    return "GAP"


def make_receipt(
    *,
    edge_id: str,
    lhs: str,
    rhs: str,
    assumptions: list,
    symbols: list,
    domain: str,
    kind: str,
    verdict: str,
    residual: str = "",
    counterexample: Any = None,
    functions: Any = None,
    from_eq: str = "",
    to_eq: str = "",
    from_source_hash: str = "",
    to_source_hash: str = "",
) -> dict:
    payload = {
        "schema": RECEIPT_SCHEMA,
        "edge_id": edge_id,
        "lhs": lhs,
        "rhs": rhs,
        "assumptions": assumptions or [],
        "symbols": symbols or [],
        "domain": domain or "",
        "kind": kind or "",
        "functions": functions or [],
        "from_eq": from_eq or "",
        "to_eq": to_eq or "",
        "from_source_hash": from_source_hash or "",
        "to_source_hash": to_source_hash or "",
        "verdict": verdict,
        "residual": residual,
        "counterexample": counterexample,
        "engine": engine_identity(),
        "issuer": CERTIFY_ISSUER,
    }
    payload["input_hash"] = binding_hash(payload)
    return payload
