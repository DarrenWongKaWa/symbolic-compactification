"""Compile RepresentationHypothesisV2 into experimental obligations.

A reconstruction that cannot be built is COMPILE_FAILURE, never UNKNOWN.
This module does not assign ZERO / NONZERO / UNKNOWN.
"""
from __future__ import annotations

from typing import Any, Optional

from research.llm_abstraction.constructor import (
    _diff_repeat,
    _swap_applied,
    instantiate,
    parse_flex,
    symbolic_core,
)
from research.representation_invention.obligations.constructors import (
    USED_LOCAL_DD_FALLBACK,
    eval_F,
    hermite_nodes,
    newton_first,
    parse_latent,
    split_piecewise,
)
from research.representation_invention.obligations.schema import (
    BASIS_RECONSTRUCTION,
    COMPILE_FAILURE,
    COMPILE_OK,
    CONFLUENCE,
    DERIVATIVE,
    EQUALITY,
    HERMITE_DD,
    KINDS,
    LIMIT,
    MASTER_INSTANCE,
    NEWTON_DD,
    PERMUTATION,
    RECURRENCE,
    SUBSTITUTION,
    CompileResult,
    Obligation,
)
from research.representation_invention.schema import (
    OK,
    ObligationDraft,
    OperatorSpec,
    RepresentationHypothesisV2,
)

_TYPE_KIND = {
    "local_confluence": CONFLUENCE,
    "divided_difference": NEWTON_DD,
    "hermite_divided_difference": HERMITE_DD,
    "derivative_family": DERIVATIVE,
    "recurrence_family": RECURRENCE,
    "master_function": MASTER_INSTANCE,
    "generating_function": MASTER_INSTANCE,
    "invariant_basis": BASIS_RECONSTRUCTION,
    "tensor_generator": BASIS_RECONSTRUCTION,
    "other_explicit": EQUALITY,
}

_OP_KIND = {
    "identity": EQUALITY,
    "substitution": SUBSTITUTION,
    "permutation": PERMUTATION,
    "derivative": DERIVATIVE,
    "shift": RECURRENCE,
    "limit": LIMIT,
    "newton_dd": NEWTON_DD,
    "hermite_dd": HERMITE_DD,
    "recurrence": RECURRENCE,
    "other": EQUALITY,
}

_THETA_SKIP = {"order", "n_diff", "times", "nodes", "basis", "coefficients", "rhs"}


