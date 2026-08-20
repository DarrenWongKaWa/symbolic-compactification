"""Shared data types, verdict constants and normalization helpers.

This module contains NO scientific content: only generic math/engineering
plumbing shared by the parser, the verifier and (later) the session layer.
Every record type is JSON-serializable through its ``to_dict()`` method.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import sympy

# --------------------------------------------------------------------------- #
# engine identity (versioning + provenance)
# --------------------------------------------------------------------------- #

ENGINE_VERSION = "0.2.0"

# Agent-protocol version (v0.2.2 increment): the deterministic engine is
# unchanged from v0.2.0; this constant tracks the agent-layer protocol
# (conjecture packet + STRUCTURAL_PROPOSER role contract, packet/proposal
# provenance and the PROOF_REQUIRED status taxonomy) recorded in run
# manifests alongside ``engine_version``.
AGENT_PROTOCOL_VERSION = "0.2.2"


def engine_git_sha() -> str:
    """Best-effort git HEAD sha of the engine checkout; ``"unknown"`` fallback.

    Provenance metadata only: a failure to read git NEVER fails a session
    write.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(Path(__file__).resolve().parent),
            capture_output=True, text=True, timeout=5)
        sha = out.stdout.strip()
        if out.returncode == 0 and sha:
            return sha
    except Exception:
        pass
    return "unknown"

# --------------------------------------------------------------------------- #
# verdict constants
# --------------------------------------------------------------------------- #

ZERO = "ZERO"          # exact symbolic identity
NONZERO = "NONZERO"    # refuted by an exact counterexample
UNKNOWN = "UNKNOWN"    # fail-closed: simplification undecided, no counterexample

VERIFIER_NAME = "python_sympy_exact_v1"

# Step-status lifecycle (v0.2). The CONJECTURE layer is distinct from
# certification: HYPOTHESIS marks a proposed step, UNVERIFIED one that ran
# without a ZERO verdict, CERTIFIED one certified by an exact ZERO verdict.
# The status field is OPTIONAL metadata; default behavior is unchanged.
#
# Status taxonomy (v0.2.2) — precise semantics:
# * HYPOTHESIS     - conjecture layer only: a proposed step no verifier has
#                    adjudicated yet.
# * UNVERIFIED     - a verification step ran without a ZERO verdict.
# * CERTIFIED      - certified by an exact ZERO verdict.
# * PROOF_REQUIRED - the declared assumptions are already SUFFICIENT for the
#                    claim, but the current verifier cannot prove it within
#                    its deterministic machinery/budgets. This is a
#                    proof-gap status, NOT a human-decision gate. In
#                    particular, the inability to prove a limit or
#                    special-function identity must NOT be labeled
#                    HUMAN_REQUIRED: ``HUMAN_REQUIRED`` (an
#                    ``assumptions_status`` on proposals, and a
#                    certification gate) is reserved for genuinely NEW
#                    assumptions or physical choices that require human
#                    authorization. UNKNOWN remains the verifier-level
#                    "adjudication unresolved" verdict.
STEP_STATUSES = ("HYPOTHESIS", "UNVERIFIED", "CERTIFIED", "PROOF_REQUIRED")

# Evidence kind marking a step as a STRUCTURAL_PROPOSER hypothesis (v0.2.1
# agent protocol): no verifier ran on such a step; ``run_summary`` uses this
# marker to separate proposal steps from real verification steps.
PROPOSAL_EVIDENCE_KIND = "proposer_candidate"

# Proposer-invocation modes (v0.2.2). ``run_summary`` derives ``proposer_mode``
# STRICTLY from recorded evidence — never by inferring subagent use from the
# role contract merely existing/being read. A proposal step carrying a
# recorded subagent id is HARNESS_SUBAGENT; one recorded with explicit
# ``main_agent`` mode evidence is MAIN_AGENT_ONLY; an explicit
# ``subagent_unavailable`` record (the harness cannot expose native subagent
# invocation for this run) is SUBAGENT_UNAVAILABLE — DISTINCT from UNKNOWN,
# which means the evidence is ambiguous or absent. Reading
# ``roles/STRUCTURAL_PROPOSER.md`` is never evidence of any mode.
PROPOSER_MAIN_AGENT = "MAIN_AGENT_ONLY"
PROPOSER_HARNESS_SUBAGENT = "HARNESS_SUBAGENT"
PROPOSER_SUBAGENT_UNAVAILABLE = "SUBAGENT_UNAVAILABLE"
PROPOSER_MODE_UNKNOWN = "UNKNOWN"
PROPOSER_MODES = (PROPOSER_MAIN_AGENT, PROPOSER_HARNESS_SUBAGENT,
                  PROPOSER_SUBAGENT_UNAVAILABLE, PROPOSER_MODE_UNKNOWN)
