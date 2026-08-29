"""Assumption-complete case IR. Guo hop ZERO is not a success here."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

DECLARED = "DECLARED"
DERIVED = "DERIVED"
NOT_DECLARED = "NOT_DECLARED"
PREDICATE_LABELS = (DECLARED, DERIVED, NOT_DECLARED)

METHOD_VERSION = "ac-repr-1"

LADDER = (
    "R0_repeated_local",
    "R1_parameterized_family",
    "R2_newton_dd",
    "R3_hermite_dd",
    "R4_piecewise_unification",
    "R5_special_function",
    "R6_master_object",
    "R7_master_library",
    "R8_invariant_generator",
)


@dataclass
class Predicate:
    statement: str
    label: str = NOT_DECLARED
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScientificAssumptionContract:
    """Required for every scientific task."""

    symbol_assumptions: dict[str, dict[str, Any]] = field(default_factory=dict)
    function_domains: dict[str, str] = field(default_factory=dict)
    nonzero_conditions: list[Predicate] = field(default_factory=list)
    positivity_conditions: list[Predicate] = field(default_factory=list)
    real_valued_functions: list[str] = field(default_factory=list)
    analytic_domains: list[Predicate] = field(default_factory=list)
    branch_conventions: list[str] = field(default_factory=list)
    limit_domains: list[Predicate] = field(default_factory=list)
    source_provenance: list[str] = field(default_factory=list)
    derived_conditions: list[Predicate] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for key in (
            "nonzero_conditions",
            "positivity_conditions",
            "analytic_domains",
            "limit_domains",
            "derived_conditions",
        ):
            d[key] = [
                p.to_dict() if isinstance(p, Predicate) else p for p in getattr(self, key)
            ]
        return d

    def has_not_declared_analytic(self) -> bool:
        for pred in self.analytic_domains + self.limit_domains:
            label = pred.label if isinstance(pred, Predicate) else pred.get("label")
            if label == NOT_DECLARED:
                return True
        return False


@dataclass
class CandidateDossier:
    """Case-miner output. Not an admitted benchmark task."""

    case_id: str
    title: str
    domain: str
    expression_sketch: str
    latent_structure: str
    proposed_ladder: str = ""
    assumption_contract: Optional[ScientificAssumptionContract] = None
    public_source: str = ""
    why_not_cse_lgg: str = ""
    proposer_leak_risk: str = ""
    notes: str = ""
    rejected: bool = False
    reject_reason: str = ""
    is_guo: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        ac = self.assumption_contract
        d["assumption_contract"] = ac.to_dict() if isinstance(ac, ScientificAssumptionContract) else ac
        return d


def guo_is_not_admitted(dossier: CandidateDossier) -> bool:
    """Guo cannot enter DEV/TEST in this line."""
    return (not dossier.is_guo) and "guo" not in (dossier.case_id + dossier.title).lower()