def compile_hypothesis(
    h: RepresentationHypothesisV2,
    catalog: dict[str, str],
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> CompileResult:
    symbols = list(symbols or [])
    functions = list(functions or [])
    cat = {str(k): str(v) for k, v in (catalog or {}).items()}
    notes: list[str] = []
    if USED_LOCAL_DD_FALLBACK:
        notes.append("dd_local_fallback")

    rtype = getattr(h, "representation_type", "") or ""
    latent = getattr(h, "latent_object", "") or ""
    core = symbolic_core(latent)

    if h is None:
        obl = _failure(
            EQUALITY, "null_hypothesis",
            latent=latent, assumptions=[],
        )
        return CompileResult([obl], 0, 1, rtype, rtype, core, notes)

    if getattr(h, "parse_status", OK) != OK:
        obl = _failure(
            _kind_from_type(rtype),
            f"hypothesis_parse_failure:{getattr(h, 'parse_error', None) or 'parse_failure'}",
            member_ids=list(getattr(h, "member_ids", None) or []),
            latent=latent,
            assumptions=list(getattr(h, "required_assumptions", None) or []),
        )
        return CompileResult([obl], 0, 1, rtype, rtype, core, notes)

    drafts = _collect_drafts(h)
    if not drafts:
        obl = _failure(
            _kind_from_type(rtype),
            "reconstruction_cannot_be_built",
            member_ids=list(h.member_ids or []),
            latent=latent,
            assumptions=list(h.required_assumptions or []),
        )
        return CompileResult([obl], 0, 1, rtype, rtype, core, notes)

    out = [_compile_draft(h, d, cat, symbols, functions) for d in drafts]
    n_ok = sum(1 for o in out if o.compile_status == COMPILE_OK)
    n_fail = len(out) - n_ok
    return CompileResult(
        obligations=out,
        n_ok=n_ok,
        n_fail=n_fail,
        representation_type=rtype,
        hypothesis_type=rtype,
        latent_core=core,
        notes=notes,
    )


def _kind_from_type(rtype: str) -> str:
    return _TYPE_KIND.get(rtype, EQUALITY)


def _op_attr(op: Any, name: str, default: Any = None) -> Any:
    if isinstance(op, OperatorSpec):
        return getattr(op, name, default)
    if isinstance(op, dict):
        return op.get(name, default)
    return default


def _as_draft(raw: Any) -> Optional[ObligationDraft]:
    if isinstance(raw, ObligationDraft):
        return raw
    if isinstance(raw, dict) and (raw.get("kind") or raw.get("member_ids")):
        mids = [str(x) for x in (raw.get("member_ids") or [])]
        if raw.get("member_id"):
            mids.append(str(raw.get("member_id")))
        return ObligationDraft(
            kind=str(raw.get("kind") or ""),
            member_ids=mids,
            left=str(raw.get("left") or ""),
            right=str(raw.get("right") or ""),
            operator=str(raw.get("operator") or ""),
            expected=str(raw.get("expected") or ""),
            variables=dict(raw.get("variables") or {})
            if isinstance(raw.get("variables"), dict) else {},
            assumptions=[str(x) for x in (raw.get("assumptions") or [])],
            provenance=str(raw.get("provenance") or "proposer"),
        )
    return None


def _collect_drafts(h: RepresentationHypothesisV2) -> list[ObligationDraft]:
    typed: list[ObligationDraft] = []
    for p in h.proof_obligations or []:
        d = _as_draft(p)
        if d is not None and (d.kind or d.member_ids):
            typed.append(d)
    if typed:
        return typed
    ops = list(h.operators or [])
    if ops:
        out: list[ObligationDraft] = []
        for op in ops:
            mid = str(_op_attr(op, "member_id") or "")
            okind = str(_op_attr(op, "kind") or "")
            args = _op_attr(op, "args") or {}
            kind = _OP_KIND.get(okind, _kind_from_type(h.representation_type))
            if okind == "limit" and h.representation_type == "local_confluence":
                kind = CONFLUENCE
            variables = {
                str(k): str(v)
                for k, v in (args.items() if isinstance(args, dict) else [])
                if not isinstance(v, (list, dict))
            }
            mids = [mid] if mid else list(h.member_ids or [])
            if kind in {CONFLUENCE, LIMIT} and len(h.member_ids or []) >= 2:
                mids = _role_pair(h) or list(h.member_ids)[:2]
            out.append(ObligationDraft(
                kind=kind,
                member_ids=mids,
                operator=okind or kind.lower(),
                expected="equal",
                variables=variables,
                provenance="compiler:from_operator",
            ))
        return out
    return _synthesize(h)


def _role_pair(h: RepresentationHypothesisV2) -> list[str]:
    roles = h.member_roles or {}
    gen = [m for m, r in roles.items() if r == "generic" and m in h.member_ids]
    deg = [
        m for m, r in roles.items()
        if r in {"degenerate", "repeated"} and m in h.member_ids
    ]
    if gen and deg:
        return [gen[0], deg[0]]
    if len(h.member_ids) >= 2:
        return list(h.member_ids[:2])
    return list(h.member_ids or [])


def _synthesize(h: RepresentationHypothesisV2) -> list[ObligationDraft]:
    kind = _kind_from_type(h.representation_type)
    if kind in {CONFLUENCE, LIMIT}:
        mids = _role_pair(h)
        return [ObligationDraft(
            kind=CONFLUENCE if len(mids) >= 2 or h.representation_type == "local_confluence" else LIMIT,
            member_ids=mids,
            operator="limit",
            expected="limit_equal",
            provenance="compiler:from_type",
        )]
    if kind == MASTER_INSTANCE:
        return [
            ObligationDraft(
                kind=MASTER_INSTANCE,
                member_ids=[mid],
                operator="identity",
                expected="equal",
                provenance="compiler:from_type",
            )
            for mid in (h.member_ids or [])
        ]
    mids = list(h.member_ids or [])
    if not mids:
        return []
    return [ObligationDraft(
        kind=kind,
        member_ids=mids[:1] if kind not in {CONFLUENCE} else mids[:2],
        operator=kind.lower(),
        expected="equal",
        provenance="compiler:from_type",
    )]


def _failure(
    kind: str,
    error: str,
    *,
    member_ids: Optional[list[str]] = None,
    exact: Optional[dict[str, str]] = None,
    latent: str = "",
    assumptions: Optional[list[str]] = None,
    operator: str = "",
    variables: Optional[dict[str, str]] = None,
    provenance: str = "compiler",
) -> Obligation:
    k = kind if kind in KINDS else EQUALITY
    return Obligation(
        kind=k,
        member_ids=list(member_ids or []),
        exact_expressions=dict(exact or {}),
        variables=dict(variables or {}),
        assumptions=list(assumptions or []),
        operator=operator or k.lower(),
        expected_relation="equal",
        provenance=provenance,
        compile_status=COMPILE_FAILURE,
        compile_error=error,
        latent=latent,
        left=(next(iter((exact or {}).values()), "") if exact else ""),
    )


def _imap(h: RepresentationHypothesisV2, member_id: str) -> dict[str, Any]:
    raw = (h.instance_maps or {}).get(member_id)
    return raw if isinstance(raw, dict) else {}


def _first_op(h: RepresentationHypothesisV2, member_id: str) -> Optional[Any]:
    for op in h.operators or []:
        if str(_op_attr(op, "member_id") or "") == member_id:
            return op
    return (h.operators or [None])[0]


def _op_args(h: RepresentationHypothesisV2, member_id: str) -> dict[str, Any]:
    op = _first_op(h, member_id)
    args = _op_attr(op, "args") if op is not None else None
    return dict(args) if isinstance(args, dict) else {}


def _theta_for(h: RepresentationHypothesisV2, member_id: str) -> dict[str, str]:
    imap = _imap(h, member_id)
    th = imap.get("theta") or imap.get("map") or {}
    if isinstance(th, dict) and th:
        return {
            str(k): str(v) for k, v in th.items()
            if k not in _THETA_SKIP and not isinstance(v, (list, dict))
        }
    args = _op_args(h, member_id)
    return {
        str(k): str(v) for k, v in args.items()
        if k not in _THETA_SKIP and not isinstance(v, (list, dict))
    }


def _as_int(value: Any, default: int = 1) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _node_specs(h: RepresentationHypothesisV2) -> list[tuple[str, str, int]]:
    out: list[tuple[str, str, int]] = []
    for n in h.nodes or []:
        if hasattr(n, "name"):
            name = str(n.name)
            expr = str(getattr(n, "expression", "") or name)
            mult = int(getattr(n, "multiplicity", 1) or 1)
        elif isinstance(n, dict):
            name = str(n.get("name") or "")
            expr = str(n.get("expression") or n.get("expr") or name)
            mult = _as_int(n.get("multiplicity", 1), 1)
        else:
            continue
        if name:
            out.append((name, expr, max(1, mult)))
    return out


def _requested_node_names(
    h: RepresentationHypothesisV2,
    member_id: str,
    draft: ObligationDraft,
) -> Optional[list[str]]:
    args = _op_args(h, member_id)
    imap = _imap(h, member_id)
    for src in (
        args.get("nodes"),
        imap.get("nodes"),
        (imap.get("theta") or {}).get("nodes") if isinstance(imap.get("theta"), dict) else None,
        draft.variables.get("nodes") if draft.variables else None,
    ):
        if isinstance(src, list) and src:
            return [str(x) for x in src]
        if isinstance(src, str) and src:
            return [p.strip() for p in src.split(",") if p.strip()]
    return None


def _nodes_for(
    h: RepresentationHypothesisV2,
    member_id: str,
    draft: ObligationDraft,
) -> list[str]:
    specs = _node_specs(h)
    by_name = {name: (expr, mult) for name, expr, mult in specs}
    requested = _requested_node_names(h, member_id, draft)
    if requested:
        seq: list[str] = []
        unique_req = list(dict.fromkeys(requested))
        expand_specs = (
            len(requested) == len(unique_req)
            and all(r in by_name for r in requested)
        )
        for r in requested:
            if r in by_name:
                expr, mult = by_name[r]
                times = mult if expand_specs else 1
                seq.extend([expr] * times)
            else:
                seq.append(r)
        return seq
    seq = []
    for _name, expr, mult in specs:
        seq.extend([expr] * mult)
    return seq


def _limit_var_point(
    h: RepresentationHypothesisV2,
    member_id: str,
    draft: ObligationDraft,
) -> tuple[str, str]:
    var = (
        draft.variables.get("var")
        or draft.variables.get("from")
        or ""
    )
    to = (
        draft.variables.get("to")
        or draft.variables.get("point")
        or ""
    )
    args = _op_args(h, member_id)
    var = str(var or args.get("var") or args.get("from") or "")
    to = str(to or args.get("to") or args.get("point") or "")
    if (not var or not to) and draft.variables:
        var = var or str(draft.variables.get("var") or "")
        to = to or str(draft.variables.get("to") or "")
    if not var or not to:
        nodes = _nodes_for(h, member_id, draft)
        if len(nodes) >= 2:
            var = var or nodes[0]
            to = to or nodes[1]
    return var, to


def _assumptions(h: RepresentationHypothesisV2, draft: ObligationDraft) -> list[str]:
    out = [str(x) for x in (h.required_assumptions or [])]
    out.extend(str(x) for x in (draft.assumptions or []))
    return out


def _ok_base(
    kind: str,
    h: RepresentationHypothesisV2,
    draft: ObligationDraft,
    mids: list[str],
    exact: dict[str, str],
    **kwargs: Any,
) -> Obligation:
    op = draft.operator or kind.lower()
    expected = kwargs.pop("expected_relation", "equal")
    if draft.expected in {"equal", "limit_equal", "equal_zero", "dd_equal"}:
        expected = draft.expected
    prov = draft.provenance or f"compiler:{kind.lower()}"
    variables = dict(draft.variables or {})
    variables.update(kwargs.pop("variables", {}) or {})
    return Obligation(
        kind=kind,
        member_ids=mids,
        exact_expressions=exact,
        variables=variables,
        assumptions=_assumptions(h, draft),
        operator=op,
        expected_relation=expected,
        provenance=prov,
        compile_status=COMPILE_OK,
        compile_error=None,
        latent=h.latent_object or "",
        theta=kwargs.pop("theta", {}),
        **kwargs,
    )


def _compile_draft(
    h: RepresentationHypothesisV2,
    draft: ObligationDraft,
    catalog: dict[str, str],
    symbols: list,
    functions: list,
) -> Obligation:
    kind = draft.kind or _kind_from_type(h.representation_type)
    mids = list(draft.member_ids or [])
    if not mids:
        mids = list(h.member_ids or [])
    if kind not in KINDS:
        return _failure(
            EQUALITY, f"unknown_kind:{kind}",
            member_ids=mids, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft), provenance=draft.provenance,
        )
    missing = [m for m in mids if m not in catalog or not str(catalog.get(m, "")).strip()]
    if missing:
        return _failure(
            kind, f"member_not_in_catalog:{missing[0]}",
            member_ids=mids, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
            operator=draft.operator,
            provenance=draft.provenance,
        )
    exact = {m: catalog[m] for m in mids}
    for mid, text in exact.items():
        if parse_flex(text, symbols, functions) is None:
            return _failure(
                kind, f"unparseable_member:{mid}",
                member_ids=mids, exact=exact, latent=h.latent_object or "",
                assumptions=_assumptions(h, draft),
                operator=draft.operator, provenance=draft.provenance,
            )
    builders = {
        NEWTON_DD: _build_newton,
        HERMITE_DD: _build_hermite,
        CONFLUENCE: _build_confluence,
        LIMIT: _build_limit,
        DERIVATIVE: _build_derivative,
        SUBSTITUTION: _build_substitution,
        PERMUTATION: _build_permutation,
        EQUALITY: _build_equality,
        RECURRENCE: _build_recurrence,
        MASTER_INSTANCE: _build_master,
        BASIS_RECONSTRUCTION: _build_basis,
    }
    return builders[kind](h, draft, mids, exact, symbols, functions)


