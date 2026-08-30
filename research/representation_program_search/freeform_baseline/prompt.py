"""Public-case adapter for the byte-frozen historical P0 RAW prompt."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from research.assumption_complete_representation.eval.ac_prompts import messages_for
from research.representation_program_search.program_ir import canonical_json
from research.representation_program_search.program_ir.model import thaw_json
from research.representation_program_search.search import PublicCase

from .authority import F0_AUTHORITY_COMMIT, F0_AUTHORITY_FILES, validate_f0_authority


class F0ContractError(ValueError):
    pass


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _assumption_lines(value: Any) -> list[str]:
    thawed = thaw_json(value)
    if isinstance(thawed, Mapping) and isinstance(thawed.get("predicates"), list):
        predicates = thawed["predicates"]
    elif isinstance(thawed, list):
        predicates = thawed
    else:
        predicates = [thawed]
    # Canonical JSON is presentation-only and does not interpret or repair the
    # scientific contract.  The exact assumptions hash is separately bound.
    return [canonical_json(item) for item in predicates]


def _legacy_pack(case: PublicCase) -> tuple[dict[str, Any], dict[str, str]]:
    id_map = {
        member.member_id: f"G{index:04d}"
        for index, member in enumerate(case.members, 1)
    }
    pack = {
        "assumptions": _assumption_lines(case.assumptions),
        "catalog": [
            {
                "kind": "expr",
                "source_node_id": id_map[member.member_id],
                "text": member.expression,
            }
            for member in case.members
        ],
        # No evaluator/source dossier is read to fabricate historical
        # scientific context. All source expressions remain in the catalog.
        "current": "",
        "functions": list(case.functions),
        "public_id": case.case_id,
        "scientific_context": [],
        "symbols": [thaw_json(item) for item in case.symbols],
    }
    return pack, id_map


@dataclass(frozen=True)
class F0Prompt:
    messages: tuple[Mapping[str, str], ...]
    hashes: Mapping[str, str]
    source_id_map: Mapping[str, str]
    proposer_view_sha256: str
    assumptions_sha256: str
    authority_commit: str = F0_AUTHORITY_COMMIT
    condition: str = "P0"
    result_condition: str = "F0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "assumptions_sha256": self.assumptions_sha256,
            "authority_commit": self.authority_commit,
            "authority_files": dict(sorted(F0_AUTHORITY_FILES.items())),
            "condition": self.condition,
            "hashes": dict(self.hashes),
            "messages": [dict(item) for item in self.messages],
            "private_reasoning_requested": False,
            "proposer_view_sha256": self.proposer_view_sha256,
            "result_condition": self.result_condition,
            "source_id_map": dict(self.source_id_map),
        }


def build_f0_prompt(case: PublicCase) -> F0Prompt:
    failures = validate_f0_authority(_repository_root())
    if failures:
        raise F0ContractError(failures[0])
    pack, id_map = _legacy_pack(case)
    messages, hashes = messages_for(pack, "P0")
    return F0Prompt(
        messages=tuple(messages),
        hashes=dict(hashes),
        source_id_map=id_map,
        proposer_view_sha256=case.proposer_view_sha256,
        assumptions_sha256=hashlib.sha256(
            canonical_json(thaw_json(case.assumptions)).encode("utf-8")
        ).hexdigest(),
    )
