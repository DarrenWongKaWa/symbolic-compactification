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
finalize       --run RUN_ID [--workspace W]
               render the FINAL CERTIFIED FORM deliverable (human-readable
               certified expression + definitions + provenance header) and
               write final/FINAL_CERTIFIED_FORM.md

Exit codes: 0 = ZERO, 2 = NONZERO, 3 = UNKNOWN, 4 = parse/load/usage error.

symbols.json accepts either ``{"symbols": [...]}`` or a bare JSON list. Each
entry is a name string (defaults real=True, nonzero=False) or a dict
``{"name": "a", "real": false, "nonzero": true}``. Optionally a
``"functions": [...]`` key declares the undefined-function namespace
(indexed calls such as ``f(n)``); it is backward-compatible and defaults to
empty. Namespace precedence: explicit declaration beats built-in (see the
parser module docstring); reserved-name rejection applies to undeclared
collisions.

Symbol inference (``inspect`` without --symbols) is INSPECTION ONLY: declared
symbols are guessed as every identifier in the text minus the whitelisted
functions/constants. Inference is never used for verification or session
steps, where an explicit declaration is mandatory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Optional

import sympy

from .models import (AGENT_PROTOCOL_VERSION, ENGINE_VERSION, PACKAGE_VERSION,
                     NONZERO, UNKNOWN, ZERO, AdapterError)
from .parser import infer_namespace, load_expression
from .pipeline import adjudicate_candidate
from .session import init_session, load_session, set_current
from .verifier import verify_equivalent

EXIT_ZERO = 0
EXIT_NONZERO = 2
EXIT_UNKNOWN = 3
EXIT_ERROR = 4

_VERDICT_EXIT = {ZERO: EXIT_ZERO, NONZERO: EXIT_NONZERO, UNKNOWN: EXIT_UNKNOWN}

def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


# --------------------------------------------------------------------------- #
# symbols.json handling
# --------------------------------------------------------------------------- #

def load_symbols_file(path: str) -> list:
    """Parse symbols.json: ``{"symbols": [...]}`` or a bare JSON list.

    Returns the symbol declaration list only. For the optional
    declared-function namespace use ``load_namespace_file``.
    """
    return load_namespace_file(path)[0]


def load_namespace_file(path: str) -> tuple[list, list]:
    """Parse symbols.json into ``(symbols, functions)``.

    Accepted forms (all backward compatible):
      * bare JSON list                    -> (list, [])
      * ``{"symbols": [...]}``            -> (symbols, [])
      * ``{"symbols": [...], "functions": [...]}`` -> both namespaces

    ``functions`` is the declared-function namespace (indexed calls
    such as ``f(n)``); it is optional and defaults to empty.
    """
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise AdapterError("SYMBOLS_FILE_UNREADABLE") from None
    functions: list = []
    if isinstance(data, dict):
        if "functions" in data:
            if not isinstance(data["functions"], list):
                raise AdapterError("SYMBOLS_FILE_MALFORMED")
            functions = data["functions"]
        if isinstance(data.get("symbols"), list):
            return data["symbols"], functions
        raise AdapterError("SYMBOLS_FILE_MALFORMED")
    if isinstance(data, list):
        return data, []
    raise AdapterError("SYMBOLS_FILE_MALFORMED")


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


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, sort_keys=True, ensure_ascii=False))


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
        declared, functions = load_namespace_file(args.symbols)
    else:
        declared, functions = infer_namespace(text)
        inferred = True
    parse_declared = declared if declared else ["_inspect_placeholder"]
    rec = load_expression(args.expr, parse_declared, functions=functions or None)
    preview = rec.text if len(rec.text) <= 200 else rec.text[:200] + " ..."
    if args.json:
        _print_json({
            "file": args.expr,
            "format": "native",
            "sha256": rec.sha256,
            "symbols": rec.symbols if not inferred else declared,
            "functions": functions,
            "inferred": inferred,
            "count_ops": int(sympy.count_ops(rec.parsed_expr, visual=False)),
            "preview": preview,
        })
        return EXIT_ZERO
    print(f"file:        {args.expr}")
    print(f"sha256:      {rec.sha256}")
    if inferred:
        print(f"symbols:     {json.dumps(declared)}  (INFERRED - inspect only, "
              "identifiers minus allowed functions/constants)")
    else:
        print(f"symbols:     {json.dumps(rec.symbols, ensure_ascii=False)}")
    if functions:
        print(f"functions:   {json.dumps(functions)}")
    print(f"count_ops:   {sympy.count_ops(rec.parsed_expr, visual=False)}")
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
    preview = result.text if len(result.text) <= 200 else result.text[:200] + " ..."
    if args.json:
        _print_json({
            "file": args.expr,
            "format": "wolfram",
            "sha256": digest,
            "symbols": result.symbols,
            "functions": result.functions,
            "bound_symbols": result.bound_symbols,
            "count_ops": int(sympy.count_ops(result.expr, visual=False)),
            "translated": preview,
        })
        return EXIT_ZERO
    print(f"file:        {args.expr}")
    print(f"format:      wolfram (translation only, no Wolfram runtime)")
    print(f"sha256:      {digest}")
    print(f"symbols:     {json.dumps(result.symbols, ensure_ascii=False)}  (DISCOVERED)")
    print(f"functions:   {json.dumps(result.functions)}")
    print(f"bound:       {json.dumps(result.bound_symbols)}  (Sum/Product dummy indices; declare them for re-parsing)")
    print(f"count_ops:   {sympy.count_ops(result.expr, visual=False)}")
    print(f"translated:  {preview}")
    return EXIT_ZERO