def _need_F(
    h: RepresentationHypothesisV2,
    kind: str,
    mids: list[str],
    exact: dict[str, str],
    draft: ObligationDraft,
    symbols: list,
    functions: list,
) -> tuple[Optional[Any], Optional[Any], Optional[Obligation]]:
    F, z, _zname = parse_latent(
        h.latent_object or "", h.latent_variables, symbols, functions,
    )
    if F is None:
        return None, None, _failure(
            kind, "unparseable_latent",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
            operator=draft.operator, provenance=draft.provenance,
        )
    return F, z, None


def _build_newton(
    h, draft, mids, exact, symbols, functions,
) -> Obligation:
    F, z, err = _need_F(h, NEWTON_DD, mids, exact, draft, symbols, functions)
    if err is not None:
        return err
    mid = mids[0]
    nodes = _nodes_for(h, mid, draft)
    if len(nodes) < 2:
        return _failure(
            NEWTON_DD, "reconstruction_cannot_be_built:need_two_nodes",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft), operator=draft.operator or "newton_dd",
            provenance=draft.provenance,
        )
    x = parse_flex(nodes[0], symbols, functions)
    y = parse_flex(nodes[1], symbols, functions)
    if x is None or y is None or z is None:
        return _failure(
            NEWTON_DD, "reconstruction_cannot_be_built:unparseable_nodes",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft), operator=draft.operator or "newton_dd",
            provenance=draft.provenance, variables={"x": nodes[0], "y": nodes[1]},
        )
    cand = newton_first(F, z, x, y)
    left = exact[mid]
    return _ok_base(
        NEWTON_DD, h, draft, mids, exact,
        left=left,
        right=str(cand),
        reconstruction=str(cand),
        nodes=nodes[:2],
        node_multiplicities=[1, 1],
        theta=_theta_for(h, mid),
        variables={"x": nodes[0], "y": nodes[1], "z": z.name},
        expected_relation="equal",
    )


