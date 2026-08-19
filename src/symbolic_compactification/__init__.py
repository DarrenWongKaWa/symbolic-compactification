"""Standalone symbolic compactification engine.

Kernel modules:
  models    - shared data types, verdict constants, symbol normalization
  parser    - strict whitelist SymPy parser (fail-closed, no eval/exec)
  verifier  - exact residual verification (ZERO / NONZERO / UNKNOWN)
  residual  - residual construction and session recording helpers
  session   - JSON-based run/session persistence (workspace/runs/<run-id>/)
  cli       - command-line interface (inspect / verify / init-session / step)
"""

__version__ = "0.1.0"

from .models import (ZERO, NONZERO, UNKNOWN, VERIFIER_NAME, AdapterError,
                     ExpressionRecord, SessionState, StepRecord,
                     VerificationResult, normalize_symbols, sha256_text)
from .parser import (PARSE_POLICY, get_parse_policy, load_expression,
                     parse_expression, set_parse_policy, syms_like)
from .verifier import verify_equivalent
from .residual import make_residual, residual_record
from .session import (init_session, load_session, promote, record_step,
                      set_current)

__all__ = [
    "__version__",
    # models
    "ZERO", "NONZERO", "UNKNOWN", "VERIFIER_NAME",
    "AdapterError", "ExpressionRecord", "VerificationResult",
    "StepRecord", "SessionState", "normalize_symbols", "sha256_text",
    # parser
    "PARSE_POLICY", "get_parse_policy", "set_parse_policy",
    "parse_expression", "load_expression", "syms_like",
    # verifier / residual
    "verify_equivalent", "make_residual", "residual_record",
    # session persistence
    "init_session", "load_session", "record_step", "promote", "set_current",
]
