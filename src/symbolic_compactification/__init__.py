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
  conjecture- agent protocol v0.2.1: conjecture packets + proposer candidates
              (harness-native proposer; NO agent runtime in this repo)
  reporting - agent protocol v0.2.2: FINAL CERTIFIED FORM deliverable
              contract (human-readable certified result + provenance artifact)
"""

from .models import (AGENT_PROTOCOL_VERSION, ENGINE_VERSION, ZERO, NONZERO,
                     UNKNOWN, VERIFIER_NAME, AdapterError, ExpressionRecord,
                     HARD_RESERVED_NAMES, PROPOSAL_EVIDENCE_KIND,
                     RESERVED_NAMES, STEP_STATUSES, SessionState, StepRecord,
                     VerificationResult, canonical_json, engine_git_sha,
                     normalize_symbols, sha256_text)

__version__ = ENGINE_VERSION
from .parser import (PARSE_POLICY, get_parse_policy, load_expression,
                     parse_expression, set_parse_policy, syms_like)
from .verifier import (VERIFY_POLICY, get_verify_policy, set_verify_policy,
                        verify_equivalent)
from .residual import make_residual, residual_record
from .session import (init_session, load_session, promote, record_step,
                      run_summary, set_current, set_requested_arm)
from .adapters import (TranslationResult, translate_wolfram_text,
                       extract_expression_text)
from .structure import expand_finite, structure_summary
from .budgets import (BudgetExceeded, ProcessLifecycle, get_budget_policy,
                      last_process_telemetry, owned_children_snapshot,
                      run_with_budget, set_budget_policy,
                      shutdown_budget_pool, sweep_owned_children)
from .transforms import (TransformResult, get_transform_policy,
                         set_transform_policy, combine_identical_sums,
                         factor_common_kernel, collect_common_factor,
                         canonicalize_equivalent_arguments, factor_terms,
                         together, cancel, residual_of)
from .rules import (BUILTIN_RULES, RewriteRule, RuleApplication, apply_rule,
                    apply_rules)
from .conjecture import (build_conjecture_packet, record_proposal,
                         validate_candidate)
from .reporting import FINAL_ARTIFACT_NAME, render_final_report

__all__ = [
    "__version__",
    # models
    "ZERO", "NONZERO", "UNKNOWN", "VERIFIER_NAME",
    "AdapterError", "ExpressionRecord", "VerificationResult",
    "StepRecord", "SessionState", "normalize_symbols", "sha256_text",
    "RESERVED_NAMES", "HARD_RESERVED_NAMES",
    "ENGINE_VERSION", "AGENT_PROTOCOL_VERSION", "PROPOSAL_EVIDENCE_KIND",
    "engine_git_sha", "STEP_STATUSES",
    # parser
    "PARSE_POLICY", "get_parse_policy", "set_parse_policy",
    "parse_expression", "load_expression", "syms_like",
    # verifier / residual
    "VERIFY_POLICY", "get_verify_policy", "set_verify_policy",
    "verify_equivalent", "make_residual", "residual_record",
    # session persistence
    "init_session", "load_session", "record_step", "promote", "set_current",
    "set_requested_arm",
    "run_summary",
    # adapters
    "TranslationResult", "translate_wolfram_text", "extract_expression_text",
    # structure (structure-first preservation + diagnostics)
    "expand_finite", "structure_summary",
    # budgets
    "BudgetExceeded", "get_budget_policy", "set_budget_policy",
    "run_with_budget", "shutdown_budget_pool",
    "ProcessLifecycle", "owned_children_snapshot", "sweep_owned_children",
    "last_process_telemetry",
    # transforms
    "TransformResult", "get_transform_policy", "set_transform_policy",
    "combine_identical_sums", "factor_common_kernel", "collect_common_factor",
    "canonicalize_equivalent_arguments", "factor_terms", "together", "cancel",
    "residual_of",
    # rules (assumption-aware rewrites)
    "BUILTIN_RULES", "RewriteRule", "RuleApplication", "apply_rule",
    "apply_rules",
    # conjecture (agent protocol v0.2.1; harness-native proposer, no runtime)
    "build_conjecture_packet", "validate_candidate", "record_proposal",
    # reporting (agent protocol v0.2.2 final certified-form contract)
    "render_final_report", "FINAL_ARTIFACT_NAME",
]