def _build_hermite(
    h, draft, mids, exact, symbols, functions,
) -> Obligation:
    F, z, err = _need_F(h, HERMITE_DD, mids, exact, draft, symbols, functions)
    if err is not None:
        return err
    mid = mids[0]
    nodes = _nodes_for(h, mid, draft)
    if len(nodes) < 2:
        return _failure(
            HERMITE_DD, "reconstruction_cannot_be_built:need_repeated_nodes",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft), operator=draft.operator or "hermite_dd",
            provenance=draft.provenance,
        )
    parsed = [parse_flex(n, symbols, functions) for n in nodes]
    if z is None or any(p is None for p in parsed):
        return _failure(
            HERMITE_DD, "reconstruction_cannot_be_built:unparseable_nodes",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft), operator=draft.operator or "hermite_dd",
            provenance=draft.provenance,
        )
    cand = hermite_nodes(F, z, parsed)
    return _ok_base(
        HERMITE_DD, h, draft, mids, exact,
        left=exact[mid],
        right=str(cand),
        reconstruction=str(cand),
        nodes=list(nodes),
        node_multiplicities=[1] * len(nodes),
        theta=_theta_for(h, mid),
        variables={"z": z.name, "nodes": ",".join(nodes)},
        expected_relation="equal",
    )