def cmd_verify(args) -> int:
    declared, functions = load_namespace_file(args.symbols)
    fns = functions or None
    current = load_expression(args.current, declared, functions=fns)
    candidate = load_expression(args.candidate, declared, functions=fns)
    result = verify_equivalent(current.text, candidate.text, declared,
                               functions=fns)
    if args.json:
        _print_json({
            "current": {"path": args.current, "sha256": current.sha256},
            "candidate": {"path": args.candidate,
                          "sha256": candidate.sha256},
            "result": result.to_dict(),
        })
        return _VERDICT_EXIT[result.verdict]
    print(f"current:   {args.current}  sha256={current.sha256}")
    print(f"candidate: {args.candidate}  sha256={candidate.sha256}")
    _print_result(result)
    return _VERDICT_EXIT[result.verdict]


def cmd_init_session(args) -> int:
    meta = {"cli": "init-session"}
    session = init_session(workspace_root=args.workspace, meta=meta,
                           requested_arm=args.requested_arm)
    arm = getattr(session, "requested_arm", None)
    current_payload = None
    if args.current:
        if not args.symbols:
            raise AdapterError("SYMBOLS_REQUIRED_WITH_CURRENT")
        declared, functions = load_namespace_file(args.symbols)
        rec = load_expression(args.current, declared,
                              functions=functions or None)
        set_current(session, rec, meta=meta)
        current_payload = {"path": args.current, "sha256": rec.sha256}
    if args.json:
        _print_json({"run_id": session.run_id, "run_root": session.run_root,
                     "requested_arm": arm, "current": current_payload})
        return EXIT_ZERO
    print(f"run_id:   {session.run_id}")
    print(f"run_root: {session.run_root}")
    print(f"arm:      {arm if arm is not None else '(undeclared)'}")
    if current_payload:
        print(f"current:  {args.current}  sha256={rec.sha256}")
    else:
        print("current:  (none)")
    return EXIT_ZERO


def cmd_step(args) -> int:
    declared, functions = load_namespace_file(args.symbols)
    fns = functions or None
    session = load_session(args.workspace, args.run)

    if args.current:
        current = load_expression(args.current, declared, functions=fns)
        if session.current is None:
            set_current(session, current, meta={"cli": "step-initial-current"})
        elif (current.sha256 != session.current.sha256
              or current.text != session.current.text
              or current.symbols != session.current.symbols
              or current.functions != session.current.functions):
            raise AdapterError("CURRENT_STATE_MISMATCH")
        else:
            # Same persisted bytes/namespace, now with a hydrated AST for
            # structural telemetry. This is not a state transition.
            session.current = current
    elif session.current is not None:
        current = session.current
    else:
        raise AdapterError("NO_CURRENT_EXPRESSION")
    candidate = load_expression(args.candidate, declared, functions=fns)

    outcome = adjudicate_candidate(session, candidate, meta={"cli": "step"})
    result = outcome.result
    if args.json:
        _print_json({
            "run_id": session.run_id,
            "step_file": str(outcome.step_path),
            "promoted": outcome.promoted,
            "promoted_path": (str(outcome.promoted_path)
                              if outcome.promoted_path else None),
            "result": result.to_dict(),
        })
        return _VERDICT_EXIT[result.verdict]
    print(f"run:       {session.run_id}")
    print(f"step_file: {outcome.step_path}")
    _print_result(result)
    if outcome.promoted:
        print(f"promoted:  {outcome.promoted_path}")
    else:
        print("promoted:  (no promotion; verdict != ZERO)")
    return _VERDICT_EXIT[result.verdict]


