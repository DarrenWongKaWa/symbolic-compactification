"""Failure, gain, and DD-gate labels. Never collapse P/D/G/C/V/I."""
from __future__ import annotations

LAYERS = ("P", "D", "G", "C", "V", "I")

# Phase 7 DD decisive-experiment classes.
DD_CLASSES = (
    "DD-D",   # model did not propose correct representation
    "DD-G",   # correct type but source grounding failed
    "DD-C",   # grounded type but compiler failed
    "DD-V0",  # obligation NONZERO
    "DD-VU",  # obligation UNKNOWN
    "DD-OK",  # explicit grounded DD + ZERO
)

# Phase 15 false-discovery audit classes.
AUDIT_CLASSES = (
    "TRUE_STRUCTURAL_DISCOVERY",
    "SHALLOW_REPACKAGING",
    "TAUTOLOGICAL_MASTER",
    "UNNECESSARY_STRUCTURE",
    "WRONG_MEMBER_SELECTION",
    "WRONG_OPERATOR",
    "WRONG_DD_NODE_STRUCTURE",
    "WRONG_CONFLUENCE",
    "UNGROUNDABLE",
    "COMPILE_FAILURE",
    "NONZERO",
    "UNKNOWN",
)

# Gain accounting: never confuse these.
GAIN_CLASSES = (
    "discovery_gain",   # P2 emits a representation type/structure absent from frozen P1
    "grounding_gain",   # same structure now bindable because the contract names G####
    "compiler_gain",    # old output becomes verifiable because the compiler improved
    "verifier_bound",   # compiled, but V returns UNKNOWN
)

COMPILE_FAILURE = "COMPILE_FAILURE"
VERDICT_ZERO = "ZERO"
VERDICT_NONZERO = "NONZERO"
VERDICT_UNKNOWN = "UNKNOWN"

# Proposer-visible files must not contain these Guo gold strings.
FORBIDDEN_GOLD_PATTERNS = (
    r"Phi_Gamma",
    r"phi_gamma",
    r"φ_Γ",
    r"\bL[4-7]\b",
    r"PRB master",
    r"nine generator",
)

# Verbal DD is not discovery.
VERBAL_ONLY_TYPES = (
    "might be a divided difference",
    "looks like confluence",
)
