"""Command-line interface for the symbolic compactification engine.

Subcommands
-----------
init           WORKSPACE
               create a minimal external researcher workspace
inspect        WORKSPACE
               inspect project metadata, assumptions, expressions and structure
inspect        EXPR.txt [--symbols symbols.json] [--format native|wolfram]
               hash + symbols + ops + preview; ``--format wolfram`` translates
               Wolfram text (inspection only, no Wolfram runtime)
verify         WORKSPACE
               compile and verify the workspace hypothesis, recording provenance
verify         --current A.txt --candidate B.txt --symbols symbols.json
report         WORKSPACE [--run RUN_ID]
               render a recorded workspace run (latest safe run by default)
init-session   [--workspace W] [--current A.txt --symbols symbols.json]
               [--proposer-mode main|subagent|auto]
step           --run RUN_ID [--workspace W] --candidate B.txt --symbols symbols.json
               [--current A.txt]
summary        --run RUN_ID [--workspace W]
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
import re
import sys
from pathlib import Path
from typing import Optional

import sympy

from .models import (AGENT_PROTOCOL_VERSION, ENGINE_VERSION, PACKAGE_VERSION,
                     NONZERO, UNKNOWN, ZERO, AdapterError)
from .parser import infer_namespace, load_expression
from .pipeline import adjudicate_candidate
from .provenance import ProvenanceError
from .research_api import (COMPILE_FAILURE, PARSE_FAILURE, PUBLIC_RESULTS,
                           RESULT_SCHEMA_VERSION, generate_report,
                           verify_hypothesis)
from .security import redact_public_data, redact_text
from .session import init_session, load_session, run_summary, set_current
from .structure import structure_summary
from .verifier import verify_equivalent
from .workspace import (ResearchWorkspace, WorkspaceError,
                        initialize_workspace, load_workspace)

EXIT_ZERO = 0
EXIT_NONZERO = 2
EXIT_UNKNOWN = 3
EXIT_ERROR = 4

_VERDICT_EXIT = {ZERO: EXIT_ZERO, NONZERO: EXIT_NONZERO, UNKNOWN: EXIT_UNKNOWN}
_WORKSPACE_RESULT_EXIT = {
    **_VERDICT_EXIT,
    PARSE_FAILURE: EXIT_ERROR,
    COMPILE_FAILURE: EXIT_ERROR,
}
_SAFE_RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_UTC_TIMESTAMP_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
_MAX_RUN_METADATA_BYTES = 1_048_576

def _eprint(msg: str) -> None:
    print(redact_text(msg), file=sys.stderr)


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
    print(f"residual:            {redact_text(str(result.residual))}")
    print("simplified_residual: "
          f"{redact_text(str(result.simplified_residual))}")
    print("evidence:            " + json.dumps(
        redact_public_data(result.evidence), ensure_ascii=False))
    if result.counterexample is not None:
        print("counterexample:      " + json.dumps(
            redact_public_data(result.counterexample), ensure_ascii=False))
    print(f"probes_tried:        {result.probes_tried}")
    print(f"verifier:            {result.verifier} ({result.seconds}s)")


def _print_json(payload: dict) -> None:
    print(json.dumps(
        redact_public_data(payload), sort_keys=True, ensure_ascii=False))


def _preview(text: str, limit: int = 200) -> str:
    return text if len(text) <= limit else text[:limit] + " ..."


def _workspace_expression_payload(
        workspace: ResearchWorkspace, record) -> dict:
    """Return a readable, JSON-native inspection view of one expression."""
    try:
        relative_path = Path(record.source_path).relative_to(
            workspace.root).as_posix()
    except (TypeError, ValueError):
        raise WorkspaceError(
            "WORKSPACE_STATE_INVALID",
            "a loaded expression is not owned by the workspace",
            path=workspace.root,
        ) from None
    parsed = str(record.parsed_expr)
    return {
        "path": relative_path,
        "entrypoint": relative_path == workspace.project.expression_entrypoint,
        "sha256": record.sha256,
        "text": record.text,
        "text_summary": {
            "characters": len(record.text),
            "preview": _preview(record.text),
        },
        "parsed_expression": parsed,
        "count_ops": int(sympy.count_ops(record.parsed_expr, visual=False)),
        "structure_summary": structure_summary(record.parsed_expr),
    }


def _workspace_inspection_payload(workspace: ResearchWorkspace) -> dict:
    return {
        "workspace": str(workspace.root),
        "project": workspace.project.to_dict(),
        "assumptions": {
            "symbols": list(workspace.symbols),
            "functions": list(workspace.functions),
            "sha256": workspace.assumptions_source.sha256,
        },
        "hypothesis": {
            **workspace.hypothesis.to_dict(),
            "sha256": workspace.hypothesis_source.sha256,
            "normalized_simple_form": (
                workspace.hypothesis.normalized_simple_form),
        },
        "expressions": [
            _workspace_expression_payload(workspace, record)
            for record in workspace.expressions
        ],
        "notes": [
            {
                "path": source.relative_path,
                "sha256": source.sha256,
                "size_bytes": source.size_bytes,
            }
            for source in workspace.notes
        ],
        "references": [
            {
                "path": source.relative_path,
                "sha256": source.sha256,
                "size_bytes": source.size_bytes,
            }
            for source in workspace.references
        ],
    }


def _print_workspace_inspection(payload: dict) -> None:
    safe = redact_public_data(payload)
    project = safe["project"]
    assumptions = safe["assumptions"]
    hypothesis = safe["hypothesis"]
    print(f"workspace:   {safe['workspace']}")
    print(f"project:     {project['project_name']}")
    print(f"objective:   {project['objective']}")
    print(f"entrypoint:  {project['expression_entrypoint']}")
    print(f"symbols:     {json.dumps(assumptions['symbols'], ensure_ascii=False)}")
    print(f"functions:   {json.dumps(assumptions['functions'], ensure_ascii=False)}")
    print(f"hypothesis:  {hypothesis['hypothesis_type']}")
    print(f"obligations: {len(hypothesis['proof_obligations'])}")
    print("expressions:")
    for expression in safe["expressions"]:
        marker = " (entrypoint)" if expression["entrypoint"] else ""
        print(f"  - {expression['path']}{marker}")
        print(f"    sha256:    {expression['sha256']}")
        print(f"    text:      {json.dumps(expression['text'], ensure_ascii=False)}")
        print(f"    parsed:    {expression['parsed_expression']}")
        print(f"    count_ops: {expression['count_ops']}")
        print("    structure: " + json.dumps(
            expression["structure_summary"], ensure_ascii=False))
    if safe["notes"]:
        print("notes:       " + ", ".join(
            item["path"] for item in safe["notes"]))
    if safe["references"]:
        print("references:  " + ", ".join(
            item["path"] for item in safe["references"]))


def _workspace_result_explanation(result: str) -> str:
    return {
        ZERO: (
            "every declared obligation was exactly certified under the "
            "declared engine semantics and assumptions"
        ),
        NONZERO: (
            "at least one declared obligation was refuted by the exact "
            "verification route"
        ),
        UNKNOWN: (
            "the system could not decide at least one obligation; this is "
            "not success and does not permit scientific promotion"
        ),
        PARSE_FAILURE: (
            "workspace metadata or a declared input could not be validated; "
            "no scientific relation was checked"
        ),
        COMPILE_FAILURE: (
            "the hypothesis is outside the supported v0.1 obligation "
            "language; no scientific relation was checked"
        ),
    }.get(result, "the run returned an unsupported fail-closed status")


def _safe_json_object(path: Path) -> Optional[dict]:
    """Read bounded run metadata without following a final-component symlink."""
    try:
        if path.is_symlink() or not path.is_file():
            return None
        if path.stat().st_size > _MAX_RUN_METADATA_BYTES:
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _latest_safe_run_id(workspace_path: str) -> str:
    """Select the latest valid research-API run by persisted UTC timestamp."""
    requested = Path(workspace_path)
    try:
        root = requested.resolve(strict=True)
    except OSError:
        raise WorkspaceError(
            "WORKSPACE_NOT_FOUND", "workspace directory does not exist",
            path=requested) from None
    if not root.is_dir():
        raise WorkspaceError(
            "WORKSPACE_NOT_DIRECTORY", "workspace path is not a directory",
            path=root)
    runs = root / "runs"
    if runs.is_symlink() or not runs.is_dir():
        raise WorkspaceError(
            "RUNS_DIRECTORY_UNSAFE",
            "runs must be a real directory inside the workspace",
            path=runs,
        )

    candidates: list[tuple[str, int, str]] = []
    try:
        children = tuple(runs.iterdir())
    except OSError:
        raise WorkspaceError(
            "RUNS_DIRECTORY_UNREADABLE", "runs directory is not readable",
            path=runs) from None
    for run_directory in children:
        if (run_directory.is_symlink() or not run_directory.is_dir()
                or not _SAFE_RUN_ID_RE.fullmatch(run_directory.name)):
            continue
        provenance_path = run_directory / "provenance.json"
        provenance = _safe_json_object(provenance_path)
        result = _safe_json_object(run_directory / "result.json")
        if provenance is None or result is None:
            continue
        timestamp = provenance.get("timestamp")
        status = result.get("result")
        if (not isinstance(timestamp, str)
                or not _UTC_TIMESTAMP_RE.fullmatch(timestamp)
                or status not in PUBLIC_RESULTS
                or result.get("schema_version") != RESULT_SCHEMA_VERSION
                or provenance.get("run_id") != run_directory.name
                or result.get("run_id") != run_directory.name
                or provenance.get("result") != status):
            continue
        try:
            provenance_mtime = provenance_path.stat().st_mtime_ns
        except OSError:
            continue
        candidates.append((timestamp, provenance_mtime, run_directory.name))
    if not candidates:
        raise WorkspaceError(
            "NO_RECORDED_RUNS",
            "run 'symbolic-compactification verify <workspace>' first",
            path=runs,
        )
    return max(candidates)[2]


# --------------------------------------------------------------------------- #
# subcommands
# --------------------------------------------------------------------------- #

def cmd_init_workspace(args) -> int:
    workspace = initialize_workspace(args.workspace)
    payload = {
        "status": "WORKSPACE_INITIALIZED",
        "workspace": str(workspace.root),
        "project": workspace.project.to_dict(),
        "hypothesis_path": str(workspace.hypothesis_source.absolute_path),
        "next_command": f"symbolic-compactification inspect {workspace.root}",
    }
    if args.json:
        _print_json(payload)
        return EXIT_ZERO
    print("status:      WORKSPACE_INITIALIZED")
    print(f"workspace:   {redact_text(str(workspace.root))}")
    print("entrypoint:  "
          f"{redact_text(workspace.project.expression_entrypoint)}")
    print("hypothesis:  "
          f"{redact_text(workspace.hypothesis_source.relative_path)}")
    print(f"next:        {redact_text(payload['next_command'])}")
    return EXIT_ZERO

def cmd_inspect(args) -> int:
    target = Path(args.expr)
    if target.is_dir():
        if args.symbols or args.format != "native":
            raise WorkspaceError(
                "WORKSPACE_INSPECT_OPTIONS_UNSUPPORTED",
                "workspace inspection uses its declared assumptions and "
                "native expression format",
                path=target,
            )
        payload = _workspace_inspection_payload(load_workspace(target))
        if args.json:
            _print_json(payload)
        else:
            _print_workspace_inspection(payload)
        return EXIT_ZERO

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
    preview = _preview(rec.text)
    summary = structure_summary(rec.parsed_expr)
    if args.json:
        _print_json({
            "file": args.expr,
            "format": "native",
            "sha256": rec.sha256,
            "symbols": rec.symbols if not inferred else declared,
            "functions": functions,
            "inferred": inferred,
            "count_ops": int(sympy.count_ops(rec.parsed_expr, visual=False)),
            "structure_summary": summary,
            "text": rec.text,
            "preview": preview,
        })
        return EXIT_ZERO
    print(f"file:        {redact_text(str(args.expr))}")
    print(f"sha256:      {rec.sha256}")
    if inferred:
        print("symbols:     "
              f"{json.dumps(redact_public_data(declared))}  "
              "(INFERRED - inspect only, "
              "identifiers minus allowed functions/constants)")
    else:
        print("symbols:     " + json.dumps(
            redact_public_data(rec.symbols), ensure_ascii=False))
    if functions:
        print("functions:   " + json.dumps(redact_public_data(functions)))
    print(f"count_ops:   {sympy.count_ops(rec.parsed_expr, visual=False)}")
    print("structure:   " + json.dumps(
        redact_public_data(summary), ensure_ascii=False))
    print(f"preview:     {redact_text(preview)}")
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
    preview = _preview(result.text)
    summary = structure_summary(result.expr)
    if args.json:
        _print_json({
            "file": args.expr,
            "format": "wolfram",
            "sha256": digest,
            "symbols": result.symbols,
            "functions": result.functions,
            "bound_symbols": result.bound_symbols,
            "count_ops": int(sympy.count_ops(result.expr, visual=False)),
            "structure_summary": summary,
            "text": result.text,
            "translated": result.text,
            "preview": preview,
        })
        return EXIT_ZERO
    print(f"file:        {redact_text(str(args.expr))}")
    print(f"format:      wolfram (translation only, no Wolfram runtime)")
    print(f"sha256:      {digest}")
    print("symbols:     " + json.dumps(
        redact_public_data(result.symbols), ensure_ascii=False)
        + "  (DISCOVERED)")
    print("functions:   " + json.dumps(
        redact_public_data(result.functions)))
    print("bound:       " + json.dumps(
        redact_public_data(result.bound_symbols))
        + "  (Sum/Product dummy indices; declare them for re-parsing)")
    print(f"count_ops:   {sympy.count_ops(result.expr, visual=False)}")
    print("structure:   " + json.dumps(
        redact_public_data(summary), ensure_ascii=False))
    print(f"translated:  {redact_text(preview)}")
    return EXIT_ZERO


def cmd_observe(args) -> int:
    from .observations.api import observe
    from .parser import infer_namespace
    path = Path(args.expr)
    text = path.read_text()
    if args.symbols:
        declared, functions = load_namespace_file(args.symbols)
    else:
        declared, functions = infer_namespace(text)
    spec = args.preset or args.backend
    if isinstance(spec, str) and "," in spec:
        spec = [s.strip() for s in spec.split(",") if s.strip()]
    bundle = observe(text, declared, functions, backends=spec)
    payload = redact_public_data(bundle.to_dict())
    print(json.dumps(payload, indent=2, default=str))
    if args.graph:
        Path(args.graph).write_text(json.dumps({
            "nodes": payload["nodes"],
            "relations": payload["relations"],
            "families": payload["families"],
        }, indent=2, default=str) + "\n")
    return EXIT_ZERO


def cmd_backends(args) -> int:
    from .observations.discovery import backend_status, FUTURE_ABSTRACTION
    st = backend_status()
    extra = {n: "FUTURE_ABSTRACTION_BACKEND" for n in FUTURE_ABSTRACTION}
    if args.json:
        _print_json({**st, **extra})
        return EXIT_ZERO
    width = max(len(k) for k in list(st) + list(extra))
    for k, v in {**st, **extra}.items():
        print(f"{k:<{width}}  {v}")
    return EXIT_ZERO


def cmd_verify(args) -> int:
    workspace_path = getattr(args, "workspace", None)
    legacy_values = (args.current, args.candidate, args.symbols)
    if workspace_path is not None:
        if any(value is not None for value in legacy_values):
            raise AdapterError("VERIFY_MODES_MIXED")
        result = verify_hypothesis(workspace_path)
        if args.json:
            _print_json(result.to_dict())
        else:
            _print_workspace_verification(workspace_path, result)
        return _WORKSPACE_RESULT_EXIT.get(result.result, EXIT_ERROR)

    if not all(value is not None for value in legacy_values):
        raise AdapterError("VERIFY_INPUTS_REQUIRED")
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
    print(f"current:   {redact_text(str(args.current))}  sha256={current.sha256}")
    print("candidate: "
          f"{redact_text(str(args.candidate))}  sha256={candidate.sha256}")
    _print_result(result)
    return _VERDICT_EXIT[result.verdict]


def _print_workspace_verification(workspace_path: str, result) -> None:
    print(f"workspace:   {redact_text(str(Path(workspace_path).resolve()))}")
    print(f"run_id:      {redact_text(result.run_id)}")
    print(f"result:      {result.result}")
    print(f"semantics:   {_workspace_result_explanation(result.result)}")
    if result.error_code:
        print(f"error_code:  {redact_text(result.error_code)}")
        print("action:      correct the declared workspace or hypothesis and retry")
    for obligation in result.obligations:
        print("obligation:  "
              f"{redact_text(obligation.obligation_id)} -> {obligation.verdict}")
        print(f"  left:      {redact_text(obligation.left)}")
        print(f"  right:     {redact_text(obligation.right)}")
        print("  residual:  "
              f"{redact_text(str(obligation.result.residual))}")
        if obligation.result.counterexample is not None:
            print("  exact counterexample: " + json.dumps(
                redact_public_data(obligation.result.counterexample),
                sort_keys=True,
                ensure_ascii=False,
            ))
    print(f"provenance:  {redact_text(str(result.provenance_path))}")
    print(f"report:      {redact_text(str(result.report_path))}")


def cmd_report(args) -> int:
    run_id = args.run or _latest_safe_run_id(args.workspace)
    report = generate_report(args.workspace, run_id)
    if args.json:
        _print_json(report.to_dict())
        return EXIT_ZERO
    # The report itself owns the provenance-rich human-readable content.
    safe_text = redact_text(report.text)
    print(safe_text, end="" if safe_text.endswith("\n") else "\n")
    print(f"artifact: {redact_text(str(report.path))}")
    return EXIT_ZERO


def cmd_init_session(args) -> int:
    meta = {"cli": "init-session"}
    session = init_session(
        workspace_root=args.workspace, meta=meta,
        requested_arm=args.requested_arm,
        requested_proposer_mode=getattr(args, "proposer_mode", None))
    arm = getattr(session, "requested_arm", None)
    proposer_mode = getattr(session, "requested_proposer_mode", None)
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
                     "requested_arm": arm,
                     "requested_proposer_mode": proposer_mode,
                     "current": current_payload})
        return EXIT_ZERO
    print(f"run_id:   {redact_text(session.run_id)}")
    print(f"run_root: {redact_text(str(session.run_root))}")
    print(f"arm:      {arm if arm is not None else '(undeclared)'}")
    print(f"proposer: {proposer_mode if proposer_mode is not None else '(undeclared)'}")
    if current_payload:
        print(f"current:  {redact_text(str(args.current))}  sha256={rec.sha256}")
    else:
        print("current:  (none)")
    return EXIT_ZERO


def cmd_summary(args) -> int:
    session = load_session(args.workspace, args.run)
    payload = run_summary(session.run_root)
    if args.json:
        _print_json(payload)
        return EXIT_ZERO
    print(f"run_id:                    {redact_text(str(payload['run_id']))}")
    print(f"requested_proposer_mode:   {payload['requested_proposer_mode']}")
    print(f"proposer_mode (evidence):  {payload['proposer_mode']}")
    print(f"zero_promotions:           {payload['zero_promotions']}")
    print(f"nonzero_count:             {payload['nonzero_count']}")
    print(f"unknown_count:             {payload['unknown_count']}")
    print(f"verifier_calls:            {payload['verifier_calls']}")
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
    print(f"run:       {redact_text(session.run_id)}")
    print(f"step_file: {redact_text(str(outcome.step_path))}")
    _print_result(result)
    if outcome.promoted:
        print(f"promoted:  {redact_text(str(outcome.promoted_path))}")
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
    print(f"run_id:     {redact_text(str(report['run_id']))}")
    print(f"certified:  {report['certified_state_sha256']}")
    print()
    print("certified expression (top-level, human form):")
    print(f"  {redact_text(str(report['human_form']))}")
    if report["definitions"]:
        print()
        print("definitions:")
        for name in sorted(report["definitions"]):
            print("  " + redact_text(str(name)) + " := "
                  + redact_text(str(report["definitions"][name])))
    print()
    print(f"expansion_check: {report['expansion_check']}")
    print("artifact:        "
          f"{redact_text(str(report['artifact_path']))}")
    print("note: internal final/current.json is provenance, not the deliverable")
    return EXIT_ZERO


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #

def _add_debug_argument(command_parser: argparse.ArgumentParser) -> None:
    command_parser.add_argument(
        "--debug",
        action="store_true",
        default=argparse.SUPPRESS,
        help="show developer tracebacks instead of concise user errors",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="symbolic-compactification",
        description=(
            "Context-grounded symbolic hypotheses with fail-closed exact "
            "verification."))
    parser.add_argument(
        "--version", action="version",
        version=(f"%(prog)s {PACKAGE_VERSION} "
                 f"(engine {ENGINE_VERSION}, protocol {AGENT_PROTOCOL_VERSION})"))
    parser.add_argument(
        "--debug", action="store_true",
        help="show developer tracebacks instead of concise user errors")
    sub = parser.add_subparsers(dest="command", required=True)

    p_workspace_init = sub.add_parser(
        "init", help="create a minimal external researcher workspace")
    p_workspace_init.add_argument(
        "workspace", help="new workspace directory (must not already exist)")
    p_workspace_init.add_argument(
        "--json", action="store_true",
        help="emit one machine-readable JSON object")
    p_workspace_init.set_defaults(func=cmd_init_workspace)

    p_inspect = sub.add_parser(
        "inspect", help="inspect a researcher workspace or expression file")
    p_inspect.add_argument(
        "expr", help="workspace directory or expression .txt file (read-only)")
    p_inspect.add_argument("--symbols", help="symbols.json; omit to infer (inspect only)")
    p_inspect.add_argument("--format", choices=["native", "wolfram"], default="native",
                           help="input format; 'wolfram' translates Wolfram text "
                                "(inspection only, no Wolfram runtime)")
    p_inspect.add_argument("--json", action="store_true",
                           help="emit one machine-readable JSON object")
    p_inspect.set_defaults(func=cmd_inspect)

    p_verify = sub.add_parser(
        "verify",
        help="verify a workspace hypothesis or legacy current/candidate pair")
    p_verify.add_argument(
        "workspace", nargs="?",
        help="researcher workspace (omit when using legacy file flags)")
    p_verify.add_argument("--current")
    p_verify.add_argument("--candidate")
    p_verify.add_argument("--symbols")
    p_verify.add_argument("--json", action="store_true",
                          help="emit one machine-readable JSON object")
    p_verify.set_defaults(func=cmd_verify)

    p_report = sub.add_parser(
        "report", help="show a provenance-rich workspace verification report")
    p_report.add_argument("workspace", help="researcher workspace")
    p_report.add_argument(
        "--run", help="recorded run id (default: latest safe research run)")
    p_report.add_argument("--json", action="store_true",
                          help="emit one machine-readable JSON object")
    p_report.set_defaults(func=cmd_report)

    p_init = sub.add_parser("init-session", help="create a new run directory")
    p_init.add_argument("--workspace", default="workspace")
    p_init.add_argument("--current", help="optional initial expression .txt")
    p_init.add_argument("--symbols", help="required together with --current")
    p_init.add_argument("--requested-arm", default=None, dest="requested_arm",
                        choices=[None, "A", "a", "B", "b"],
                        help="optional declared A/B experiment arm (A or B)")
    p_init.add_argument(
        "--proposer-mode", default=None, dest="proposer_mode",
        choices=["main", "subagent", "auto"],
        help="skill proposer intent (default undeclared = main)")
    p_init.add_argument("--json", action="store_true",
                        help="emit one machine-readable JSON object")
    p_init.set_defaults(func=cmd_init_session)

    p_summary = sub.add_parser(
        "summary", help="print run_summary counters for an existing run")
    p_summary.add_argument("--run", required=True)
    p_summary.add_argument("--workspace", default="workspace")
    p_summary.add_argument("--json", action="store_true",
                           help="emit one machine-readable JSON object")
    p_summary.set_defaults(func=cmd_summary)

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

    p_obs = sub.add_parser(
        "observe",
        help="read-only structural observation layer (no promotion)")
    p_obs.add_argument("expr", help="expression .txt")
    p_obs.add_argument("--symbols", help="symbols.json (inferred if omitted)")
    p_obs.add_argument("--backend", default="auto",
                       help="backend name, comma list, or preset")
    p_obs.add_argument("--preset", default=None,
                       help="minimal|algebra|relations|physics|all_available")
    p_obs.add_argument("--format", choices=["json"], default="json")
    p_obs.add_argument("--graph", default=None,
                       help="write relation graph JSON to this path")
    p_obs.set_defaults(func=cmd_observe)

    p_be = sub.add_parser("backends", help="list observation-backend status")
    p_be.add_argument("--json", action="store_true")
    p_be.set_defaults(func=cmd_backends)

    for command_parser in (
            p_workspace_init, p_inspect, p_verify, p_report, p_init,
            p_summary, p_step, p_finalize, p_obs, p_be):
        _add_debug_argument(command_parser)

    return parser


def _emit_cli_error(args, code: str) -> int:
    if getattr(args, "json", False):
        _print_json({"error": {"code": code}})
    else:
        _eprint(f"error: {code}")
    return EXIT_ERROR


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        try:
            return args.func(args)
        except AdapterError as exc:
            if args.debug:
                raise
            return _emit_cli_error(args, exc.code)
        except WorkspaceError as exc:
            if args.debug:
                raise
            return _emit_cli_error(args, exc.code)
        except ProvenanceError as exc:
            if args.debug:
                raise
            return _emit_cli_error(args, exc.code)
        except (OSError, UnicodeDecodeError):
            if args.debug:
                raise
            return _emit_cli_error(args, "EXPRESSION_SOURCE_UNREADABLE")
        except Exception:
            if args.debug:
                raise
            return _emit_cli_error(args, "INTERNAL_ERROR")
    finally:
        # Owned child-process hygiene: sweep any engine-owned budget workers
        # on EVERY CLI exit path (success, verdict, error, interrupt). The
        # budgets module also registers an atexit sweep as a backstop.
        from .budgets import sweep_owned_children
        sweep_owned_children()


if __name__ == "__main__":
    sys.exit(main())
