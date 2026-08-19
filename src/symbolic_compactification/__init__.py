"""Standalone symbolic compactification engine.

Kernel modules:
  models    - shared data types, verdict constants, symbol normalization
  parser    - strict whitelist SymPy parser (fail-closed, no eval/exec)
  verifier  - exact residual verification (ZERO / NONZERO / UNKNOWN)
  residual  - residual construction and session recording helpers
  session   - JSON-based run/session persistence (workspace/runs/<run-id>/)
  cli       - command-line interface (inspect / verify / init-session / step)
  adapters  - neutral ingestion adapters (Wolfram text -> SymPy)
  structure - structure-first preservation + finite-N diagnostic replay
  transforms- bounded structural transformation primitives
  budgets   - wall-clock budgets for expensive symbolic operations
"""

__version__ = "0.1.0"

from .models import (ZERO, NONZERO, UNKNOWN, VERIFIER_NAME, AdapterError,
                     ExpressionRecord, SessionState, StepRecord,
                     VerificationResult, normalize_symbols, sha256_text)
from .parser import (PARSE_POLICY, get_parse_policy, load_expression,
                     parse_expression, set_parse_policy, syms_like)
from .verifier import (VERIFY_POLICY, get_verify_policy, set_verify_policy,
                        verify_equivalent)
from .residual import make_residual, residual_record
from .session import (init_session, load_session, promote, record_step,
                      set_current)
from .adapters import (TranslationResult, translate_wolfram_text,
                       extract_expression_text)
from .structure import expand_finite, structure_summary
from .budgets import (BudgetExceeded, get_budget_policy, run_with_budget,
                      set_budget_policy, shutdown_budget_pool)
from .transforms import (TransformResult, get_transform_policy,
                         set_transform_policy, combine_identical_sums,
                         factor_common_kernel, collect_common_factor,
                         canonicalize_equivalent_arguments, factor_terms,
                         together, cancel, residual_of)

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
    "VERIFY_POLICY", "get_verify_policy", "set_verify_policy",
    "verify_equivalent", "make_residual", "residual_record",
    # session persistence
    "init_session", "load_session", "record_step", "promote", "set_current",
    # adapters
    "TranslationResult", "translate_wolfram_text", "extract_expression_text",
    # structure (structure-first preservation + diagnostics)
    "expand_finite", "structure_summary",
    # budgets
    "BudgetExceeded", "get_budget_policy", "set_budget_policy",
    "run_with_budget", "shutdown_budget_pool",
    # transforms
    "TransformResult", "get_transform_policy", "set_transform_policy",
    "combine_identical_sums", "factor_common_kernel", "collect_common_factor",
    "canonicalize_equivalent_arguments", "factor_terms", "together", "cancel",
    "residual_of",
]
