"""Standalone symbolic compactification engine.

Kernel modules:
  models    - shared data types, verdict constants, symbol normalization
  parser    - strict whitelist SymPy parser (fail-closed, no eval/exec)
  verifier  - exact residual verification (ZERO / NONZERO / UNKNOWN)
  residual  - residual construction and session recording helpers

Session persistence and the CLI are owned by later layers and are
intentionally not part of this kernel.
"""

__version__ = "0.1.0"

from .models import (ZERO, NONZERO, UNKNOWN, VERIFIER_NAME, AdapterError,
                     ExpressionRecord, SessionState, StepRecord,
                     VerificationResult, normalize_symbols, sha256_text)
from .parser import (PARSE_POLICY, get_parse_policy, load_expression,
                     parse_expression, set_parse_policy, syms_like)
from .verifier import verify_equivalent
from .residual import make_residual, residual_record

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
]
