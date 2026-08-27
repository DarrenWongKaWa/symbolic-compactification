"""Parse model JSON into RepresentationHypothesisV2. Aliases are not repaired."""
from __future__ import annotations

from typing import Any

from research.llm_abstraction.parser import extract_json_object
from research.representation_invention.schema import PARSE_FAILURE, parse_document_v2


def parse_p2(text: str, catalog: set[str]) -> dict[str, Any]:
    """extract_json_object then parse_document_v2. No alias repair."""
    obj, err = extract_json_object(text)
    if obj is None:
        return {
            "parse_status": PARSE_FAILURE,
            "parse_error": err,
            "hypotheses": [],
            "abstain": False,
            "n_ok": 0,
            "n_parse_failure": 0,
        }
    return parse_document_v2(obj, catalog)
