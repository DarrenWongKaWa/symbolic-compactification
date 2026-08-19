"""Command-line interface for the symbolic compactification engine.

Subcommands
-----------
inspect        EXPR.txt [--symbols symbols.json] [--format native|wolfram]
               hash + symbols + ops + preview; ``--format wolfram`` translates
               Wolfram text (inspection only, no Wolfram runtime)
verify         --current A.txt --candidate B.txt --symbols symbols.json
init-session   [--workspace W] [--current A.txt --symbols symbols.json]
step           --run RUN_ID [--workspace W] --candidate B.txt --symbols symbols.json
               [--current A.txt]

Exit codes: 0 = ZERO, 2 = NONZERO, 3 = UNKNOWN, 4 = parse/load/usage error.

symbols.json accepts either ``{"symbols": [...]}`` or a bare JSON list. Each
entry is a name string (defaults real=True, nonzero=False) or a dict
``{"name": "a", "real": false, "nonzero": true}``.

Symbol inference (``inspect`` without --symbols) is INSPECTION ONLY: declared
symbols are guessed as every identifier in the text minus the whitelisted
functions/constants. Inference is never used for verification or session
steps, where an explicit declaration is mandatory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Optional

import sympy

from .models import (NONZERO, UNKNOWN, ZERO, AdapterError, StepRecord)
from .parser import get_parse_policy, load_expression
from .session import init_session, load_session, promote, record_step, set_current
from .verifier import verify_equivalent

EXIT_ZERO = 0
EXIT_NONZERO = 2
EXIT_UNKNOWN = 3
EXIT_ERROR = 4

_VERDICT_EXIT = {ZERO: EXIT_ZERO, NONZERO: EXIT_NONZERO, UNKNOWN: EXIT_UNKNOWN}

_CONSTANTS = {"pi", "E", "I", "oo"}
_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


# --------------------------------------------------------------------------- #
# symbols.json handling
# --------------------------------------------------------------------------- #

def load_symbols_file(path: str) -> list:
    """Parse symbols.json: ``{"symbols": [...]}`` or a bare JSON list."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise AdapterError("SYMBOLS_FILE_UNREADABLE") from None
    if isinstance(data, dict) and isinstance(data.get("symbols"), list):
        return data["symbols"]
    if isinstance(data, list):
        return data
    raise AdapterError("SYMBOLS_FILE_MALFORMED")


def infer_symbols(text: str) -> list[str]:
    """Inspection-only inference: identifiers minus whitelisted functions/consts."""
    allowed_fns = set(get_parse_policy()["allowed_functions"])
    names = _IDENTIFIER_RE.findall(text)
    seen: list[str] = []
    for n in names:
        if n not in allowed_fns and n not in _CONSTANTS and n not in seen:
            seen.append(n)
    return seen


# --------------------------------------------------------------------------- #
# output helpers
# --------------------------------------------------------------------------- #

def _print_result(result) -> None:
    print(f"verdict:             {result.verdict}")
    print(f"residual:            {result.residual}")
    print(f"simplified_residual: {result.simplified_residual}")
    print(f"evidence:            {json.dumps(result.evidence, ensure_ascii=False)}")
    if result.counterexample is not None:
        print(f"counterexample:      {json.dumps(result.counterexample, ensure_ascii=False)}")
    print(f"probes_tried:        {result.probes_tried}")
    print(f"verifier:            {result.verifier} ({result.seconds}s)")


# --------------------------------------------------------------------------- #
# subcommands
# --------------------------------------------------------------------------- #

def cmd_inspect(args) -> int:
    raw = Path(args.expr).read_bytes()  # raises OSError -> EXIT_ERROR upstream
    text = raw.decode("utf-8").strip()

    if args.format == "wolfram":
        return _inspect_wolfram(args, raw, text)

    inferred = False
    if args.symbols:
        declared = load_symbols_file(args.symbols)
    else:
        declared = infer_symbols(text)
        inferred = True
    parse_declared = declared if declared else ["_inspect_placeholder"]
    rec = load_expression(args.expr, parse_declared)
    print(f"file:        {args.expr}")
    print(f"sha256:      {rec.sha256}")
    if inferred:
        print(f"symbols:     {json.dumps(declared)}  (INFERRED - inspect only, "
              "identifiers minus allowed functions/constants)")
    else:
        print(f"symbols:     {json.dumps(rec.symbols, ensure_ascii=False)}")
    print(f"count_ops:   {sympy.count_ops(rec.parsed_expr, visual=False)}")
    preview = rec.text if len(rec.text) <= 200 else rec.text[:200] + " ..."
    print(f"preview:     {preview}")
    return EXIT_ZERO


