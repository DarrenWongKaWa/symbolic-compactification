"""Many-body equivalence checks: Matsubara sums, asymptotic remainders,
real-frequency integrals, operator identities, Langreth rules, and
identities with divided differences, derivatives and series coefficients.

See ``docs/many-body-equivalence.md`` for the forms covered, the theorem
behind each check, and how results map onto audit statuses.
"""
from ._common import DISTRIBUTION_FUNCTIONS, ManyBodyResult
from .calculus import divided_difference, verify_identity, verify_series_coefficient
from .cards import run_card
from .fermi_integral import FERMI_RESIDUE_SPLITTING, verify_fermi_integral
from .asymptotic import (ASYMPTOTIC_REMAINDER_LIMIT, certify_remainder,
                         estimate_remainder_order)
from .integrals import NUMERICAL_SUPPORT, check_frequency_integral
from .numeric import check_numeric_equivalence
from .keldysh import LANGRETH_KELDYSH_ALGEBRA, verify_langreth
from .matsubara import (MATSUBARA_POLES_OFF_AXIS, MATSUBARA_RESIDUE_THEOREM,
                        matsubara_closed_form, verify_matsubara_sum)
from .noncommutative import verify_operator_identity
from .special import reflect_polygamma

__all__ = [
    "ASYMPTOTIC_REMAINDER_LIMIT",
    "DISTRIBUTION_FUNCTIONS",
    "FERMI_RESIDUE_SPLITTING",
    "LANGRETH_KELDYSH_ALGEBRA",
    "MATSUBARA_POLES_OFF_AXIS",
    "MATSUBARA_RESIDUE_THEOREM",
    "ManyBodyResult",
    "NUMERICAL_SUPPORT",
    "certify_remainder",
    "check_frequency_integral",
    "check_numeric_equivalence",
    "divided_difference",
    "estimate_remainder_order",
    "matsubara_closed_form",
    "reflect_polygamma",
    "run_card",
    "verify_fermi_integral",
    "verify_identity",
    "verify_langreth",
    "verify_matsubara_sum",
    "verify_operator_identity",
    "verify_series_coefficient",
]