def cmd_finalize(args) -> int:
    """Render the FINAL CERTIFIED FORM deliverable for a run.

    Prints the explicit certified top-level expression (plus every
    abbreviation definition) and the artifact path, and writes
    ``final/FINAL_CERTIFIED_FORM.md`` with the provenance header. The
    internal ``final/current.json`` is provenance, NOT the deliverable.
    """
    from .reporting import render_final_report
    session = load_session(args.workspace, args.run)
    report = render_final_report(session)
    if args.json:
        _print_json(report)
        return EXIT_ZERO
    print("FINAL CERTIFIED FORM")
    print("=" * 20)
    print(f"run_id:     {report['run_id']}")
    print(f"certified:  {report['certified_state_sha256']}")
    print()
    print("certified expression (top-level, human form):")
    print(f"  {report['human_form']}")
    if report["definitions"]:
        print()
        print("definitions:")
        for name in sorted(report["definitions"]):
            print(f"  {name} := {report['definitions'][name]}")
    print()
    print(f"expansion_check: {report['expansion_check']}")
    print(f"artifact:        {report['artifact_path']}")
    print("note: internal final/current.json is provenance, not the deliverable")
    return EXIT_ZERO


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="symbolic-compactification",
        description="Strict symbolic ingestion, verification and session records.")
    parser.add_argument(
        "--version", action="version",
        version=(f"%(prog)s {PACKAGE_VERSION} "
                 f"(engine {ENGINE_VERSION}, protocol {AGENT_PROTOCOL_VERSION})"))
    sub = parser.add_subparsers(dest="command", required=True)

    p_inspect = sub.add_parser("inspect", help="hash/parse a .txt expression file")
    p_inspect.add_argument("expr", help="expression .txt file (read-only)")
    p_inspect.add_argument("--symbols", help="symbols.json; omit to infer (inspect only)")
    p_inspect.add_argument("--format", choices=["native", "wolfram"], default="native",
                           help="input format; 'wolfram' translates Wolfram text "
                                "(inspection only, no Wolfram runtime)")
    p_inspect.add_argument("--json", action="store_true",
                           help="emit one machine-readable JSON object")
    p_inspect.set_defaults(func=cmd_inspect)

    p_verify = sub.add_parser("verify", help="verify current == candidate (residual)")
    p_verify.add_argument("--current", required=True)
    p_verify.add_argument("--candidate", required=True)
    p_verify.add_argument("--symbols", required=True)
    p_verify.add_argument("--json", action="store_true",
                          help="emit one machine-readable JSON object")
    p_verify.set_defaults(func=cmd_verify)

    p_init = sub.add_parser("init-session", help="create a new run directory")
    p_init.add_argument("--workspace", default="workspace")
    p_init.add_argument("--current", help="optional initial expression .txt")
    p_init.add_argument("--symbols", help="required together with --current")
    p_init.add_argument("--requested-arm", default=None, dest="requested_arm",
                        choices=[None, "A", "a", "B", "b"],
                        help="optional declared A/B experiment arm (A or B)")
    p_init.add_argument("--json", action="store_true",
                        help="emit one machine-readable JSON object")
    p_init.set_defaults(func=cmd_init_session)

    p_step = sub.add_parser("step", help="one verify step recorded into a run")
    p_step.add_argument("--run", required=True, help="run-id of an existing run")
    p_step.add_argument("--workspace", default="workspace")
    p_step.add_argument("--current", help="override the session's current expression")
    p_step.add_argument("--candidate", required=True)
    p_step.add_argument("--symbols", required=True)
    p_step.add_argument("--json", action="store_true",
                        help="emit one machine-readable JSON object")
    p_step.set_defaults(func=cmd_step)

    p_finalize = sub.add_parser(
        "finalize", help="render the FINAL CERTIFIED FORM deliverable")
    p_finalize.add_argument("--run", required=True,
                            help="run-id of an existing run")
    p_finalize.add_argument("--workspace", default="workspace")
    p_finalize.add_argument("--json", action="store_true",
                            help="emit one machine-readable JSON object")
    p_finalize.set_defaults(func=cmd_finalize)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        try:
            return args.func(args)
        except AdapterError as exc:
            _eprint(f"error: {exc.code}")
            return EXIT_ERROR
        except (OSError, UnicodeDecodeError):
            _eprint("error: EXPRESSION_SOURCE_UNREADABLE")
            return EXIT_ERROR
    finally:
        # Owned child-process hygiene: sweep any engine-owned budget workers
        # on EVERY CLI exit path (success, verdict, error, interrupt). The
        # budgets module also registers an atexit sweep as a backstop.
        from .budgets import sweep_owned_children
        sweep_owned_children()


if __name__ == "__main__":
    sys.exit(main())
