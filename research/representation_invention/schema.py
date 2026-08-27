"""RepresentationHypothesisV2 — shared contract.

Parse is syntactic. Completeness (operators, reconstruction, obligations)
is a later D/C check. Aliases are PARSE_FAILURE and are never repaired.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

PARSE_FAILURE = "PARSE_FAILURE"
OK = "OK"
ABSTAIN = "ABSTAIN"

GID_RE = re.compile(r"^G\d{4}$")
ALIAS_RE = re.compile(
    r"^(S\d|C\d|O\d|G\d\(|branch_|generic|degenerate|diag|off)",
    re.I,
)

REPRESENTATION_TYPES = (
    "local_confluence",
    "divided_difference",
    "hermite_divided_difference",
    "derivative_family",
    "recurrence_family",
    "master_function",
    "generating_function",
    "invariant_basis",
    "tensor_generator",
    "other_explicit",
)

MEMBER_ROLES = (
    "generic",
    "degenerate",
    "instance",
    "repeated",
    "kernel",
    "other",
)

OPERATOR_KINDS = (
    "identity",
    "substitution",
    "permutation",
    "derivative",
    "shift",
    "limit",
    "newton_dd",
    "hermite_dd",
    "recurrence",
    "other",
)

OBLIGATION_KINDS = (
    "EQUALITY",
    "SUBSTITUTION",
    "PERMUTATION",
    "DERIVATIVE",
    "LIMIT",
    "NEWTON_DD",
    "HERMITE_DD",
    "CONFLUENCE",
    "RECURRENCE",
    "MASTER_INSTANCE",
    "BASIS_RECONSTRUCTION",
)

# P1 type names are historical. V2 does not accept them.
P1_TYPE_ALIASES = {
    "confluent_representation": "local_confluence",
}


def is_catalog_id(value: str) -> bool:
    return bool(GID_RE.fullmatch(value or ""))


def is_alias_id(value: str) -> bool:
    s = (value or "").strip()
    if not s:
        return False
    if is_catalog_id(s):
        return False
    return bool(ALIAS_RE.match(s)) or not is_catalog_id(s)


@dataclass
class NodeSpec:
    name: str
    expression: str
    multiplicity: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OperatorSpec:
    member_id: str
    kind: str
    args: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "member_id": self.member_id,
            "kind": self.kind,
            "args": dict(self.args),
        }


@dataclass
class ObligationDraft:
    """Proposer-facing obligation. Compiler types this; verifier does not."""

    kind: str
    member_ids: list[str] = field(default_factory=list)
    left: str = ""
    right: str = ""
    operator: str = ""
    expected: str = ""
    variables: dict[str, str] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    provenance: str = "proposer"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RepresentationHypothesisV2:
    representation_type: str
    member_ids: list[str]
    member_roles: dict[str, str] = field(default_factory=dict)
    latent_object: str = ""
    latent_variables: list[str] = field(default_factory=list)
    nodes: list[NodeSpec] = field(default_factory=list)
    operators: list[OperatorSpec] = field(default_factory=list)
    instance_maps: dict[str, Any] = field(default_factory=dict)
    reconstruction_rule: str = ""
    required_assumptions: list[str] = field(default_factory=list)
    proof_obligations: list[Any] = field(default_factory=list)
    scientific_rationale: str = ""
    confidence: float = 0.0
    parse_status: str = OK
    parse_error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "representation_type": self.representation_type,
            "member_ids": list(self.member_ids),
            "member_roles": dict(self.member_roles),
            "latent_object": self.latent_object,
            "latent_variables": list(self.latent_variables),
            "nodes": [n.to_dict() if isinstance(n, NodeSpec) else n for n in self.nodes],
            "operators": [
                o.to_dict() if isinstance(o, OperatorSpec) else o for o in self.operators
            ],
            "instance_maps": dict(self.instance_maps),
            "reconstruction_rule": self.reconstruction_rule,
            "required_assumptions": list(self.required_assumptions),
            "proof_obligations": [
                p.to_dict() if hasattr(p, "to_dict") else p for p in self.proof_obligations
            ],
            "scientific_rationale": self.scientific_rationale,
            "confidence": self.confidence,
            "parse_status": self.parse_status,
            "parse_error": self.parse_error,
        }


def _fail(
    rtype: str,
    error: str,
    *,
    member_ids: Optional[list[str]] = None,
    **kwargs: Any,
) -> RepresentationHypothesisV2:
    return RepresentationHypothesisV2(
        representation_type=rtype or "other_explicit",
        member_ids=list(member_ids or []),
        parse_status=PARSE_FAILURE,
        parse_error=error,
        **kwargs,
    )


def _parse_nodes(raw: Any) -> tuple[list[NodeSpec] | None, str | None]:
    if raw is None:
        return [], None
    if not isinstance(raw, list):
        return None, "nodes_not_list"
    out: list[NodeSpec] = []
    for item in raw:
        if not isinstance(item, dict):
            return None, "node_not_object"
        name = str(item.get("name") or "").strip()
        expr = str(item.get("expression") or item.get("expr") or "").strip()
        if not name:
            return None, "node_missing_name"
        try:
            mult = int(item.get("multiplicity", 1))
        except (TypeError, ValueError):
            return None, "node_multiplicity_not_int"
        if mult < 1:
            return None, "node_multiplicity_lt_1"
        out.append(NodeSpec(name=name, expression=expr, multiplicity=mult))
    return out, None


def _parse_operators(raw: Any) -> tuple[list[OperatorSpec] | None, str | None]:
    if raw is None:
        return [], None
    if not isinstance(raw, list):
        return None, "operators_not_list"
    out: list[OperatorSpec] = []
    for item in raw:
        if not isinstance(item, dict):
            return None, "operator_not_object"
        mid = str(item.get("member_id") or item.get("member") or "").strip()
        kind = str(item.get("kind") or item.get("O") or "").strip()
        if not mid:
            return None, "operator_missing_member_id"
        if is_alias_id(mid) or not is_catalog_id(mid):
            return None, f"alias_or_bad_id:{mid}"
        if kind not in OPERATOR_KINDS:
            return None, f"unknown_operator_kind:{kind}"
        args = item.get("args") if isinstance(item.get("args"), dict) else {}
        out.append(OperatorSpec(member_id=mid, kind=kind, args=dict(args)))
    return out, None


def _parse_obligations(raw: Any) -> tuple[list[Any] | None, str | None]:
    if raw is None:
        return [], None
    if not isinstance(raw, list):
        return None, "proof_obligations_not_list"
    out: list[Any] = []
    for item in raw:
        if isinstance(item, str):
            out.append(item)
            continue
        if not isinstance(item, dict):
            return None, "obligation_not_object_or_string"
        kind = str(item.get("kind") or "").strip()
        if kind and kind not in OBLIGATION_KINDS:
            return None, f"unknown_obligation_kind:{kind}"
        mids_raw = item.get("member_ids") or []
        if item.get("member_id"):
            mids_raw = list(mids_raw) + [item.get("member_id")]
        mids: list[str] = []
        for m in mids_raw:
            s = str(m).strip()
            if not s:
                continue
            if is_alias_id(s) or not is_catalog_id(s):
                return None, f"alias_or_bad_id:{s}"
            mids.append(s)
        out.append(
            ObligationDraft(
                kind=kind or "EQUALITY",
                member_ids=mids,
                left=str(item.get("left") or ""),
                right=str(item.get("right") or ""),
                operator=str(item.get("operator") or ""),
                expected=str(item.get("expected") or ""),
                variables=dict(item.get("variables") or {})
                if isinstance(item.get("variables"), dict)
                else {},
                assumptions=[str(x) for x in (item.get("assumptions") or [])],
                provenance=str(item.get("provenance") or "proposer"),
            )
        )
    return out, None


def parse_hypothesis_v2(
    raw: dict,
    catalog: set[str],
) -> RepresentationHypothesisV2:
    """Syntactic parse. Does not compile, verify, or repair aliases."""
    if not isinstance(raw, dict):
        return _fail("other_explicit", "not_object")

    rtype = raw.get("representation_type")
    if rtype in P1_TYPE_ALIASES:
        return _fail(
            "other_explicit",
            f"p1_type_not_accepted:{rtype}",
        )
    if rtype not in REPRESENTATION_TYPES:
        return _fail("other_explicit", f"unknown_type:{rtype}")

    mids_raw = raw.get("member_ids")
    if not isinstance(mids_raw, list) or not mids_raw:
        return _fail(rtype, "member_ids_required")

    member_ids: list[str] = []
    for m in mids_raw:
        s = str(m).strip()
        if is_alias_id(s) or not is_catalog_id(s):
            return _fail(rtype, f"alias_or_bad_id:{s}", member_ids=member_ids)
        if s not in catalog:
            return _fail(rtype, f"id_not_in_catalog:{s}", member_ids=member_ids)
        if s not in member_ids:
            member_ids.append(s)

    roles_raw = raw.get("member_roles") or {}
    if not isinstance(roles_raw, dict):
        return _fail(rtype, "member_roles_not_object", member_ids=member_ids)
    member_roles: dict[str, str] = {}
    for k, v in roles_raw.items():
        ks = str(k).strip()
        vs = str(v).strip() or "other"
        if is_alias_id(ks) or not is_catalog_id(ks):
            return _fail(rtype, f"alias_or_bad_id:{ks}", member_ids=member_ids)
        if ks not in catalog:
            return _fail(rtype, f"id_not_in_catalog:{ks}", member_ids=member_ids)
        if ks not in member_ids:
            return _fail(rtype, f"role_id_not_in_member_ids:{ks}", member_ids=member_ids)
        if vs not in MEMBER_ROLES:
            return _fail(rtype, f"unknown_role:{vs}", member_ids=member_ids)
        member_roles[ks] = vs

    latent = raw.get("latent_object")
    if not isinstance(latent, str) or not latent.strip():
        return _fail(rtype, "latent_object_empty", member_ids=member_ids)

    conf = raw.get("confidence")
    try:
        cf = float(conf)
    except (TypeError, ValueError):
        return _fail(rtype, "confidence_not_number", member_ids=member_ids)
    if not 0.0 <= cf <= 1.0:
        return _fail(rtype, "confidence_out_of_range", member_ids=member_ids)

    nodes, err = _parse_nodes(raw.get("nodes"))
    if err:
        return _fail(rtype, err, member_ids=member_ids)

    operators, err = _parse_operators(raw.get("operators"))
    if err:
        return _fail(rtype, err, member_ids=member_ids)
    for op in operators or []:
        if op.member_id not in member_ids:
            return _fail(
                rtype,
                f"operator_member_not_in_member_ids:{op.member_id}",
                member_ids=member_ids,
            )

    obligations, err = _parse_obligations(raw.get("proof_obligations"))
    if err:
        return _fail(rtype, err, member_ids=member_ids)

    lv = raw.get("latent_variables") or []
    if lv is None:
        lv = []
    if not isinstance(lv, list):
        return _fail(rtype, "latent_variables_not_list", member_ids=member_ids)

    imap = raw.get("instance_maps") or {}
    if not isinstance(imap, dict):
        return _fail(rtype, "instance_maps_not_object", member_ids=member_ids)
    for k in imap:
        ks = str(k)
        if is_catalog_id(ks) and ks not in member_ids:
            return _fail(
                rtype,
                f"instance_map_id_not_in_member_ids:{ks}",
                member_ids=member_ids,
            )
        if is_alias_id(ks):
            return _fail(rtype, f"alias_or_bad_id:{ks}", member_ids=member_ids)

    assumptions = raw.get("required_assumptions") or []
    if not isinstance(assumptions, list):
        return _fail(rtype, "required_assumptions_not_list", member_ids=member_ids)

    return RepresentationHypothesisV2(
        representation_type=rtype,
        member_ids=member_ids,
        member_roles=member_roles,
        latent_object=str(latent).strip(),
        latent_variables=[str(x) for x in lv],
        nodes=nodes or [],
        operators=operators or [],
        instance_maps=dict(imap),
        reconstruction_rule=str(raw.get("reconstruction_rule") or ""),
        required_assumptions=[str(x) for x in assumptions],
        proof_obligations=obligations or [],
        scientific_rationale=str(
            raw.get("scientific_rationale") or raw.get("rationale") or ""
        ),
        confidence=cf,
        parse_status=OK,
        parse_error=None,
    )


def parse_document_v2(obj: dict, catalog: set[str]) -> dict[str, Any]:
    """Parse an LLM JSON envelope. Does not call the model."""
    if not isinstance(obj, dict):
        return {
            "parse_status": PARSE_FAILURE,
            "parse_error": "not_object",
            "hypotheses": [],
            "abstain": False,
        }
    if obj.get("abstain") and not obj.get("hypotheses"):
        return {
            "parse_status": ABSTAIN,
            "hypotheses": [],
            "abstain": True,
            "abstain_reason": str(obj.get("abstain_reason") or "abstain"),
        }
    raw_h = obj.get("hypotheses")
    if not isinstance(raw_h, list):
        return {
            "parse_status": PARSE_FAILURE,
            "parse_error": "hypotheses_not_list",
            "hypotheses": [],
        }
    hyps = [
        parse_hypothesis_v2(h, catalog)
        if isinstance(h, dict)
        else _fail("other_explicit", "not_object")
        for h in raw_h
    ]
    ok = [h for h in hyps if h.parse_status == OK]
    if ok and all(h.parse_status == OK for h in hyps):
        status = OK
    elif ok:
        status = OK
    else:
        status = PARSE_FAILURE
    return {
        "parse_status": status,
        "hypotheses": hyps,
        "abstain": bool(obj.get("abstain")) and not ok,
        "n_ok": len(ok),
        "n_parse_failure": len(hyps) - len(ok),
    }