DEFAULT_PROPOSER_ROLE = "STRUCTURAL_PROPOSER"

# A/B arm vocabulary (v0.2.2): a run may DECLARE which experiment arm it is
# at ``init_session`` time (or later via ``set_requested_arm``). Arm validity
# is derived strictly from recorded proposer evidence in ``run_summary``:
# arm B requires a recorded harness subagent; arm A requires none.
REQUESTED_ARMS = ("A", "B")

MAX_SYMBOLS = 40

# Names that may never be used as declared symbol names: they collide with the
# parser's allowed functions/constants whitelist.
RESERVED_NAMES = frozenset({
    "pi", "E", "I", "oo",
    "sin", "cos", "tan", "exp", "log", "sqrt", "Abs", "conjugate", "re", "im",
    "sinh", "cosh", "tanh", "asin", "acos", "atan", "atan2", "Rational",
    # must mirror the parser's allowed-functions policy: admitting a function
    # (e.g. the polygamma family, v0.2) reserves its name as a symbol too
    "polygamma",
    # structural builtins (v0.2) are callables only; never declared symbols
    "Sum", "Product", "Piecewise",
    "Eq", "Ne", "Lt", "Le", "Gt", "Ge", "And", "Or", "Not", "True", "False",
})

# Symbol namespace policy (v0.2): explicit declaration beats built-in, but
# only along the function-builtin axis and only when EXPLICITLY opted in.
#
# * HARD-RESERVED names (constants, Rational, structural builtins) can NEVER
#   be declared, in any namespace: they carry fixed SymPy semantics and an
#   explicit declaration could not safely shadow them.
# * FUNCTION builtins (sin, cos, ..., polygamma) are reserved for the DEFAULT
#   symbol declaration path (``SYMBOL_NAME_RESERVED``). With the explicit
#   opt-in ``normalize_symbols(..., allow_reserved=True)`` a declared symbol
#   named like a function builtin is treated as a SYMBOL — the reserved-name
#   rejection applies only to UNDECLARED collisions.
HARD_RESERVED_NAMES = frozenset({
    "pi", "E", "I", "oo", "Rational",
    "Sum", "Product", "Piecewise",
    "Eq", "Ne", "Lt", "Le", "Gt", "Ge", "And", "Or", "Not", "True", "False",
})
FUNCTION_RESERVED_NAMES = RESERVED_NAMES - HARD_RESERVED_NAMES


def _now_iso() -> str:
    """UTC timestamp string used across session records."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# --------------------------------------------------------------------------- #
# error type
# --------------------------------------------------------------------------- #

class AdapterError(Exception):
    """Engine error carrying a stable machine-readable ``.code`` string."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


# --------------------------------------------------------------------------- #
# hashing helper
# --------------------------------------------------------------------------- #

def sha256_text(s: str) -> str:
    """SHA-256 hex digest of a string (utf-8 encoded)."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def canonical_json(payload: Any) -> str:
    """Canonical JSON encoding for deterministic hashing.

    Sorted keys, compact separators, non-ASCII preserved. Two JSON-native
    payloads that are equal as data always encode to the identical string,
    so ``sha256_text(canonical_json(p))`` is a stable content hash.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


# --------------------------------------------------------------------------- #
# symbol normalization
# --------------------------------------------------------------------------- #

def normalize_symbols(symbols: Any, *, allow_reserved: bool = False) -> list[dict]:
    """Normalize a symbol declaration list to canonical dict form.

    Accepts ``["x", "y"]`` or ``[{"name": "x", "real": true, "nonzero": false}, ...]``.
    The string shorthand defaults to ``real=True, nonzero=False``.

    Namespace policy: by default ANY collision with a reserved builtin name
    is rejected (``SYMBOL_NAME_RESERVED``). With the EXPLICIT opt-in
    ``allow_reserved=True`` the precedence "explicit declaration beats
    built-in" applies along the function axis: a declared symbol named like
    a function builtin (sin, cos, ...) is treated as a SYMBOL, while
    hard-reserved names (constants, Rational, structural builtins) are
    ALWAYS rejected. The reserved-name rejection thus applies only to
    undeclared collisions once declarations are explicit.

    Raises:
      AdapterError("CLAIM_SYMBOLS_MALFORMED")  - bad shape, empty list, or duplicates
      AdapterError("SYMBOL_NAME_RESERVED")     - name collides with allowed
                                                 functions/constants
      AdapterError("CLAIM_SYMBOLS_TOO_MANY")   - more than MAX_SYMBOLS symbols
    """
    if not isinstance(symbols, (list, tuple)):
        raise AdapterError("CLAIM_SYMBOLS_MALFORMED")
    out: list[dict] = []
    for entry in symbols:
        if isinstance(entry, str):
            name = entry
            out.append({"name": name, "real": True, "nonzero": False})
        elif isinstance(entry, dict) and isinstance(entry.get("name"), str):
            out.append({
                "name": entry["name"],
                "real": bool(entry.get("real", True)),
                "nonzero": bool(entry.get("nonzero", False)),
            })
        else:
            raise AdapterError("CLAIM_SYMBOLS_MALFORMED")
    names = [s["name"] for s in out]
    if not names:
        raise AdapterError("CLAIM_SYMBOLS_MALFORMED")
    if len(names) != len(set(names)):
        raise AdapterError("CLAIM_SYMBOLS_MALFORMED")
    if any(not n or not n.strip() for n in names):
        raise AdapterError("CLAIM_SYMBOLS_MALFORMED")
    forbidden = HARD_RESERVED_NAMES if allow_reserved else RESERVED_NAMES
    if forbidden & set(names):
        raise AdapterError("SYMBOL_NAME_RESERVED")
    if len(names) > MAX_SYMBOLS:
        raise AdapterError("CLAIM_SYMBOLS_TOO_MANY")
    return out


