"""Optional independent second-engine (Wolfram) check. Opt-in, fail-closed.

Ported from ``repo-native-symbolic-science`` (``tools/independent_zero_engine.py``
and ``tools/wolfram_runtime.py``; Apache-2.0, same author) and adapted to this
package's ZERO / NONZERO / UNKNOWN verdict model.  Attribution:
``docs/history/third-party.md``.

Role
----
The primary route ``python_sympy_exact_v1`` remains the ONLY route that
issues a verdict.  When a caller explicitly opts in
(``verify_equivalent(..., second_engine="wolfram")`` or
``symbolic-compactification verify ... --second-engine wolfram``), the same
raw ``current`` / ``candidate`` text is serialized to Wolfram Language
WITHOUT SymPy -- a Python ``ast`` walk over the strict grammar the primary
parser has already accepted -- and a separate ``wolframscript`` process is
asked whether::

    FullSimplify[current == candidate, <declared symbol domains>]

is ``True`` (engine ``ZERO``), ``False`` (engine ``NONZERO``: the two sides
are equal nowhere on the declared domain) or anything else (engine
``UNKNOWN``).  The comparison with the primary verdict is recorded as:

``agree``         both engines reached the same decisive verdict;
``disagree``      ZERO against NONZERO -- the verdict becomes UNKNOWN;
``inconclusive``  the second engine ran, but at least one side is UNKNOWN;
``unavailable``   the second engine could not run (not installed, not
                  activated, timeout, expression outside its grammar, ...).

Fail-closed rules
-----------------
* The second engine NEVER promotes.  An UNKNOWN or NONZERO primary verdict is
  never turned into ZERO, whatever Wolfram reports.
* A disagreement never yields a decisive verdict: the result is UNKNOWN.
* ``require=True`` keeps a primary ZERO only on ``agree``; every other status
  downgrades it to UNKNOWN (the RN ``SYMBOLIC_ZERO_PENDING_SECOND_ENGINE``
  rule).
* Without the opt-in nothing in this module runs and every existing output is
  byte-for-byte unchanged.

Executable discovery (first hit wins)
-------------------------------------
1. ``$SYMBOLIC_COMPACTIFICATION_WOLFRAMSCRIPT`` -- an absolute path to an
   executable file.  A set-but-invalid override is reported as
   ``WOLFRAM_OVERRIDE_INVALID``; it never silently falls back.
2. ``wolframscript`` on ``PATH``.
3. Known install locations (macOS app bundles, common Linux/Windows paths).

Injection safety
----------------
* No shell: ``[executable, "-code", code]`` is passed as an argv list.
* User text never reaches Wolfram.  Declared symbols are renamed to
  ``scv1, scv2, ...`` and declared functions to ``scf1, ...``; the rest of the
  generated code is integers, parentheses, arithmetic operators and a fixed
  table of function heads.  Anything else (floats, ``oo``, ``Sum``,
  ``Piecewise``, relations, ...) is ``EXPRESSION_UNSUPPORTED``.
* Bounded: the primary parser's size policy applies first, the generated code
  is capped, ``FullSimplify`` runs under ``TimeConstrained`` and the process
  under a wall-clock timeout.  On timeout only the process group this module
  started is signalled.
"""
from __future__ import annotations

import ast
import glob
import hashlib
import os
import re
import shutil
import signal
import subprocess
import time
from dataclasses import replace
from typing import Any, Optional

from .models import (AdapterError, NONZERO, UNKNOWN, ZERO,
                     VerificationResult, normalize_symbols)
from .parser import normalize_functions, parse_expression

# --------------------------------------------------------------------------- #
# identity / policy
# --------------------------------------------------------------------------- #

WOLFRAM_ENGINE = "wolfram"
SECOND_ENGINES = (WOLFRAM_ENGINE,)
SECOND_ENGINE_ROUTE = "wolfram_second_engine_v1"
SECOND_ENGINE_METHOD = "FullSimplify[current == candidate, declared domains]"
WOLFRAMSCRIPT_ENV = "SYMBOLIC_COMPACTIFICATION_WOLFRAMSCRIPT"

# Whole-process budget (spawn, kernel start, FullSimplify, shutdown).  RN
# measured kernel cold start at ~5-6 s and FullSimplify p95 at ~12 s under
# load; 120 s keeps a wide margin and a timeout is never a verdict.
DEFAULT_TIMEOUT_SECONDS = 120.0
_KILL_GRACE_SECONDS = 2.0
MAX_WOLFRAM_CODE_CHARS = 200_000

