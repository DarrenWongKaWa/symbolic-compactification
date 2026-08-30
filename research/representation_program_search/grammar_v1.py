"""RepresentationGrammarV1 constants. No search. No TEST-driven operators."""
from __future__ import annotations

GRAMMAR_ID = "RepresentationGrammarV1"
METHOD_VERSION = "rps-1"

LATENT_FORMS = (
    "FUNCTION_1",
    "FUNCTION_2",
    "MATRIX_FUNCTION",
    "SCALAR_KERNEL",
    "TENSOR_GENERATOR",
    "BASIS_OBJECT",
)

OPERATORS = (
    "VALUE",
    "SUBSTITUTE",
    "DERIVATIVE",
    "SHIFT",
    "PERMUTE",
    "NEWTON_DD",
    "HERMITE_DD",
    "RECURRENCE",
    "LINEAR_COMBINATION",
    "BASIS_PROJECT",
    "BASIS_RECONSTRUCT",
    "COMPOSE",
)

# DEV-only promotions. Not in V1 until DEV evidence. Not for TEST patching.
OPTIONAL_LATER = (
    "RESOLVENT",
    "GENERATING_FUNCTION",
    "BLOCK_OPERATOR",
)

ACTIONS = (
    "CREATE_LATENT",
    "ADD_MEMBER",
    "GROUP_MEMBERS",
    "ADD_PARAMETER",
    "SUBSTITUTE_PARAMETER",
    "ADD_DERIVATIVE",
    "ADD_NEWTON_DD",
    "ADD_REPEATED_NODE",
    "ADD_HERMITE_DD",
    "ADD_RECURRENCE",
    "ADD_PERMUTATION",
    "ADD_LINEAR_COMBINATION",
    "ADD_COMPOSE",
    "CREATE_BASIS",
    "RECONSTRUCT_FROM_BASIS",
    "REMOVE_REDUNDANT_OBJECT",
)

ABLATIONS = ("G_FULL", "G_NO_HERMITE", "G_PRIMITIVE")

G_PRIMITIVE_OPS = (
    "VALUE",
    "DERIVATIVE",
    "SUBSTITUTE",
    "LINEAR_COMBINATION",
    "COMPOSE",
)

SCORE_LAMBDAS = {"lambda1": 1, "lambda2": 1, "lambda3": 1, "lambda4": 2}
BUDGET_STATES = (10, 50, 100, 500, 1000)
CONDITIONS = ("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "F0")