def _build_confluence(
    h, draft, mids, exact, symbols, functions, kind: str = CONFLUENCE,
) -> Obligation:
    generic_text = ""
    deg_text = ""
    used_ids = list(mids)
    if len(mids) >= 2:
        pair = _role_pair(h)
        if pair and pair[0] in exact and pair[1] in exact:
            used_ids = pair
        generic_text = exact[used_ids[0]]
        deg_text = exact[used_ids[1]]
        ge = parse_flex(generic_text, symbols, functions)
        if ge is not None and split_piecewise(ge)[0] is not None:
            g, d = split_piecewise(ge)
            generic_text, deg_text = str(g), str(d) if d is not None else deg_text
    elif len(mids) == 1:
        e = parse_flex(exact[mids[0]], symbols, functions)
        g, d = split_piecewise(e) if e is not None else (None, None)
        if g is None or d is None:
            return _failure(
                kind, "reconstruction_cannot_be_built:need_generic_and_degenerate",
                member_ids=mids, exact=exact, latent=h.latent_object or "",
                assumptions=_assumptions(h, draft), operator=draft.operator or "limit",
                provenance=draft.provenance,
            )
        generic_text, deg_text = str(g), str(d)
    else:
        return _failure(
            kind, "reconstruction_cannot_be_built:need_generic_and_degenerate",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
        )
    var, to = _limit_var_point(h, used_ids[0], draft)
    if not var or not to:
        return _failure(
            kind, "limit_var_or_point_missing",
            member_ids=used_ids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft), operator=draft.operator or "limit",
            provenance=draft.provenance,
        )
    if parse_flex(var, symbols, functions) is None or parse_flex(to, symbols, functions) is None:
        return _failure(
            kind, "limit_var_or_point_unparseable",
            member_ids=used_ids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft), operator=draft.operator or "limit",
            provenance=draft.provenance, variables={"var": var, "to": to},
        )
    return _ok_base(
        kind, h, draft, used_ids, exact,
        left=generic_text,
        right=deg_text,
        reconstruction=f"limit({generic_text}, {var}, {to})",
        var=var,
        to=to,
        nodes=[var, to],
        theta=_theta_for(h, used_ids[0]),
        variables={"var": var, "to": to},
        expected_relation="limit_equal",
    )


