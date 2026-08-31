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
  conjecture- conjecture packets + harness-native proposer candidates
              (harness-native proposer; NO agent runtime in this repo)
  reporting - FINAL CERTIFIED FORM deliverable contract
              contract (human-readable certified result + provenance artifact)
"""

from .models import (AGENT_PROTOCOL_VERSION, ASSUMPTION_STATUS_VALUES,
                     ENGINE_VERSION, PACKAGE_VERSION, ZERO, NONZERO,
                     UNKNOWN, VERIFIER_NAME, AdapterError, ExpressionRecord,
                     HARD_RESERVED_NAMES, PROOF_STATUS_VALUES,
                     PROPOSAL_EVIDENCE_KIND,
                     RESERVED_NAMES, STEP_STATUSES, SessionState, StepRecord,
                     VerificationResult, canonical_json, derive_status_axes,
                     engine_git_sha,
                     normalize_symbols, sha256_text)

__version__ = PACKAGE_VERSION
from .parser import (PARSE_POLICY, get_parse_policy, infer_namespace,
                     load_expression, normalize_functions, parse_expression,
                     set_parse_policy, syms_like)
from .verifier import (VERIFY_POLICY, get_verify_policy, set_verify_policy,
                        verify_equivalent)
from .residual import make_residual, residual_record
from .session import (init_session, load_session, promote, record_step,
                      run_summary, set_current, set_requested_arm,
                      set_requested_proposer_mode)
from .adapters import (TranslationResult, translate_wolfram_text,
                       extract_expression_text)
from .structure import (canonical_structure_items, expand_finite,
                        ordered_atoms, structure_summary)
from .budgets import (BudgetExceeded, ProcessLifecycle, get_budget_policy,
                      last_process_telemetry, owned_children_snapshot,
                      run_symbolic_operation, run_with_budget, set_budget_policy,
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
from .reporting import (CERTIFIED_EXPRESSION_NAME, FINAL_ARTIFACT_NAME,
                        render_final_report)
from .fidelity import (FIDELITY_CLASSES, translation_fidelity)
from .pipeline import StepOutcome, adjudicate_candidate
from .workspace import (HypothesisObligation, ResearchWorkspace,
                        WorkspaceError, WorkspaceHypothesis, WorkspaceProject,
                        WorkspaceSource, initialize_workspace, load_workspace)
from .provenance import (
    PROVENANCE_FILE_NAME,
    PROVENANCE_RESULTS,
    PROVENANCE_SCHEMA_VERSION,
    ProvenanceError,
    RecordedRun,
    build_run_record,
    dependency_versions,
    hash_named_files,
    record_research_run,
    sha256_file,
    write_run_record,
)
from .research_api import (
    ASSUMPTION_REQUIRED,
    COMPILE_FAILURE,
    PARSE_FAILURE,
    REPORT_FILE_NAME,
    RESULT_FILE_NAME,
    RESULT_SCHEMA_VERSION,
    GeneratedReport,
    HypothesisVerificationResult,
    ObligationVerification,
    generate_report,
    verify_hypothesis,
)
from .security import REDACTED, redact_public_data, redact_text

__all__ = [
    "__version__",
    # models
    "ZERO", "NONZERO", "UNKNOWN", "VERIFIER_NAME",
    "AdapterError", "ExpressionRecord", "VerificationResult",
    "StepRecord", "SessionState", "normalize_symbols", "sha256_text",
    "RESERVED_NAMES", "HARD_RESERVED_NAMES",
    "PACKAGE_VERSION", "ENGINE_VERSION", "AGENT_PROTOCOL_VERSION",
    "PROPOSAL_EVIDENCE_KIND",
    "engine_git_sha", "STEP_STATUSES",
    "ASSUMPTION_STATUS_VALUES", "PROOF_STATUS_VALUES", "derive_status_axes",
    # parser
    "PARSE_POLICY", "get_parse_policy", "set_parse_policy",
    "parse_expression", "load_expression", "normalize_functions",
    "infer_namespace", "syms_like",
    # verifier / residual
    "VERIFY_POLICY", "get_verify_policy", "set_verify_policy",
    "verify_equivalent", "make_residual", "residual_record",
    # session persistence
    "init_session", "load_session", "record_step", "promote", "set_current",
    "set_requested_arm",
    "set_requested_proposer_mode",
    "run_summary",
    # adapters
    "TranslationResult", "translate_wolfram_text", "extract_expression_text",
    # structure (structure-first preservation + diagnostics)
    "expand_finite", "structure_summary",
    # budgets
    "BudgetExceeded", "get_budget_policy", "set_budget_policy",
    "run_with_budget", "run_symbolic_operation", "shutdown_budget_pool",
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
    # conjecture (harness-native proposer, no runtime)
    "build_conjecture_packet", "validate_candidate", "record_proposal",
    # reporting (final certified-form contract)
    "render_final_report", "FINAL_ARTIFACT_NAME", "CERTIFIED_EXPRESSION_NAME",
    "translation_fidelity", "FIDELITY_CLASSES",
    # stable source-to-state pipeline
    "StepOutcome", "adjudicate_candidate",
    # external researcher workspace (read-only ingestion; no run mutation)
    "HypothesisObligation", "ResearchWorkspace", "WorkspaceError",
    "WorkspaceHypothesis", "WorkspaceProject", "WorkspaceSource",
    "initialize_workspace", "load_workspace",
    # bounded researcher-workspace run provenance
    "PROVENANCE_FILE_NAME", "PROVENANCE_RESULTS",
    "PROVENANCE_SCHEMA_VERSION", "ProvenanceError", "RecordedRun",
    "build_run_record", "dependency_versions", "hash_named_files",
    "record_research_run", "sha256_file", "write_run_record",
    # stable researcher Python API (v0.1 equivalence obligations)
    "ASSUMPTION_REQUIRED", "COMPILE_FAILURE", "PARSE_FAILURE",
    "REPORT_FILE_NAME",
    "RESULT_FILE_NAME", "RESULT_SCHEMA_VERSION", "GeneratedReport",
    "HypothesisVerificationResult", "ObligationVerification",
    "generate_report", "verify_hypothesis",
    # public-output secret redaction (defence in depth; not an env reader)
    "REDACTED", "redact_public_data", "redact_text",
]
