"""Many-body equivalence checks: Matsubara sums, asymptotic remainders,
real-frequency integrals, operator identities and Langreth rules.

See ``docs/many-body-equivalence.md`` for the forms covered, the theorem
behind each check, and how results map onto audit statuses.
"""
from ._common import DISTRIBUTION_FUNCTIONS, ManyBodyResult
from .asymptotic import (ASYMPTOTIC_REMAINDER_LIMIT, certify_remainder,
                         estimate_remainder_order)
from .integrals import NUMERICAL_SUPPORT, check_frequency_integral
from .keldysh import LANGRETH_KELDYSH_ALGEBRA, verify_langreth
from .matsubara import (MATSUBARA_POLES_OFF_AXIS, MATSUBARA_RESIDUE_THEOREM,
                        matsubara_closed_form, verify_matsubara_sum)
from .noncommutative import verify_operator_identity

__all__ = [
    "ASYMPTOTIC_REMAINDER_LIMIT",
    "DISTRIBUTION_FUNCTIONS",
    "LANGRETH_KELDYSH_ALGEBRA",
    "MATSUBARA_POLES_OFF_AXIS",
    "MATSUBARA_RESIDUE_THEOREM",
    "ManyBodyResult",
    "NUMERICAL_SUPPORT",
    "certify_remainder",
    "check_frequency_integral",
    "estimate_remainder_order",
    "matsubara_closed_form",
    "verify_langreth",
    "verify_matsubara_sum",
    "verify_operator_identity",
]
