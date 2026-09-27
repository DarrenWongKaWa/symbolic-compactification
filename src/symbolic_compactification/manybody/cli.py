"""``symbolic-compactification manybody ...``: JSON in, JSON out.

Every subcommand prints one JSON object. Exit status is 0 when the check ran
(whatever the verdict) and 2 on invalid input, so agents can branch on the
``status`` / ``verdict`` field instead of the exit code.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

EXIT_OK, EXIT_INPUT = 0, 2


# Options whose values are expressions; "-tanh(x)" must not read as a flag.
EXPRESSION_OPTIONS = frozenset({
    "--summand", "--claim", "--function", "--approximant", "--integrand",
    "--lhs", "--rhs", "--prefactor", "--expr",
})


def normalize_argv(argv: list[str]) -> list[str]:
    """Join `--claim -expr` into `--claim=-expr` so argparse keeps the sign."""
    out: list[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token in EXPRESSION_OPTIONS and i + 1 < len(argv) and argv[i + 1].startswith("-"):
            out.append(f"{token}={argv[i + 1]}")
            i += 2
            continue
        out.append(token)
        i += 1
    return out


def _symbols(value: str | None) -> list:
    if not value:
        return []
    path = Path(value)
    raw = path.read_text(encoding="utf-8") if path.is_file() else value
    data = yaml.safe_load(raw)
    if isinstance(data, dict):
        data = data.get("symbols", [])
    if not isinstance(data, list):
        raise ValueError("symbols must be a list or a mapping with 'symbols'")
    return data


def _expr(value: str) -> str:
    """Inline expression, or @path to read it from a file."""
    if value.startswith("@"):
        return Path(value[1:]).read_text(encoding="utf-8").strip()
    return value


def _names(value: str | None) -> tuple[str, ...]:
    return tuple(n.strip() for n in (value or "").split(",") if n.strip())


def add_manybody_parser(sub) -> argparse.ArgumentParser:
    p = sub.add_parser("manybody", help="many-body equivalence checks (JSON output)")
    msub = p.add_subparsers(dest="manybody_command", required=True)

    m = msub.add_parser("matsubara", help="T sum_n F(i w_n) versus a closed form")
    m.add_argument("--summand", required=True)
    m.add_argument("--claim", required=True)
    m.add_argument("--variable", default="z")
    m.add_argument("--beta", default="beta")
    m.add_argument("--statistics", choices=("fermion", "boson"), required=True)
    m.add_argument("--convergence", choices=("none", "plus", "minus"), default="none")
    m.add_argument("--symbols", help="JSON/YAML list, or a file holding it")
    m.add_argument("--rules", help="comma-separated declared rules")
    m.add_argument("--positive", help="comma-separated symbols sampled as positive")

    r = msub.add_parser("remainder", help="certify f = P + O(x**order) as x -> point")
    r.add_argument("--function", required=True)
    r.add_argument("--approximant", required=True)
    r.add_argument("--variable", required=True)
    r.add_argument("--point", choices=("0", "oo", "-oo"), required=True)
    r.add_argument("--order", type=int, required=True)
    r.add_argument("--direction", choices=("+", "-", "+-"), default="+-")
    r.add_argument("--symbols")
    r.add_argument("--positive")

    i = msub.add_parser("integral", help="numerical support for int_R f(w) dw = claim")
    i.add_argument("--integrand", required=True)
    i.add_argument("--claim", required=True)
    i.add_argument("--variable", default="w")
    i.add_argument("--beta")
    i.add_argument("--prefactor", default="1")
    i.add_argument("--symbols")
    i.add_argument("--positive")

    o = msub.add_parser("operator", help="identity in the free operator algebra")
    o.add_argument("--lhs", required=True)
    o.add_argument("--rhs", required=True)
    o.add_argument("--operators", required=True, help="comma-separated")
    o.add_argument("--scalars")
    o.add_argument("--hermitian")

    k = msub.add_parser("langreth", help="Langreth rule for a contour product")
    k.add_argument("--product", required=True, help="comma-separated, e.g. A,B,C")
    k.add_argument("--component", choices=("R", "A", "K", "less", "greater"), required=True)
    k.add_argument("--claim", required=True)
    d = msub.add_parser("identity", help="identity with DD_f(...), D_f(k, x), polygammas")
    d.add_argument("--lhs", required=True)
    d.add_argument("--rhs", required=True)
    d.add_argument("--functions", help="comma-separated arbitrary smooth functions")
    d.add_argument("--symbols")
    d.add_argument("--positive")

    c = msub.add_parser("coefficient", help="[x^k] of an expression versus a claim")
    c.add_argument("--expr", required=True)
    c.add_argument("--claim", required=True)
    c.add_argument("--variable", required=True)
    c.add_argument("--order", type=int, required=True)
    c.add_argument("--functions")
    c.add_argument("--symbols")
    c.add_argument("--positive")
    st = msub.add_parser("step", help="run one YAML step card (docs/encoding-cookbook.md)")
    st.add_argument("card", help="path to the step card")
    st.add_argument("--require-source", action="store_true",
                    help="NOT_DECIDED unless every expression is quoted from source_document")
    sts = msub.add_parser("steps", help="run a directory of step cards; table and HTML report")
    sts.add_argument("paths", nargs="+", help="card files or directories")
    sts.add_argument("--require-source", action="store_true")
    sts.add_argument("--html", help="write a reviewer HTML report here")
    dr = msub.add_parser("draft", help="draft step cards from a .tex file or a plain-text sheet")
    dr.add_argument("document")
    dr.add_argument("--out", required=True, help="directory for the cards and conventions.yaml")
    for parser in (m, r, i, o, k, d, c, st, sts, dr):
        parser.set_defaults(func=dispatch_manybody)
    p.set_defaults(func=dispatch_manybody)
    return p


def _run(args) -> dict[str, Any]:
    from . import (certify_remainder, check_frequency_integral, verify_langreth,
                   verify_matsubara_sum, verify_operator_identity)
    cmd = args.manybody_command
    if cmd == "matsubara":
        return verify_matsubara_sum(
            _expr(args.summand), _expr(args.claim), variable=args.variable,
            beta=args.beta, statistics=args.statistics, convergence=args.convergence,
            symbols=_symbols(args.symbols), declared_rules=_names(args.rules),
            positive=_names(args.positive)).to_dict()
    if cmd == "remainder":
        return certify_remainder(
            _expr(args.function), _expr(args.approximant), variable=args.variable,
            point=args.point, order=args.order, direction=args.direction,
            symbols=_symbols(args.symbols), positive=_names(args.positive)).to_dict()
    if cmd == "integral":
        return check_frequency_integral(
            _expr(args.integrand), _expr(args.claim), variable=args.variable,
            symbols=_symbols(args.symbols), beta=args.beta, prefactor=args.prefactor,
            positive=_names(args.positive))
    if cmd == "step":
        from .cards import run_card
        return run_card(args.card, require_source=args.require_source or None)
    if cmd == "draft":
        from .draft import draft
        return draft(args.document, args.out)
    if cmd == "steps":
        from .batch import run_cards, to_html
        report = run_cards(args.paths, require_source=args.require_source or None)
        if args.html:
            Path(args.html).write_text(to_html(report), encoding="utf-8")
            report = {**report, "html": args.html}
        return report
    if cmd == "identity":
        from .calculus import verify_identity
        return verify_identity(_expr(args.lhs), _expr(args.rhs), symbols=_symbols(args.symbols),
                               functions=_names(args.functions), positive=_names(args.positive))
    if cmd == "coefficient":
        from .calculus import verify_series_coefficient
        return verify_series_coefficient(
            _expr(args.expr), _expr(args.claim), variable=args.variable, order=args.order,
            symbols=_symbols(args.symbols), functions=_names(args.functions),
            positive=_names(args.positive))
    if cmd == "operator":
        return dict(verify_operator_identity(
            _expr(args.lhs), _expr(args.rhs), operators=_names(args.operators),
            scalars=_names(args.scalars), hermitian=_names(args.hermitian)))
    return dict(verify_langreth(_names(args.product), args.component, _expr(args.claim)))


def dispatch_manybody(args) -> int:
    try:
        payload = _run(args)
    except (OSError, ValueError, yaml.YAMLError) as exc:  # CardError is a ValueError
        print(json.dumps({"error": {"code": "MANYBODY_INPUT_INVALID", "detail": str(exc)[:300]}}))
        return EXIT_INPUT
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    return EXIT_OK