AGREE = "agree"
DISAGREE = "disagree"
INCONCLUSIVE = "inconclusive"
UNAVAILABLE = "unavailable"
SECOND_ENGINE_STATUSES = (AGREE, DISAGREE, INCONCLUSIVE, UNAVAILABLE)

_KNOWN_LOCATIONS = (
    # macOS application bundles
    "/Applications/Wolfram.app/Contents/MacOS/wolframscript",
    "/Applications/Wolfram Engine.app/Contents/MacOS/wolframscript",
    "/Applications/Wolfram Engine.app/Contents/Resources/"
    "Wolfram Player.app/Contents/MacOS/wolframscript",
    "/Applications/Mathematica.app/Contents/MacOS/wolframscript",
    # Linux
    "/usr/local/bin/wolframscript",
    "/usr/bin/wolframscript",
    "/opt/Wolfram/WolframScript/bin/wolframscript",
    # Windows
    r"C:\Program Files\Wolfram Research\WolframScript\wolframscript.exe",
)
# versioned Linux installs; newest version directory first
_KNOWN_LOCATION_GLOBS = (
    "/usr/local/Wolfram/Wolfram/*/Executables/wolframscript",
    "/usr/local/Wolfram/WolframEngine/*/Executables/wolframscript",
    "/usr/local/Wolfram/Mathematica/*/Executables/wolframscript",
    "/opt/Wolfram/WolframEngine/*/Executables/wolframscript",
    "/opt/Wolfram/Mathematica/*/Executables/wolframscript",
)

_OUTPUT_RE = re.compile(
    r"SCSE\|([0-9]+(?:\.[0-9]+){0,3})\|(ZERO|NONZERO|UNDECIDED|TIMEOUT)\Z")


