"""Latent-F consistency for Track V2.

``latent_compatible`` checks whether a claimed latent object is compatible
with the listed operators and member roles. It does not invent F, bind
catalog members, run limits, or certify ZERO.

Verdicts: True, False, ``UNKNOWN``. Call ``as_bool`` before
``compose_family_verdict`` (``UNKNOWN`` is truthy as a string).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional, Union

import sympy
from sympy.parsing.sympy_parser import parse_expr

from research.representation_invention.schema import MEMBER_ROLES, OPERATOR_KINDS

UNKNOWN = "UNKNOWN"
Verdict = Union[bool, str]

CHECK_NAMES = (
    "argument_compatibility",
    "derivative_order",
    "special_function_head",
    "shared_vars",
    "multiplicity",
    "recurrence_compatibility",
    "member_roles",
)

_MAX_LATENT_CHARS = 4096
_MAX_PARSE_CHARS = 512

_IDENT = re.compile(r"[A-Za-z_][\w]*")
_SYMBOL_CTOR = re.compile(
    r"Symbol\(\s*['\"]([A-Za-z_][\w]*)['\"]",
)
_CALL = re.compile(r"([A-Za-z_][\w]*)\s*\(\s*([A-Za-z_][\w]*)\s*\)")
_EPS_PREFIX = re.compile(
    r"(?i)^(eps|epsilon|varepsilon)_([A-Za-z_][\w]*)$",
)
_NUMERIC = re.compile(r"^[-+]?(?:\d+(?:\.\d*)?|\.\d+)$")
_PROSE = re.compile(
    r"(?i)\b(generic|degenerate|branch|catalog|unmodified|piecewise|"
    r"summation|coefficient|true-branch|where|viewed|raw)\b"
)
_GOLD_MASTER = re.compile(
    r"(?i)(?:\\Phi_\\Gamma|\bPhi[_\s-]*Gamma\b|\bPhiGamma\b|\bL[4-7]\b)"
)
_G4 = re.compile(r"^G\d{4}$")

_PG_FAMILY = frozenset({"polygamma", "digamma", "trigamma", "psi"})
_GAMMA_FAMILY = frozenset({"gamma", "loggamma", "log_gamma"})
_SF_ALL = _PG_FAMILY | _GAMMA_FAMILY

_HEAD_WORD = re.compile(
    r"(?i)\b(polygamma|digamma|trigamma|loggamma|log_gamma|gamma|psi)\b"
)

_VAR_VALUE_KEYS = (
    "var",
    "wrt",
    "variable",
    "index",
    "at",
    "to",
    "point",
    "from",
    "source",
    "target",
    "source1",
    "target1",
    "source2",
    "target2",
    "x",
    "y",
)
_HEAD_KEYS = ("head", "function", "expected_head", "special_function")
_ORDER_KEYS = ("order", "n_diff", "times")
_SHIFT_KEYS = ("delta", "step", "h")
_META_KEYS = frozenset(
    {
        "member",
        "member_id",
        "O",
        "kind",
        "operator",
        "theta",
        "map",
        "note",
        "nodes",
        "order",
        "n",
        "n_diff",
        "times",
        "var",
        "wrt",
        "variable",
        "index",
        "at",
        "to",
        "point",
        "delta",
        "step",
        "h",
        "perm",
        "swap",
        "x",
        "y",
        "multiplicity",
        "source",
        "target",
        "source1",
        "target1",
        "source2",
        "target2",
        "limits",
        "head",
        "function",
        "expected_head",
        "special_function",
        "from",
        "limit",
    }
)

_ROLE_KINDS = {
    "generic": frozenset(
        {"identity", "newton_dd", "hermite_dd", "substitution", "permutation", "shift"}
    ),
    "degenerate": frozenset(
        {"limit", "substitution", "newton_dd", "hermite_dd", "derivative"}
    ),
    "repeated": frozenset({"hermite_dd", "derivative", "limit"}),
    "instance": frozenset(
        {"substitution", "permutation", "shift", "recurrence", "identity"}
    ),
    "kernel": frozenset({"identity", "substitution", "permutation"}),
    "other": frozenset(OPERATOR_KINDS),
}

_PARSE_LOCAL: dict[str, Any] = {
    "polygamma": sympy.polygamma,
    "PolyGamma": sympy.polygamma,
    "psi": sympy.digamma,
    "digamma": sympy.digamma,
    "gamma": sympy.gamma,
    "loggamma": sympy.loggamma,
    "exp": sympy.exp,
    "log": sympy.log,
    "sin": sympy.sin,
    "cos": sympy.cos,
    "Derivative": sympy.Derivative,
    "pi": sympy.pi,
    "E": sympy.E,
    "I": sympy.I,
    "oo": sympy.oo,
}
if hasattr(sympy, "trigamma"):
    _PARSE_LOCAL["trigamma"] = sympy.trigamma


@dataclass(frozen=True)
class CheckResult:
    name: str
    verdict: Verdict
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "verdict": self.verdict, "note": self.note}


@dataclass(frozen=True)
class LatentConsistency:
    """Per-check report. ``verdict`` is True, False, or UNKNOWN."""

    verdict: Verdict
    checks: tuple[CheckResult, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "checks": [c.to_dict() for c in self.checks],
        }


def as_bool(verdict: Verdict) -> bool:
    """True only on explicit compatibility. UNKNOWN must not certify."""
    return verdict is True


def latent_compatible(
    hyp: Any = None,
    *,
    latent_object: Any = None,
    operators: Any = None,
    member_roles: Any = None,
    latent_variables: Any = None,
    nodes: Any = None,
    member_ids: Any = None,
    representation_type: Any = None,
) -> Verdict:
    """Return True, False, or UNKNOWN. Does not discover F."""
    return check_latent_consistency(
        hyp,
        latent_object=latent_object,
        operators=operators,
        member_roles=member_roles,
        latent_variables=latent_variables,
        nodes=nodes,
        member_ids=member_ids,
        representation_type=representation_type,
    ).verdict


def check_latent_consistency(
    hyp: Any = None,
    *,
    latent_object: Any = None,
    operators: Any = None,
    member_roles: Any = None,
    latent_variables: Any = None,
    nodes: Any = None,
    member_ids: Any = None,
    representation_type: Any = None,
) -> LatentConsistency:
    try:
        fields = _fields(
            hyp,
            latent_object=latent_object,
            operators=operators,
            member_roles=member_roles,
            latent_variables=latent_variables,
            nodes=nodes,
            member_ids=member_ids,
            representation_type=representation_type,
        )
        return _evaluate(fields)
    except Exception as exc:
        return LatentConsistency(
            UNKNOWN,
            (CheckResult("error", UNKNOWN, type(exc).__name__),),
        )


def _combine(verdicts: list[Verdict]) -> Verdict:
    if any(v is False for v in verdicts):
        return False
    if any(v == UNKNOWN for v in verdicts):
        return UNKNOWN
    return True


def _fields(hyp: Any, **overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {}
    if hyp is None:
        pass
    elif isinstance(hyp, dict):
        base = dict(hyp)
    else:
        for key in (
            "latent_object",
            "operators",
            "member_roles",
            "latent_variables",
            "nodes",
            "member_ids",
            "representation_type",
        ):
            if hasattr(hyp, key):
                base[key] = getattr(hyp, key)
    for key, val in overrides.items():
        if val is not None:
            base[key] = val
    return base


def _evaluate(fields: dict[str, Any]) -> LatentConsistency:
    latent = str(fields.get("latent_object") or "").strip()
    ops_raw = fields.get("operators")
    roles_raw = fields.get("member_roles")
    if not latent:
        return _uniform(UNKNOWN, "latent_object_empty")
    if _GOLD_MASTER.search(latent):
        return _uniform(False, "invented_master_name")
    if len(latent) > _MAX_LATENT_CHARS:
        return _uniform(UNKNOWN, "size_guard")
    if ops_raw is None:
        return _uniform(UNKNOWN, "operators_missing")
    ops, op_err = _parse_ops(ops_raw)
    if op_err == "operators_not_list":
        return _uniform(UNKNOWN, op_err)
    if op_err:
        return _uniform(False, op_err)
    if not ops:
        return _uniform(UNKNOWN, "operators_empty")

    roles, role_err = _parse_roles(roles_raw)
    if role_err:
        return _uniform(False, role_err)

    member_ids = _parse_ids(fields.get("member_ids"))
    if member_ids:
        for op in ops:
            if op.member_id and op.member_id not in member_ids:
                return _uniform(False, f"operator_member_not_in_member_ids:{op.member_id}")
        for mid in roles:
            if mid not in member_ids:
                return _uniform(False, f"role_id_not_in_member_ids:{mid}")
    else:
        member_ids = _inferred_ids(ops, roles)

    nodes, node_err = _parse_nodes(fields.get("nodes"))
    if node_err:
        return _uniform(False, node_err)

    lv = _parse_names(fields.get("latent_variables"))
    rtype = str(fields.get("representation_type") or "").strip()
    sig = _signature(latent, lv)

    checks = (
        _check_arguments(sig, ops, nodes),
        _check_derivative_order(sig, ops, nodes),
        _check_special_head(sig, ops, latent),
        _check_shared_vars(sig, ops, nodes, lv),
        _check_multiplicity(ops, nodes, roles),
        _check_recurrence(sig, ops, rtype),
        _check_roles(ops, roles),
    )
    return LatentConsistency(_combine([c.verdict for c in checks]), checks)


def _uniform(verdict: Verdict, note: str) -> LatentConsistency:
    checks = tuple(CheckResult(name, verdict, note) for name in CHECK_NAMES)
    return LatentConsistency(verdict, checks)


@dataclass(frozen=True)
class _Op:
    member_id: str
    kind: str
    args: dict[str, Any]
    var_names: tuple[str, ...]
    eval_points: tuple[str, ...]
    subst_pairs: tuple[tuple[str, str], ...]
    order: Optional[int]
    order_unparsed: bool
    multiplicity: Optional[int]
    multiplicity_unparsed: bool
    heads: tuple[str, ...]
    shift_var: Optional[str]
    shift_delta: Any
    coincident_eval: bool
    coalescence: bool
    perm_ok: Optional[bool]


@dataclass(frozen=True)
class _Node:
    name: str
    expression: str
    multiplicity: int


@dataclass(frozen=True)
class _Sig:
    name: str
    args: tuple[str, ...]
    body: str
    parsed: Optional[sympy.Expr]
    heads: tuple[str, ...]
    pg_order: Any
    pg_arg: Optional[str]


def _parse_ops(raw: Any) -> tuple[list[_Op], str]:
    if not isinstance(raw, list):
        return [], "operators_not_list"
    out: list[_Op] = []
    for item in raw:
        if isinstance(item, dict):
            mid = str(item.get("member_id") or item.get("member") or "").strip()
            kind = str(item.get("kind") or item.get("O") or "").strip()
            args = item.get("args") if isinstance(item.get("args"), dict) else {}
            if not args:
                args = {
                    k: v
                    for k, v in item.items()
                    if k not in {"kind", "O", "member_id", "member", "args"}
                }
        elif hasattr(item, "kind"):
            mid = str(getattr(item, "member_id", "") or "").strip()
            kind = str(getattr(item, "kind", "") or "").strip()
            args = dict(getattr(item, "args", None) or {})
        else:
            return [], "operator_not_object"
        if not kind:
            return [], "operator_missing_kind"
        if kind not in OPERATOR_KINDS:
            return [], f"unknown_operator_kind:{kind}"
        out.append(_op_from(mid, kind, dict(args or {})))
    return out, ""


def _op_from(member_id: str, kind: str, args: dict[str, Any]) -> _Op:
    nested = args.get("theta") if isinstance(args.get("theta"), dict) else None
    if not nested:
        nested = args.get("map") if isinstance(args.get("map"), dict) else {}
    merged = dict(args)
    if isinstance(nested, dict):
        for k, v in nested.items():
            merged.setdefault(k, v)

    subst: list[tuple[str, str]] = []
    eval_points: list[str] = []
    var_names: list[str] = []
    heads: list[str] = []

    for key in _HEAD_KEYS:
        val = merged.get(key)
        if isinstance(val, str) and val.strip():
            heads.extend(_head_names(val))

    for key in _VAR_VALUE_KEYS:
        val = merged.get(key)
        if val in (None, ""):
            continue
        text = str(val).strip()
        if key in {"x", "y", "at", "to", "point", "target", "target1", "target2"}:
            eval_points.append(text)
        else:
            var_names.append(text)

    for key, val in merged.items():
        if key in _META_KEYS:
            continue
        if isinstance(val, (str, int, float)) and not isinstance(val, bool):
            subst.append((str(key), str(val)))

    nodes_raw = merged.get("nodes")
    node_texts: list[str] = []
    if isinstance(nodes_raw, (list, tuple)):
        for item in nodes_raw:
            if isinstance(item, dict):
                t = str(item.get("expression") or item.get("name") or item.get("expr") or "").strip()
            else:
                t = str(item).strip()
            if t:
                node_texts.append(t)
                eval_points.append(t)

    limits = merged.get("limits")
    if isinstance(limits, (list, tuple)):
        for item in limits:
            if not isinstance(item, dict):
                continue
            src = item.get("var") or item.get("source") or item.get("from")
            dst = item.get("to") or item.get("target") or item.get("at")
            if src not in (None, ""):
                var_names.append(str(src).strip())
            if dst not in (None, ""):
                eval_points.append(str(dst).strip())
            if src not in (None, "") and dst not in (None, ""):
                subst.append((str(src), str(dst)))

    for a, b in (("source", "target"), ("source1", "target1"), ("source2", "target2")):
        if merged.get(a) not in (None, "") and merged.get(b) not in (None, ""):
            subst.append((str(merged[a]), str(merged[b])))

    swap = merged.get("swap")
    if isinstance(swap, (list, tuple)) and len(swap) == 2:
        subst.append((str(swap[0]), str(swap[1])))
        var_names.extend([str(swap[0]), str(swap[1])])

    perm_ok: Optional[bool] = None
    perm = merged.get("perm")
    if perm is not None:
        if not isinstance(perm, (list, tuple)) or not perm:
            perm_ok = False
        else:
            try:
                idx = [int(x) for x in perm]
            except (TypeError, ValueError):
                perm_ok = False
            else:
                perm_ok = sorted(idx) == list(range(len(idx)))

    order, order_unparsed = _int_field(merged, _ORDER_KEYS)
    if (
        kind == "derivative"
        and order is None
        and not order_unparsed
        and merged.get("n") not in (None, "")
        and str(merged.get("var") or merged.get("wrt") or "") != str(merged.get("n"))
    ):
        order, order_unparsed = _int_field(merged, ("n",))

    multiplicity, mult_unparsed = _int_field(merged, ("multiplicity",))
    if multiplicity is None and not mult_unparsed and node_texts:
        counts: dict[str, int] = {}
        for t in node_texts:
            counts[t] = counts.get(t, 0) + 1
        mx = max(counts.values()) if counts else 0
        if mx >= 2:
            multiplicity = mx

    coincident = False
    if len(node_texts) >= 2 and len(set(node_texts)) == 1:
        coincident = True
    if str(merged.get("x") or "").strip() and str(merged.get("x")).strip() == str(merged.get("y") or "").strip():
        coincident = True

    coalescence = False
    pairs = list(subst)
    if kind == "limit":
        src = merged.get("var") or merged.get("source") or merged.get("from")
        dst = merged.get("to") or merged.get("target") or merged.get("at")
        if src not in (None, "") and dst not in (None, ""):
            pairs.append((str(src), str(dst)))
    for a, b in pairs:
        if _is_coalescence(a, b):
            coalescence = True
            break

    shift_var = None
    for key in ("var", "wrt", "variable", "index"):
        if merged.get(key) not in (None, ""):
            shift_var = str(merged[key]).strip()
            break
    shift_delta = None
    for key in _SHIFT_KEYS:
        if merged.get(key) not in (None, ""):
            shift_delta = merged[key]
            break

    if kind in {"limit", "substitution", "newton_dd", "hermite_dd", "derivative"}:
        if merged.get("var") not in (None, ""):
            var_names.append(str(merged["var"]).strip())
        if merged.get("wrt") not in (None, ""):
            var_names.append(str(merged["wrt"]).strip())

    return _Op(
        member_id=member_id,
        kind=kind,
        args=dict(args),
        var_names=tuple(_dedupe(var_names)),
        eval_points=tuple(_dedupe(eval_points)),
        subst_pairs=tuple(pairs),
        order=order,
        order_unparsed=order_unparsed,
        multiplicity=multiplicity,
        multiplicity_unparsed=mult_unparsed,
        heads=tuple(_dedupe(heads)),
        shift_var=shift_var,
        shift_delta=shift_delta,
        coincident_eval=coincident,
        coalescence=coalescence,
        perm_ok=perm_ok,
    )


def _int_field(blob: dict[str, Any], keys: tuple[str, ...]) -> tuple[Optional[int], bool]:
    for key in keys:
        if key not in blob or blob[key] in (None, ""):
            continue
        n = _as_int(blob[key])
        if n is None:
            return None, True
        return n, False
    return None, False


def _as_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    if n != int(n):
        return None
    return int(n)


def _dedupe(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        s = str(item).strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _parse_roles(raw: Any) -> tuple[dict[str, str], str]:
    if raw in (None, ""):
        return {}, ""
    if not isinstance(raw, dict):
        return {}, "member_roles_not_object"
    out: dict[str, str] = {}
    for key, val in raw.items():
        ks = str(key).strip()
        vs = str(val).strip() or "other"
        if not ks:
            return {}, "role_missing_id"
        if vs not in MEMBER_ROLES:
            return {}, f"unknown_role:{vs}"
        out[ks] = vs
    return out, ""


def _parse_ids(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        s = str(item).strip()
        if s and s not in out:
            out.append(s)
    return out


def _inferred_ids(ops: list[_Op], roles: dict[str, str]) -> list[str]:
    out: list[str] = []
    for op in ops:
        if op.member_id and op.member_id not in out:
            out.append(op.member_id)
    for mid in roles:
        if mid not in out:
            out.append(mid)
    return out


def _parse_names(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(x).strip() for x in raw if str(x).strip()]


def _parse_nodes(raw: Any) -> tuple[list[_Node], str]:
    if raw in (None, "", []):
        return [], ""
    if not isinstance(raw, list):
        return [], "nodes_not_list"
    out: list[_Node] = []
    for item in raw:
        if hasattr(item, "name"):
            name = str(getattr(item, "name", "") or "").strip()
            expr = str(getattr(item, "expression", "") or "").strip()
            try:
                mult = int(getattr(item, "multiplicity", 1) or 1)
            except (TypeError, ValueError):
                return [], "node_multiplicity_not_int"
        elif isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            expr = str(item.get("expression") or item.get("expr") or "").strip()
            try:
                mult = int(item.get("multiplicity", 1))
            except (TypeError, ValueError):
                return [], "node_multiplicity_not_int"
        else:
            return [], "node_not_object"
        if not name:
            return [], "node_missing_name"
        if mult < 1:
            return [], "node_multiplicity_lt_1"
        out.append(_Node(name=name, expression=expr, multiplicity=mult))
    return out, ""


def _split_head(text: str) -> tuple[str, list[str], str]:
    """Match F(args) at the first parenthesis, not the last ')' in the body."""
    s = (text or "").strip()
    m = _IDENT.match(s)
    if not m:
        return "", [], s
    name = m.group(0)
    i = m.end()
    while i < len(s) and s[i].isspace():
        i += 1
    if i >= len(s) or s[i] != "(":
        return name, [], s
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "(":
            depth += 1
        elif s[j] == ")":
            depth -= 1
            if depth == 0:
                inside = s[i + 1 : j]
                rest = s[j + 1 :].lstrip()
                if rest.startswith(":="):
                    rest = rest[2:].lstrip()
                elif rest[:1] in "=:":
                    rest = rest[1:].lstrip()
                return name, _split_sig_args(inside), rest
    return name, [], s


def _signature(latent: str, latent_variables: list[str]) -> _Sig:
    text = latent.strip().strip("`")
    text = text.replace(":=", "=")
    name, args, body = _split_head(text)
    if not args and not body:
        body = text
    parsed = _try_parse(body)
    heads = (
        _heads_from_parsed(parsed)
        if parsed is not None
        else _heads_from_text(body or text)
    )
    pg_order, pg_arg = _polygamma_slots(parsed)
    if not args and latent_variables:
        args = list(latent_variables)
    if not args and parsed is not None:
        args = [
            s.name
            for s in parsed.free_symbols
            if s.name not in {"pi", "E"}
        ]
    return _Sig(
        name=name,
        args=tuple(args),
        body=body,
        parsed=parsed,
        heads=tuple(_dedupe(list(heads))),
        pg_order=pg_order,
        pg_arg=pg_arg,
    )


def _split_sig_args(inside: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    for ch in inside or "":
        if ch in "([{":
            depth += 1
            buf.append(ch)
        elif ch in ")]}":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif depth == 0 and ch in ",;":
            token = "".join(buf).strip()
            buf = []
            ident = _arg_ident(token)
            if ident:
                parts.append(ident)
        else:
            buf.append(ch)
    ident = _arg_ident("".join(buf).strip())
    if ident:
        parts.append(ident)
    return parts


def _arg_ident(token: str) -> str:
    if not token:
        return ""
    if "=" in token:
        token = token.split("=", 1)[0].strip()
    m = _IDENT.match(token.strip())
    return m.group(0) if m else ""


def _try_parse(body: str) -> Optional[sympy.Expr]:
    text = (body or "").strip()
    if not text or len(text) > _MAX_PARSE_CHARS:
        return None
    if _PROSE.search(text) or _G4.fullmatch(text):
        return None
    if _IDENT.fullmatch(text):
        return sympy.Symbol(text)
    if not re.search(r"[+\-*/^]|\w+\(", text):
        return None
    try:
        expr = parse_expr(text, local_dict=dict(_PARSE_LOCAL), evaluate=True)
    except Exception:
        return None
    if not isinstance(expr, sympy.Expr):
        return None
    return _rewrite_heads(expr)


def _rewrite_heads(expr: sympy.Expr) -> sympy.Expr:
    repl: dict[sympy.Expr, sympy.Expr] = {}
    for f in expr.atoms(sympy.Function):
        name = getattr(f.func, "__name__", "") or str(f.func)
        if name in {"psi", "digamma"} and len(f.args) == 1:
            repl[f] = sympy.polygamma(0, f.args[0])
        elif name == "PolyGamma" and len(f.args) == 2:
            repl[f] = sympy.polygamma(f.args[0], f.args[1])
    return expr.xreplace(repl) if repl else expr


def _heads_from_parsed(expr: sympy.Expr) -> list[str]:
    found: list[str] = []
    if expr.atoms(sympy.polygamma):
        found.append("polygamma")
    if expr.atoms(sympy.gamma):
        found.append("gamma")
    if expr.atoms(sympy.loggamma):
        found.append("loggamma")
    for f in expr.atoms(sympy.Function):
        name = (getattr(f.func, "__name__", "") or str(f.func)).lower()
        if name in _SF_ALL:
            found.append(name if name != "polygamma" else "polygamma")
    return found


def _heads_from_text(text: str) -> list[str]:
    found: list[str] = []
    for m in _HEAD_WORD.finditer(text or ""):
        word = m.group(1).lower()
        found.append("polygamma" if word == "polygamma" else word)
    return found


def _head_names(text: str) -> list[str]:
    return _heads_from_text(text) or (
        [text.strip().lower()] if str(text).strip() else []
    )


def _polygamma_slots(expr: Optional[sympy.Expr]) -> tuple[Any, Optional[str]]:
    if expr is None:
        return None, None
    pgs = list(expr.atoms(sympy.polygamma))
    if len(pgs) != 1 or len(pgs[0].args) != 2:
        return None, None
    order, arg = pgs[0].args
    arg_name = arg.name if isinstance(arg, sympy.Symbol) else str(arg)
    return order, arg_name


def _tokens(name: str) -> frozenset[str]:
    raw = (name or "").strip()
    if not raw:
        return frozenset()
    out: set[str] = {raw, raw.lower()}
    for m in _SYMBOL_CTOR.finditer(raw):
        out.add(m.group(1))
        out.add(m.group(1).lower())
    for fn, inner in _CALL.findall(raw):
        out.add(fn)
        out.add(fn.lower())
        out.add(inner)
        out.add(inner.lower())
    m = _EPS_PREFIX.match(raw)
    if m:
        out.add(m.group(2))
        out.add(m.group(2).lower())
    ident = _IDENT.match(raw)
    if ident:
        out.add(ident.group(0))
        out.add(ident.group(0).lower())
    return frozenset(t for t in out if t)


def _token_union(names: list[str] | tuple[str, ...]) -> frozenset[str]:
    acc: set[str] = set()
    for name in names:
        acc |= set(_tokens(name))
    return frozenset(acc)


def _is_numeric(text: str) -> bool:
    return bool(_NUMERIC.fullmatch((text or "").strip()))


def _name_allowed(name: str, allowed: frozenset[str]) -> bool:
    if not (name or "").strip():
        return True
    if _is_numeric(name):
        return True
    toks = _tokens(name)
    if not toks:
        return True
    return bool(toks & allowed)


def _is_coalescence(src: str, dst: str) -> bool:
    if _is_numeric(src) or _is_numeric(dst):
        return False
    a = _tokens(src)
    b = _tokens(dst)
    if not a or not b:
        return False
    return a != b


def _latent_allowed(sig: _Sig, nodes: list[_Node]) -> frozenset[str]:
    names = list(sig.args)
    names.extend(n.name for n in nodes if n.name)
    names.extend(n.expression for n in nodes if n.expression)
    return _token_union(names)


def _analytic_args(sig: _Sig) -> frozenset[str]:
    return _token_union(list(sig.args))


def _check_arguments(sig: _Sig, ops: list[_Op], nodes: list[_Node]) -> CheckResult:
    latent_args = _analytic_args(sig)
    if not latent_args:
        return CheckResult("argument_compatibility", UNKNOWN, "no_latent_args")
    allowed = _latent_allowed(sig, nodes)
    node_allowed = _token_union(
        [n.name for n in nodes] + [n.expression for n in nodes if n.expression]
    )
    for op in ops:
        if op.kind == "other":
            return CheckResult("argument_compatibility", UNKNOWN, "operator_kind_other")
        if op.perm_ok is False:
            return CheckResult("argument_compatibility", False, "perm_not_a_permutation")
        if op.perm_ok is True and sig.args:
            perm = op.args.get("perm")
            if isinstance(perm, (list, tuple)) and len(perm) != len(sig.args):
                return CheckResult("argument_compatibility", False, "perm_arity_mismatch")
        for name in op.var_names:
            if not _name_allowed(name, latent_args | node_allowed):
                return CheckResult(
                    "argument_compatibility", False, f"var_not_in_latent:{name}"
                )
            # analytic var (wrt/var) must hit F's arguments, not only a node label
            if op.kind in {"derivative", "shift", "recurrence", "newton_dd", "hermite_dd"}:
                key_var = str(op.args.get("var") or op.args.get("wrt") or op.shift_var or "")
                if name == key_var and not _name_allowed(name, latent_args):
                    return CheckResult(
                        "argument_compatibility", False, f"analytic_var_not_in_latent:{name}"
                    )
        for src, dst in op.subst_pairs:
            if not _name_allowed(src, allowed):
                return CheckResult(
                    "argument_compatibility", False, f"subst_src_not_in_latent:{src}"
                )
            if not _name_allowed(dst, allowed) and not _is_numeric(dst):
                return CheckResult(
                    "argument_compatibility", False, f"subst_dst_not_in_latent:{dst}"
                )
        if nodes:
            for pt in op.eval_points:
                if _is_numeric(pt):
                    continue
                if not _name_allowed(pt, allowed):
                    return CheckResult(
                        "argument_compatibility", False, f"eval_point_not_in_nodes:{pt}"
                    )
        if op.kind in {"derivative", "newton_dd", "hermite_dd", "shift", "recurrence"}:
            key_var = str(op.args.get("var") or op.args.get("wrt") or op.shift_var or "")
            if not key_var and not op.var_names:
                if len(sig.args) != 1:
                    return CheckResult(
                        "argument_compatibility", UNKNOWN, f"missing_var:{op.kind}"
                    )
        if sig.pg_arg and op.kind in {"derivative", "newton_dd", "hermite_dd"}:
            wrt = op.shift_var or (op.var_names[0] if op.var_names else "")
            if wrt and sig.pg_order is not None:
                order_name = (
                    sig.pg_order.name
                    if isinstance(sig.pg_order, sympy.Symbol)
                    else None
                )
                if order_name and _name_allowed(wrt, _tokens(order_name)):
                    if not _name_allowed(wrt, _tokens(sig.pg_arg)):
                        return CheckResult(
                            "argument_compatibility",
                            False,
                            "derivative_wrt_polygamma_order",
                        )
    return CheckResult("argument_compatibility", True, "ok")


def _check_derivative_order(sig: _Sig, ops: list[_Op], nodes: list[_Node]) -> CheckResult:
    relevant = [op for op in ops if op.kind in {"derivative", "hermite_dd"}]
    if not relevant:
        return CheckResult("derivative_order", True, "no_derivative_ops")
    for op in relevant:
        if op.kind == "derivative":
            if op.order_unparsed:
                return CheckResult("derivative_order", UNKNOWN, "order_unparsed")
            order = 1 if op.order is None else op.order
            if order < 1:
                return CheckResult("derivative_order", False, "order_lt_1")
            if op.multiplicity is not None:
                if op.multiplicity_unparsed:
                    return CheckResult("derivative_order", UNKNOWN, "multiplicity_unparsed")
                if op.multiplicity != order + 1:
                    return CheckResult(
                        "derivative_order",
                        False,
                        f"order_{order}_vs_multiplicity_{op.multiplicity}",
                    )
        if op.kind == "hermite_dd":
            if op.order_unparsed or op.multiplicity_unparsed:
                return CheckResult("derivative_order", UNKNOWN, "hermite_order_unparsed")
            mult = op.multiplicity
            if mult is None:
                node_mult = [n.multiplicity for n in nodes if n.multiplicity >= 2]
                if node_mult:
                    mult = max(node_mult)
            if op.order is not None and mult is not None and op.order != mult - 1:
                return CheckResult(
                    "derivative_order",
                    False,
                    f"hermite_order_{op.order}_vs_multiplicity_{mult}",
                )
            if op.order is not None and op.order < 0:
                return CheckResult("derivative_order", False, "order_lt_0")
    return CheckResult("derivative_order", True, "ok")


def _family(heads: tuple[str, ...] | list[str]) -> Optional[str]:
    labels = {h.lower() for h in heads}
    pg = bool(labels & _PG_FAMILY)
    gm = bool(labels & _GAMMA_FAMILY)
    other = labels - _SF_ALL
    if other:
        return "other:" + ",".join(sorted(other))
    if pg and gm:
        return "gamma_poly"
    if pg:
        return "polygamma"
    if gm:
        return "gamma"
    return None


def _check_special_head(sig: _Sig, ops: list[_Op], latent: str) -> CheckResult:
    f_heads = list(sig.heads)
    if not f_heads:
        f_heads = _heads_from_text(latent)
    f_fam = _family(tuple(f_heads))
    op_heads: list[str] = []
    needs_head = False
    for op in ops:
        op_heads.extend(op.heads)
        if op.kind in {"derivative", "newton_dd", "hermite_dd"}:
            needs_head = True
    o_fam = _family(tuple(op_heads)) if op_heads else None

    if o_fam and o_fam.startswith("other:"):
        if f_fam and f_fam != o_fam and not (
            f_fam in {"polygamma", "gamma", "gamma_poly"} and o_fam.startswith("other:")
        ):
            return CheckResult("special_function_head", False, "unrelated_operator_head")
        if f_fam in {"polygamma", "gamma", "gamma_poly"}:
            return CheckResult("special_function_head", False, "unrelated_operator_head")

    if f_fam and o_fam:
        if f_fam == o_fam:
            return CheckResult("special_function_head", True, f_fam)
        # gamma differentiates into polygamma; both stay in {gamma, polygamma, gamma_poly}
        allowed = {"gamma", "polygamma", "gamma_poly"}
        if f_fam in allowed and o_fam in allowed:
            if f_fam == "polygamma" and o_fam == "gamma":
                rec = any(op.kind in {"recurrence", "shift"} for op in ops)
                if rec:
                    return CheckResult(
                        "special_function_head",
                        False,
                        "polygamma_vs_gamma_recurrence",
                    )
            return CheckResult("special_function_head", True, f"{f_fam}->{o_fam}")
        return CheckResult("special_function_head", False, f"{f_fam}_vs_{o_fam}")

    if not f_fam and o_fam in {"polygamma", "gamma"}:
        if sig.parsed is not None:
            return CheckResult("special_function_head", False, "algebraic_vs_special")
        return CheckResult("special_function_head", UNKNOWN, "unparsed_vs_special_op")

    if needs_head and not f_fam and sig.parsed is None:
        return CheckResult("special_function_head", UNKNOWN, "unparsed_special_head")
    return CheckResult("special_function_head", True, "n/a" if not f_fam else f_fam)


def _check_shared_vars(
    sig: _Sig, ops: list[_Op], nodes: list[_Node], lv: list[str]
) -> CheckResult:
    latent = _token_union(list(sig.args) + list(lv))
    if not latent:
        return CheckResult("shared_vars", UNKNOWN, "no_latent_vars")
    used: set[str] = set()
    nontrivial = False
    for op in ops:
        if op.kind == "other":
            return CheckResult("shared_vars", UNKNOWN, "operator_kind_other")
        if op.kind != "identity":
            nontrivial = True
        for name in list(op.var_names) + [a for a, _ in op.subst_pairs]:
            used |= set(_tokens(name))
    if not nontrivial:
        return CheckResult("shared_vars", True, "identity_only")
    if not used:
        return CheckResult("shared_vars", True, "no_operator_vars")
    if used & set(latent):
        return CheckResult("shared_vars", True, "ok")
    node_toks = _token_union([n.name for n in nodes] + [n.expression for n in nodes])
    if used & set(node_toks) and (node_toks & set(latent) or not sig.args):
        return CheckResult("shared_vars", True, "via_nodes")
    return CheckResult("shared_vars", False, "disjoint_operator_vars")


def _check_multiplicity(
    ops: list[_Op], nodes: list[_Node], roles: dict[str, str]
) -> CheckResult:
    for n in nodes:
        if n.multiplicity < 1:
            return CheckResult("multiplicity", False, "node_multiplicity_lt_1")
    for op in ops:
        if op.multiplicity_unparsed:
            return CheckResult("multiplicity", UNKNOWN, "multiplicity_unparsed")
        if op.multiplicity is not None and op.multiplicity < 1:
            return CheckResult("multiplicity", False, "op_multiplicity_lt_1")
        if op.kind == "hermite_dd":
            node_mult = op.multiplicity
            if node_mult is None:
                highs = [n.multiplicity for n in nodes if n.multiplicity >= 2]
                node_mult = max(highs) if highs else None
            if node_mult is None and op.coincident_eval:
                node_mult = 2
            if node_mult is not None and node_mult < 2 and not op.coalescence:
                return CheckResult("multiplicity", False, "hermite_multiplicity_lt_2")
        if op.kind == "newton_dd" and op.coincident_eval:
            role = roles.get(op.member_id, "")
            if role == "repeated":
                return CheckResult(
                    "multiplicity", False, "coincident_newton_is_not_repeated"
                )
            return CheckResult("multiplicity", False, "coincident_newton_ill_posed")
        if op.kind == "identity":
            role = roles.get(op.member_id, "")
            if role == "repeated":
                return CheckResult("multiplicity", False, "repeated_identity")
        if op.kind == "limit" and roles.get(op.member_id) == "repeated":
            if not op.coalescence:
                return CheckResult(
                    "multiplicity", False, "repeated_point_limit_not_coalescence"
                )
    for mid, role in roles.items():
        if role != "repeated":
            continue
        member_ops = [op for op in ops if op.member_id == mid]
        if not member_ops:
            continue
        ok = False
        for op in member_ops:
            if op.kind == "hermite_dd" and (op.multiplicity or 0) >= 2:
                ok = True
            elif op.kind == "derivative" and (op.order or 1) >= 1:
                ok = True
            elif op.kind == "limit" and op.coalescence:
                ok = True
            elif any(n.multiplicity >= 2 for n in nodes):
                ok = True
        if not ok:
            return CheckResult("multiplicity", False, f"repeated_without_multiplicity:{mid}")
    return CheckResult("multiplicity", True, "ok")


def _check_recurrence(sig: _Sig, ops: list[_Op], rtype: str) -> CheckResult:
    recs = [op for op in ops if op.kind in {"recurrence", "shift"}]
    if rtype == "recurrence_family" and not recs:
        return CheckResult("recurrence_compatibility", False, "recurrence_family_without_shift")
    if not recs:
        return CheckResult("recurrence_compatibility", True, "no_recurrence_ops")
    latent = _analytic_args(sig)
    if not latent:
        return CheckResult("recurrence_compatibility", UNKNOWN, "no_latent_args")
    for op in recs:
        var = op.shift_var or (op.var_names[0] if op.var_names else "")
        if not var:
            return CheckResult("recurrence_compatibility", UNKNOWN, "recurrence_var_missing")
        if not _name_allowed(var, latent):
            return CheckResult(
                "recurrence_compatibility", False, f"recurrence_var_not_latent:{var}"
            )
        if op.shift_delta in (None, "") and op.kind == "recurrence":
            return CheckResult("recurrence_compatibility", UNKNOWN, "recurrence_delta_missing")
        if sig.pg_arg and sig.pg_order is not None:
            order_name = (
                sig.pg_order.name if isinstance(sig.pg_order, sympy.Symbol) else None
            )
            if order_name and _name_allowed(var, _tokens(order_name)):
                if not _name_allowed(var, _tokens(sig.pg_arg)):
                    return CheckResult(
                        "recurrence_compatibility",
                        False,
                        "recurrence_on_polygamma_order",
                    )
    return CheckResult("recurrence_compatibility", True, "ok")


def _check_roles(ops: list[_Op], roles: dict[str, str]) -> CheckResult:
    if not roles:
        return CheckResult("member_roles", UNKNOWN, "roles_missing")
    has_identity = any(op.kind == "identity" for op in ops)
    for op in ops:
        if not op.member_id or op.member_id not in roles:
            continue
        role = roles[op.member_id]
        allowed = _ROLE_KINDS.get(role)
        if allowed is None:
            return CheckResult("member_roles", False, f"unknown_role:{role}")
        if op.kind == "other":
            return CheckResult("member_roles", UNKNOWN, "operator_kind_other")
        if op.kind not in allowed:
            if role == "generic" and op.kind == "limit" and has_identity:
                return CheckResult("member_roles", False, "generic_limit_with_identity")
            if role == "generic" and op.kind == "derivative" and has_identity:
                return CheckResult("member_roles", False, "generic_derivative_with_identity")
            return CheckResult(
                "member_roles", False, f"role_{role}_vs_kind_{op.kind}:{op.member_id}"
            )
        if role == "degenerate" and op.kind == "identity":
            return CheckResult("member_roles", False, f"degenerate_identity:{op.member_id}")
        if role == "repeated" and op.kind == "identity":
            return CheckResult("member_roles", False, f"repeated_identity:{op.member_id}")
        if role == "repeated" and op.kind == "limit" and not op.coalescence:
            return CheckResult("member_roles", False, f"repeated_non_coalescent:{op.member_id}")
        if role == "generic" and op.kind == "limit" and has_identity:
            return CheckResult("member_roles", False, "generic_is_limit")
    # unlabeled operators are allowed; unlabeled-only → still UNKNOWN if nothing matched
    labeled = [op for op in ops if op.member_id in roles]
    if not labeled:
        return CheckResult("member_roles", UNKNOWN, "roles_do_not_cover_operators")
    return CheckResult("member_roles", True, "ok")