def _inspect_wolfram(args, raw: bytes, text: str) -> int:
    """Translate Wolfram text then report. INSPECTION ONLY: the translated
    expression earns no verdict here; certification still requires the
    strict parser + exact verifier with explicit declarations."""
    from .adapters.wolfram_text import (extract_expression_text,
                                        translate_wolfram_text)
    if args.symbols:
        raise AdapterError("WOLFRAM_FORMAT_SYMBOLS_UNSUPPORTED")
    digest = hashlib.sha256(raw).hexdigest()
    source = extract_expression_text(text)
    result = translate_wolfram_text(source)
    print(f"file:        {args.expr}")
    print(f"format:      wolfram (translation only, no Wolfram runtime)")
    print(f"sha256:      {digest}")
    print(f"symbols:     {json.dumps(result.symbols, ensure_ascii=False)}  (DISCOVERED)")
    print(f"functions:   {json.dumps(result.functions)}")
    print(f"count_ops:   {sympy.count_ops(result.expr, visual=False)}")
    preview = result.text if len(result.text) <= 200 else result.text[:200] + " ..."
    print(f"translated:  {preview}")
    return EXIT_ZERO


def cmd_verify(args) -> int:
    declared = load_symbols_file(args.symbols)
    current = load_expression(args.current, declared)
    candidate = load_expression(args.candidate, declared)
    result = verify_equivalent(current.text, candidate.text, declared)
    print(f"current:   {args.current}  sha256={current.sha256}")
    print(f"candidate: {args.candidate}  sha256={candidate.sha256}")
    _print_result(result)
    return _VERDICT_EXIT[result.verdict]


def cmd_init_session(args) -> int:
    meta = {"cli": "init-session"}
    session = init_session(workspace_root=args.workspace, meta=meta)
    print(f"run_id:   {session.run_id}")
    print(f"run_root: {session.run_root}")
    if args.current:
        if not args.symbols:
            raise AdapterError("SYMBOLS_REQUIRED_WITH_CURRENT")
        declared = load_symbols_file(args.symbols)
        rec = load_expression(args.current, declared)
        set_current(session, rec, meta=meta)
        print(f"current:  {args.current}  sha256={rec.sha256}")
    else:
        print("current:  (none)")
    return EXIT_ZERO


def cmd_step(args) -> int:
    declared = load_symbols_file(args.symbols)
    session = load_session(args.workspace, args.run)

    if args.current:
        current = load_expression(args.current, declared)
    elif session.current is not None:
        current = session.current
    else:
        raise AdapterError("NO_CURRENT_EXPRESSION")
    candidate = load_expression(args.candidate, declared)

    result = verify_equivalent(current.text, candidate.text, declared)
    step = StepRecord(
        step=len(session.steps) + 1,
        current_hash=current.sha256,
        candidate_hash=candidate.sha256,
        candidate_text=candidate.text,
        residual=result.simplified_residual or result.residual,
        verdict=result.verdict,
        evidence=result.evidence,
    )
    step_path = record_step(session, step, meta={"cli": "step"})
    print(f"run:       {session.run_id}")
    print(f"step_file: {step_path}")
    _print_result(result)
    if result.verdict == ZERO:
        final_path = promote(session, candidate, meta={"cli": "step"})
        print(f"promoted:  {final_path}")
    else:
        print("promoted:  (no promotion; verdict != ZERO)")
    return _VERDICT_EXIT[result.verdict]


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="symbolic-compactification",
        description="Strict symbolic ingestion, verification and session records.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_inspect = sub.add_parser("inspect", help="hash/parse a .txt expression file")
    p_inspect.add_argument("expr", help="expression .txt file (read-only)")
    p_inspect.add_argument("--symbols", help="symbols.json; omit to infer (inspect only)")
    p_inspect.add_argument("--format", choices=["native", "wolfram"], default="native",
                           help="input format; 'wolfram' translates Wolfram text "
                                "(inspection only, no Wolfram runtime)")
    p_inspect.set_defaults(func=cmd_inspect)

    p_verify = sub.add_parser("verify", help="verify current == candidate (residual)")
    p_verify.add_argument("--current", required=True)
    p_verify.add_argument("--candidate", required=True)
    p_verify.add_argument("--symbols", required=True)
    p_verify.set_defaults(func=cmd_verify)

    p_init = sub.add_parser("init-session", help="create a new run directory")
    p_init.add_argument("--workspace", default="workspace")
    p_init.add_argument("--current", help="optional initial expression .txt")
    p_init.add_argument("--symbols", help="required together with --current")
    p_init.set_defaults(func=cmd_init_session)

    p_step = sub.add_parser("step", help="one verify step recorded into a run")
    p_step.add_argument("--run", required=True, help="run-id of an existing run")
    p_step.add_argument("--workspace", default="workspace")
    p_step.add_argument("--current", help="override the session's current expression")
    p_step.add_argument("--candidate", required=True)
    p_step.add_argument("--symbols", required=True)
    p_step.set_defaults(func=cmd_step)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except AdapterError as exc:
        _eprint(f"error: {exc.code}")
        return EXIT_ERROR
    except (OSError, UnicodeDecodeError):
        _eprint("error: EXPRESSION_SOURCE_UNREADABLE")
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