class SecondEngineUnavailable(Exception):
    """Internal: the second engine cannot run; ``code`` is a stable reason."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


# --------------------------------------------------------------------------- #
# discovery
# --------------------------------------------------------------------------- #

def _version_key(path: str) -> list[int]:
    """Numeric sort key so ``14.1`` ranks above ``9.0`` (newest first)."""
    return [int(part) for part in re.findall(r"\d+", path)]


def _is_executable_file(path: str) -> bool:
    return os.path.isfile(path) and os.access(path, os.X_OK)


def find_wolframscript(environ: Optional[dict] = None) -> tuple[str, str]:
    """Return ``(executable, discovery)`` or raise ``SecondEngineUnavailable``.

    ``discovery`` is ``env_override``, ``path`` or ``known_location``; the
    absolute host path itself is never written into results.
    """
    env = os.environ if environ is None else environ
    override = env.get(WOLFRAMSCRIPT_ENV)
    if override is not None and override != "":
        if os.path.isabs(override) and _is_executable_file(override):
            return override, "env_override"
        raise SecondEngineUnavailable("WOLFRAM_OVERRIDE_INVALID")
    on_path = shutil.which("wolframscript", path=env.get("PATH"))
    if on_path and _is_executable_file(on_path):
        return on_path, "path"
    for candidate in _KNOWN_LOCATIONS:
        if _is_executable_file(candidate):
            return candidate, "known_location"
    for pattern in _KNOWN_LOCATION_GLOBS:
        for candidate in sorted(glob.glob(pattern), key=_version_key,
                                reverse=True):
            if _is_executable_file(candidate):
                return candidate, "known_location"
    raise SecondEngineUnavailable("WOLFRAM_NOT_FOUND")


def wolfram_available(environ: Optional[dict] = None) -> bool:
    """True when a ``wolframscript`` executable is discoverable."""
    try:
        find_wolframscript(environ)
    except SecondEngineUnavailable:
        return False
    return True


# --------------------------------------------------------------------------- #
# raw text -> Wolfram Language (no SymPy on this path)
# --------------------------------------------------------------------------- #

_UNARY_HEADS = {
    "sin": "Sin", "cos": "Cos", "tan": "Tan", "exp": "Exp", "sqrt": "Sqrt",
    "sinh": "Sinh", "cosh": "Cosh", "tanh": "Tanh",
    "asin": "ArcSin", "acos": "ArcCos", "atan": "ArcTan",
    "Abs": "Abs", "conjugate": "Conjugate", "re": "Re", "im": "Im",
}
_CONSTANTS = {"pi": "Pi", "E": "E", "I": "I"}
_BINOPS = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
           ast.Pow: "^"}


class _Unsupported(Exception):
    pass


def _integer(node: ast.AST) -> Optional[int]:
    """Exact Python ``int`` literal (``bool`` excluded), optionally negated."""
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value
    if (isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub)
            and isinstance(node.operand, ast.Constant)
            and type(node.operand.value) is int):
        return -node.operand.value
    return None


def _to_wolfram(text: str, symbol_map: dict, function_map: dict) -> str:
    """Serialize one strict-grammar expression to Wolfram Language."""
    # the token grammar has no string literals, so collapsing whitespace and
    # mapping ``^`` to ``**`` (as the primary parser's convert_xor does) is
    # meaning-preserving
    normalized = " ".join(text.split()).replace("^", "**")
    try:
        tree = ast.parse(normalized, mode="eval").body
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        raise _Unsupported() from None

    def emit(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            if node.id in symbol_map:
                return symbol_map[node.id]
            if node.id in _CONSTANTS:
                return _CONSTANTS[node.id]
            raise _Unsupported()
        if isinstance(node, ast.Constant):
            if type(node.value) is int:
                return str(node.value)
            raise _Unsupported()  # floats, bools, strings: never exact here
        if isinstance(node, ast.UnaryOp) and isinstance(
                node.op, (ast.USub, ast.UAdd)):
            sign = "-" if isinstance(node.op, ast.USub) else "+"
            return "(" + sign + emit(node.operand) + ")"
        if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
            return ("(" + emit(node.left) + _BINOPS[type(node.op)]
                    + emit(node.right) + ")")
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and not node.keywords):
            name, args = node.func.id, node.args
            if any(isinstance(a, ast.Starred) for a in args):
                raise _Unsupported()
            # explicit declaration beats built-in (parser namespace policy)
            if name in function_map:
                if not args:
                    raise _Unsupported()
                return (function_map[name] + "["
                        + ",".join(emit(a) for a in args) + "]")
            if name in symbol_map:
                raise _Unsupported()
            if name in _UNARY_HEADS and len(args) == 1:
                return _UNARY_HEADS[name] + "[" + emit(args[0]) + "]"
            if name == "log" and len(args) == 1:
                return "Log[" + emit(args[0]) + "]"
            if name == "log" and len(args) == 2:      # log(x, b) = Log[b, x]
                return "Log[" + emit(args[1]) + "," + emit(args[0]) + "]"
            if name == "atan2" and len(args) == 2:    # atan2(y, x) = ArcTan[x, y]
                return "ArcTan[" + emit(args[1]) + "," + emit(args[0]) + "]"
            if name == "polygamma" and len(args) == 2:
                return "PolyGamma[" + emit(args[0]) + "," + emit(args[1]) + "]"
            if name == "Rational" and len(args) == 2:
                p, q = _integer(args[0]), _integer(args[1])
                if p is None or q is None or q == 0:
                    raise _Unsupported()
                return "(" + str(p) + "/" + str(q) + ")"
        raise _Unsupported()

    try:
        return emit(tree)
    except RecursionError:
        raise _Unsupported() from None


def build_wolfram_code(current_text: str, candidate_text: str, symbols: Any,
                       *, functions: Any = None, allow_reserved: bool = False,
                       time_constraint_seconds: float = 90.0) -> str:
    """Return the Wolfram Language program for one equivalence check.

    Both texts must first pass the package's strict whitelist parser (same
    namespace policy as the primary route).  Raises
    ``SecondEngineUnavailable`` with ``EXPRESSION_REJECTED``,
    ``EXPRESSION_UNSUPPORTED`` or ``WOLFRAM_INPUT_TOO_LARGE``.
    """
    try:
        declared = normalize_symbols(symbols, allow_reserved=allow_reserved)
        func_names = normalize_functions(
            functions, declared_symbol_names={s["name"] for s in declared})
        for text in (current_text, candidate_text):
            parse_expression(text, declared, functions=func_names or None,
                             allow_reserved=allow_reserved)
    except AdapterError:
        raise SecondEngineUnavailable("EXPRESSION_REJECTED") from None

    symbol_map = {s["name"]: f"scv{i}" for i, s in enumerate(declared, 1)}
    function_map = {name: f"scf{i}" for i, name in enumerate(func_names, 1)}
    try:
        lhs = _to_wolfram(current_text, symbol_map, function_map)
        rhs = _to_wolfram(candidate_text, symbol_map, function_map)
    except _Unsupported:
        raise SecondEngineUnavailable("EXPRESSION_UNSUPPORTED") from None

    conditions = []
    # mirror SymPy: ``nonzero=True`` means real and nonzero
    reals = [symbol_map[s["name"]] for s in declared
             if s["real"] or s.get("nonzero")]
    if reals:
        conditions.append("Element[{" + ",".join(reals) + "},Reals]")
    conditions.extend(symbol_map[s["name"]] + "!=0"
                      for s in declared if s.get("nonzero"))
    assumptions = "&&".join(conditions) if conditions else "True"
    limit = max(1, int(time_constraint_seconds))
    code = (
        "Module[{scr=Quiet[TimeConstrained[FullSimplify[(" + lhs + ")==("
        + rhs + ")," + assumptions + "]," + str(limit) + ",$Aborted]]},"
        "StringRiffle[{\"SCSE\",First[StringSplit[$Version]],"
        "Which[scr===True,\"ZERO\",scr===False,\"NONZERO\","
        "scr===$Aborted,\"TIMEOUT\",True,\"UNDECIDED\"]},\"|\"]]"
    )
    if len(code) > MAX_WOLFRAM_CODE_CHARS:
        raise SecondEngineUnavailable("WOLFRAM_INPUT_TOO_LARGE")
    return code


# --------------------------------------------------------------------------- #
# process execution
# --------------------------------------------------------------------------- #

def _terminate_owned(proc: subprocess.Popen) -> None:
    """Stop the process group this module started (never anything else)."""
    use_group = os.name == "posix" and hasattr(os, "killpg")
    try:
        if use_group:
            os.killpg(proc.pid, signal.SIGTERM)
        else:
            proc.terminate()
    except (ProcessLookupError, PermissionError, OSError):
        pass
    try:
        proc.wait(timeout=_KILL_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        try:
            if use_group:
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
        except (ProcessLookupError, PermissionError, OSError):
            pass
    try:
        proc.communicate(timeout=_KILL_GRACE_SECONDS)
    except Exception:
        pass


def run_wolframscript(executable: str, code: str,
                      timeout_seconds: float) -> tuple[int, str, str]:
    """Run ``executable -code CODE`` without a shell; return (rc, out, err).

    Raises ``SecondEngineUnavailable`` (``WOLFRAM_LAUNCH_FAILED`` /
    ``WOLFRAM_TIMEOUT``).  This is the unit-test seam.
    """
    try:
        proc = subprocess.Popen(
            [executable, "-code", code],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8",
            errors="replace", shell=False,
            start_new_session=(os.name == "posix"))
    except (OSError, ValueError):
        raise SecondEngineUnavailable("WOLFRAM_LAUNCH_FAILED") from None
    try:
        out, err = proc.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        _terminate_owned(proc)
        raise SecondEngineUnavailable("WOLFRAM_TIMEOUT") from None
    except BaseException:
        _terminate_owned(proc)
        raise
    return proc.returncode, out or "", err or ""


# --------------------------------------------------------------------------- #
# the check and its combination with the primary verdict
# --------------------------------------------------------------------------- #

def _blank_record(engine: str = WOLFRAM_ENGINE,
                  reason: Optional[str] = None) -> dict:
    return {
        "engine": engine,
        "route": SECOND_ENGINE_ROUTE if engine == WOLFRAM_ENGINE else None,
        "method": SECOND_ENGINE_METHOD if engine == WOLFRAM_ENGINE else None,
        "engine_verdict": None,
        "reason": reason,
        "wolfram_version": None,
        "discovery": None,
        "wolfram_input_sha256": None,
        "seconds": 0.0,
    }


def wolfram_zero_check(current_text: str, candidate_text: str, symbols: Any,
                       *, functions: Any = None, allow_reserved: bool = False,
                       timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
                       environ: Optional[dict] = None) -> dict:
    """Ask Wolfram whether ``current == candidate``; never raises.

    Returns a JSON-native record whose ``engine_verdict`` is ``ZERO``,
    ``NONZERO``, ``UNKNOWN`` (ran, undecided) or ``None`` (could not run;
    ``reason`` says why).
    """
    t0 = time.monotonic()
    record = _blank_record()
    try:
        if (isinstance(timeout_seconds, bool)
                or not isinstance(timeout_seconds, (int, float))
                or not timeout_seconds > 0):
            raise SecondEngineUnavailable("SECOND_ENGINE_TIMEOUT_INVALID")
        code = build_wolfram_code(
            current_text, candidate_text, symbols, functions=functions,
            allow_reserved=allow_reserved,
            time_constraint_seconds=max(1.0, 0.75 * float(timeout_seconds)))
        record["wolfram_input_sha256"] = hashlib.sha256(
            code.encode("utf-8")).hexdigest()
        executable, record["discovery"] = find_wolframscript(environ)
        returncode, out, _err = run_wolframscript(
            executable, code, float(timeout_seconds))
        if returncode != 0:
            raise SecondEngineUnavailable("WOLFRAM_PROCESS_FAILED")
        match = _OUTPUT_RE.fullmatch(out.strip())
        if match is None:
            # e.g. an unactivated kernel, license prompt, or stray messages
            raise SecondEngineUnavailable("WOLFRAM_OUTPUT_UNRECOGNIZED")
        record["wolfram_version"] = match.group(1)
        outcome = match.group(2)
        if outcome in (ZERO, NONZERO):
            record["engine_verdict"] = outcome
        else:
            record["engine_verdict"] = UNKNOWN
            record["reason"] = ("WOLFRAM_TIME_CONSTRAINT" if outcome == "TIMEOUT"
                                else "WOLFRAM_UNDECIDED")
    except SecondEngineUnavailable as exc:
        record["engine_verdict"] = None
        record["reason"] = exc.code
    except Exception:  # defensive: the opt-in check must never raise
        record["engine_verdict"] = None
        record["reason"] = "SECOND_ENGINE_INTERNAL_ERROR"
    record["seconds"] = round(time.monotonic() - t0, 4)
    return record


def compare_verdicts(primary: str, engine_verdict: Optional[str]) -> str:
    """Classify a primary verdict against a second-engine verdict."""
    if engine_verdict is None:
        return UNAVAILABLE
    decisive = (ZERO, NONZERO)
    if primary in decisive and engine_verdict == primary:
        return AGREE
    if primary in decisive and engine_verdict in decisive:
        return DISAGREE
    return INCONCLUSIVE


def apply_second_engine(result: VerificationResult, check: dict, *,
                        require: bool = False) -> VerificationResult:
    """Combine a primary result with a second-engine record (fail-closed).

    Returns a NEW result; ``result`` is not mutated.  The verdict can only
    stay the same or become UNKNOWN -- never ZERO from anything else.
    """
    primary = result.verdict
    status = compare_verdicts(primary, check.get("engine_verdict"))
    final = primary
    fail_closed_reason = None
    if status == DISAGREE:
        final, fail_closed_reason = UNKNOWN, "SECOND_ENGINE_DISAGREES"
    elif require and primary == ZERO and status != AGREE:
        final, fail_closed_reason = UNKNOWN, "SECOND_ENGINE_CONFIRMATION_REQUIRED"
    if final not in (primary, UNKNOWN):  # structural guard: never promote
        final, fail_closed_reason = UNKNOWN, "SECOND_ENGINE_GUARD"

    summary = {
        **check,
        "status": status,
        "primary_verdict": primary,
        "final_verdict": final,
        "required": bool(require),
        "fail_closed_reason": fail_closed_reason,
    }
    evidence = list(result.evidence)
    evidence.append({
        "kind": "independent_second_engine",
        "engine": check.get("engine", WOLFRAM_ENGINE),
        "status": status,
        "engine_verdict": check.get("engine_verdict"),
        "reason": check.get("reason"),
    })
    if fail_closed_reason is not None:
        evidence.append({
            "kind": "second_engine_fail_closed",
            "primary_verdict": primary,
            "reason": fail_closed_reason,
        })
    return replace(result, verdict=final, evidence=evidence,
                   second_engine=summary)


def verify_with_second_engine(result: VerificationResult, current_text: Any,
                              candidate_text: Any, symbols: Any, *,
                              engine: Optional[str] = WOLFRAM_ENGINE,
                              require: bool = False, functions: Any = None,
                              allow_reserved: bool = False,
                              timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
                              ) -> VerificationResult:
    """Run the selected second engine on a finished primary result."""
    if engine not in SECOND_ENGINES:
        check = _blank_record(str(engine)[:64], "SECOND_ENGINE_UNSUPPORTED")
    elif not isinstance(current_text, str) or not isinstance(candidate_text, str):
        check = _blank_record(reason="EXPRESSION_REJECTED")
    else:
        check = wolfram_zero_check(
            current_text, candidate_text, symbols, functions=functions,
            allow_reserved=allow_reserved, timeout_seconds=timeout_seconds)
    return apply_second_engine(result, check, require=require)


__all__ = [
    "AGREE", "DISAGREE", "INCONCLUSIVE", "UNAVAILABLE",
    "DEFAULT_TIMEOUT_SECONDS", "SECOND_ENGINES", "SECOND_ENGINE_ROUTE",
    "SECOND_ENGINE_STATUSES", "WOLFRAMSCRIPT_ENV", "WOLFRAM_ENGINE",
    "SecondEngineUnavailable", "apply_second_engine", "build_wolfram_code",
    "compare_verdicts", "find_wolframscript", "run_wolframscript",
    "verify_with_second_engine", "wolfram_available", "wolfram_zero_check",
]