def _build_limit(
    h, draft, mids, exact, symbols, functions,
) -> Obligation:
    if len(mids) >= 2:
        return _build_confluence(h, draft, mids, exact, symbols, functions, kind=LIMIT)
    mid = mids[0]
    var, to = _limit_var_point(h, mid, draft)
    if not var or not to:
        return _failure(
            LIMIT, "limit_var_or_point_missing",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft), operator=draft.operator or "limit",
            provenance=draft.provenance,
        )
    if parse_flex(var, symbols, functions) is None or parse_flex(to, symbols, functions) is None:
        return _failure(
            LIMIT, "limit_var_or_point_unparseable",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
            operator=draft.operator or "limit", provenance=draft.provenance,
        )
    args = _op_args(h, mid)
    expected = (
        draft.right
        or str(args.get("value") or args.get("equals") or args.get("expected") or "")
        or (exact[mids[1]] if len(mids) > 1 else "")
    )
    if not expected:
        nodes = _nodes_for(h, mid, draft)
        # limit of member vs reconstruction from F at the point, if available
        F, z, err = _need_F(h, LIMIT, mids, exact, draft, symbols, functions)
        if err is None and F is not None and z is not None:
            pt = parse_flex(to, symbols, functions)
            if pt is not None:
                expected = str(eval_F(F, z, pt))
        if not expected and len(nodes) >= 2:
            return _failure(
                LIMIT, "reconstruction_cannot_be_built:limit_target_missing",
                member_ids=mids, exact=exact, latent=h.latent_object or "",
                assumptions=_assumptions(h, draft),
            )
        if not expected:
            return _failure(
                LIMIT, "reconstruction_cannot_be_built:limit_target_missing",
                member_ids=mids, exact=exact, latent=h.latent_object or "",
                assumptions=_assumptions(h, draft),
            )
    return _ok_base(
        LIMIT, h, draft, mids, exact,
        left=exact[mid],
        right=str(expected),
        reconstruction=f"limit({exact[mid]}, {var}, {to})",
        var=var,
        to=to,
        nodes=[var, to],
        theta=_theta_for(h, mid),
        variables={"var": var, "to": to},
        expected_relation="limit_equal",
    )


def _build_derivative(
    h, draft, mids, exact, symbols, functions,
) -> Obligation:
    F, z, err = _need_F(h, DERIVATIVE, mids, exact, draft, symbols, functions)
    if err is not None:
        return err
    mid = mids[0]
    args = _op_args(h, mid)
    order = _as_int(
        draft.variables.get("order")
        or args.get("order")
        or _theta_for(h, mid).get("order")
        or 1,
        1,
    )
    var_name = str(
        draft.variables.get("var")
        or args.get("var")
        or (z.name if z is not None else "")
    )
    if z is None and not var_name:
        return _failure(
            DERIVATIVE, "reconstruction_cannot_be_built:no_diff_variable",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
        )
    var = z if z is not None and (not var_name or z.name == var_name) else None
    if var is None and var_name:
        var = next((s for s in F.free_symbols if s.name == var_name), None)
    if var is None:
        return _failure(
            DERIVATIVE, "reconstruction_cannot_be_built:no_diff_variable",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
        )
    d = _diff_repeat(F, var, max(1, order))
    theta = _theta_for(h, mid)
    inst = instantiate(d, theta, symbols, functions)
    if inst is None:
        return _failure(
            DERIVATIVE, "reconstruction_cannot_be_built:instantiate_failed",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
        )
    return _ok_base(
        DERIVATIVE, h, draft, mids, exact,
        left=exact[mid],
        right=str(inst),
        reconstruction=str(inst),
        order=max(1, order),
        var=var.name,
        theta=theta,
        variables={"var": var.name, "order": str(max(1, order))},
        expected_relation="equal",
    )


def _build_substitution(
    h, draft, mids, exact, symbols, functions,
) -> Obligation:
    F, z, err = _need_F(h, SUBSTITUTION, mids, exact, draft, symbols, functions)
    if err is not None:
        return err
    mid = mids[0]
    theta = _theta_for(h, mid)
    inst = instantiate(F, theta, symbols, functions)
    if inst is None:
        return _failure(
            SUBSTITUTION, "reconstruction_cannot_be_built:instantiate_failed",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
        )
    return _ok_base(
        SUBSTITUTION, h, draft, mids, exact,
        left=exact[mid],
        right=str(inst),
        reconstruction=str(inst),
        theta=theta,
        variables=dict(theta),
        expected_relation="equal",
    )