# --------------------------------------------------------------------------- #
# data records (all JSON-serializable via to_dict)
# --------------------------------------------------------------------------- #

@dataclass
class ExpressionRecord:
    """One ingested expression: original text, content hash, parse result."""

    text: str
    sha256: str
    source_path: Optional[str] = None
    parsed_expr: Optional[sympy.Expr] = None
    symbols: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "sha256": self.sha256,
            "source_path": self.source_path,
            # sympy expressions are not JSON-native; store the canonical string
            "parsed_expr": None if self.parsed_expr is None else str(self.parsed_expr),
            "symbols": [dict(s) for s in self.symbols],
        }


@dataclass
class VerificationResult:
    """Outcome of one residual verification. Fail-closed verdict semantics."""

    verdict: str                      # ZERO | NONZERO | UNKNOWN
    residual: str                     # str(expand(current - candidate))
    simplified_residual: str          # str of the adjudicated simplified form
    evidence: list[dict] = field(default_factory=list)
    counterexample: Optional[dict] = None
    probes_tried: int = 0
    seconds: float = 0.0
    verifier: str = VERIFIER_NAME

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "residual": self.residual,
            "simplified_residual": self.simplified_residual,
            "evidence": list(self.evidence),
            "counterexample": self.counterexample,
            "probes_tried": self.probes_tried,
            "seconds": self.seconds,
            "verifier": self.verifier,
        }


@dataclass
class StepRecord:
    """One compactification step: candidate vs. current, residual + verdict.

    v0.2 additions (all optional; default behavior unchanged):
      * ``status``          - lifecycle marker, one of ``STEP_STATUSES``
                              (HYPOTHESIS / UNVERIFIED / CERTIFIED) or None;
                              the conjecture layer is DISTINCT from
                              certification.
      * ``telemetry``       - cheap JSON-native step telemetry: input_chars,
                              output_chars, count_ops_before, count_ops_after,
                              primitive (name or None), wall_time_seconds,
                              verdict, timeout_status, engine_version.
      * ``engine_version``  - engine version that produced the record.
      * ``engine_git_sha``  - engine git HEAD sha (provenance; "unknown" ok).
    """

    step: int
    current_hash: str
    candidate_hash: str
    candidate_text: str
    residual: Optional[str]
    verdict: str
    evidence: list[dict] = field(default_factory=list)
    timestamp: str = field(default_factory=_now_iso)
    status: Optional[str] = None
    telemetry: dict = field(default_factory=dict)
    engine_version: str = ENGINE_VERSION
    engine_git_sha: str = field(default_factory=engine_git_sha)

    def __post_init__(self):
        if self.status is not None and self.status not in STEP_STATUSES:
            raise AdapterError("STEP_STATUS_INVALID")

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "current_hash": self.current_hash,
            "candidate_hash": self.candidate_hash,
            "candidate_text": self.candidate_text,
            "residual": self.residual,
            "verdict": self.verdict,
            "evidence": list(self.evidence),
            "timestamp": self.timestamp,
            "status": self.status,
            "telemetry": dict(self.telemetry),
            "engine_version": self.engine_version,
            "engine_git_sha": self.engine_git_sha,
        }


@dataclass
class SessionState:
    """Minimal session container; a later task owns JSON (de)serialization."""

    run_id: str
    created_at: str = field(default_factory=_now_iso)
    current: Optional[ExpressionRecord] = None
    steps: list[StepRecord] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "current": None if self.current is None else self.current.to_dict(),
            "steps": [s.to_dict() for s in self.steps],
        }