def _build_permutation(
    h, draft, mids, exact, symbols, functions,
) -> Obligation:
    F, z, err = _need_F(h, PERMUTATION, mids, exact, draft, symbols, functions)
    if err is not None:
        return err
    mid = mids[0]
    theta = _theta_for(h, mid)
    inst = instantiate(F, theta, symbols, functions)
    if inst is None:
        return _failure(
            PERMUTATION, "reconstruction_cannot_be_built:instantiate_failed",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
        )
    cand = _swap_applied(inst)
    return _ok_base(
        PERMUTATION, h, draft, mids, exact,
        left=exact[mid],
        right=str(cand),
        reconstruction=str(cand),
        theta=theta,
        variables=dict(theta),
        expected_relation="equal",
    )


def _build_equality(
    h, draft, mids, exact, symbols, functions,
) -> Obligation:
    if len(mids) >= 2:
        return _ok_base(
            EQUALITY, h, draft, mids[:2], exact,
            left=exact[mids[0]],
            right=exact[mids[1]],
            reconstruction=exact[mids[1]],
            theta=_theta_for(h, mids[0]),
            expected_relation="equal",
        )
    F, z, err = _need_F(h, EQUALITY, mids, exact, draft, symbols, functions)
    if err is not None:
        return err
    mid = mids[0]
    theta = _theta_for(h, mid)
    inst = instantiate(F, theta, symbols, functions)
    if inst is None:
        return _failure(
            EQUALITY, "reconstruction_cannot_be_built:instantiate_failed",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
        )
    return _ok_base(
        EQUALITY, h, draft, mids, exact,
        left=exact[mid],
        right=str(inst),
        reconstruction=str(inst),
        theta=theta,
        expected_relation="equal",
    )


def _build_recurrence(
    h, draft, mids, exact, symbols, functions,
) -> Obligation:
    F, z, err = _need_F(h, RECURRENCE, mids, exact, draft, symbols, functions)
    if err is not None:
        return err
    mid = mids[0] if mids else ""
    args = _op_args(h, mid) if mid else {}
    rhs = str(
        draft.variables.get("rhs")
        or args.get("rhs")
        or args.get("delta")
        or ""
    )
    shift_var = str(
        draft.variables.get("shift")
        or draft.variables.get("var")
        or args.get("shift")
        or args.get("variable")
        or args.get("var")
        or (z.name if z is not None else "")
    )
    step = str(
        draft.variables.get("step")
        or args.get("step")
        or "1"
    )
    if not rhs:
        return _failure(
            RECURRENCE, "reconstruction_cannot_be_built:recurrence_rhs_missing",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
            operator=draft.operator or "recurrence",
        )
    if parse_flex(rhs, symbols, functions) is None:
        return _failure(
            RECURRENCE, "reconstruction_cannot_be_built:unparseable_rhs",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
        )
    if z is None and not shift_var:
        return _failure(
            RECURRENCE, "reconstruction_cannot_be_built:no_shift_variable",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
        )
    n = z if z is not None and (not shift_var or z.name == shift_var) else None
    if n is None:
        n = next((s for s in F.free_symbols if s.name == shift_var), None)
    step_e = parse_flex(step, symbols, functions)
    rhs_e = parse_flex(rhs, symbols, functions)
    if n is None or step_e is None or rhs_e is None:
        return _failure(
            RECURRENCE, "reconstruction_cannot_be_built:shift_unparseable",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
        )
    residual = F.xreplace({n: n + step_e}) - F - rhs_e
    left = exact[mid] if mid else str(residual)
    return _ok_base(
        RECURRENCE, h, draft, mids, exact,
        left=left,
        right="0",
        reconstruction=str(residual),
        recurrence_rhs=rhs,
        shift_var=n.name,
        shift_step=step,
        var=n.name,
        theta=_theta_for(h, mid) if mid else {},
        variables={"shift": n.name, "step": step, "rhs": rhs},
        expected_relation="equal_zero",
    )


def _build_master(
    h, draft, mids, exact, symbols, functions,
) -> Obligation:
    F, z, err = _need_F(h, MASTER_INSTANCE, mids, exact, draft, symbols, functions)
    if err is not None:
        return err
    mid = mids[0]
    op = _first_op(h, mid)
    okind = str(_op_attr(op, "kind") or draft.operator or "identity")
    theta = _theta_for(h, mid)
    args = _op_args(h, mid)
    cand = None
    if okind in {"identity", "substitution", ""}:
        cand = instantiate(F, theta, symbols, functions)
    elif okind == "derivative":
        order = _as_int(args.get("order") or draft.variables.get("order") or 1, 1)
        var = z
        if var is None:
            return _failure(
                MASTER_INSTANCE, "reconstruction_cannot_be_built:no_diff_variable",
                member_ids=mids, exact=exact, latent=h.latent_object or "",
                assumptions=_assumptions(h, draft),
            )
        cand = instantiate(_diff_repeat(F, var, max(1, order)), theta, symbols, functions)
    elif okind == "permutation":
        inst = instantiate(F, theta, symbols, functions)
        cand = _swap_applied(inst) if inst is not None else None
    elif okind == "newton_dd":
        nodes = _nodes_for(h, mid, draft)
        if len(nodes) < 2 or z is None:
            return _failure(
                MASTER_INSTANCE, "reconstruction_cannot_be_built:need_two_nodes",
                member_ids=mids, exact=exact, latent=h.latent_object or "",
                assumptions=_assumptions(h, draft),
            )
        x = parse_flex(nodes[0], symbols, functions)
        y = parse_flex(nodes[1], symbols, functions)
        if x is None or y is None:
            return _failure(
                MASTER_INSTANCE, "reconstruction_cannot_be_built:unparseable_nodes",
                member_ids=mids, exact=exact, latent=h.latent_object or "",
                assumptions=_assumptions(h, draft),
            )
        cand = newton_first(F, z, x, y)
    else:
        cand = instantiate(F, theta, symbols, functions)
    if cand is None:
        return _failure(
            MASTER_INSTANCE, "reconstruction_cannot_be_built",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
        )
    return _ok_base(
        MASTER_INSTANCE, h, draft, mids, exact,
        left=exact[mid],
        right=str(cand),
        reconstruction=str(cand),
        theta=theta,
        variables=dict(theta),
        expected_relation="equal",
        order=_as_int(args.get("order") or 1, 1),
    )


def _build_basis(
    h, draft, mids, exact, symbols, functions,
) -> Obligation:
    mid = mids[0]
    args = _op_args(h, mid)
    basis_raw = args.get("basis") or draft.variables.get("basis")
    coef_raw = args.get("coefficients") or args.get("coeffs")
    if isinstance(basis_raw, str):
        basis_list = [p.strip() for p in basis_raw.split(",") if p.strip()]
    elif isinstance(basis_raw, list):
        basis_list = [str(x) for x in basis_raw]
    else:
        basis_list = []
    coefs: dict[str, str] = {}
    if isinstance(coef_raw, dict):
        coefs = {str(k): str(v) for k, v in coef_raw.items()}
    elif isinstance(coef_raw, list) and basis_list and len(coef_raw) == len(basis_list):
        coefs = {basis_list[i]: str(coef_raw[i]) for i in range(len(basis_list))}
    if not basis_list or not coefs:
        return _failure(
            BASIS_RECONSTRUCTION, "reconstruction_cannot_be_built:basis_or_coefficients_missing",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
            operator=draft.operator or "other",
        )
    F, z, _err = _need_F(h, BASIS_RECONSTRUCTION, mids, exact, draft, symbols, functions)
    theta = _theta_for(h, mid)
    acc = None
    for b in basis_list:
        be = parse_flex(str(b), symbols, functions)
        ce = parse_flex(str(coefs.get(str(b), "0")), symbols, functions)
        if be is None or ce is None:
            return _failure(
                BASIS_RECONSTRUCTION, "reconstruction_cannot_be_built:unparseable_basis",
                member_ids=mids, exact=exact, latent=h.latent_object or "",
                assumptions=_assumptions(h, draft),
            )
        if z is not None and theta:
            be = instantiate(be, theta, symbols, functions)
        term = ce * be
        acc = term if acc is None else acc + term
    if acc is None:
        return _failure(
            BASIS_RECONSTRUCTION, "reconstruction_cannot_be_built",
            member_ids=mids, exact=exact, latent=h.latent_object or "",
            assumptions=_assumptions(h, draft),
        )
    return _ok_base(
        BASIS_RECONSTRUCTION, h, draft, mids, exact,
        left=exact[mid],
        right=str(acc),
        reconstruction=str(acc),
        theta=theta,
        coefficients=coefs,
        basis=basis_list,
        variables=dict(theta),
        expected_relation="equal",
    )
