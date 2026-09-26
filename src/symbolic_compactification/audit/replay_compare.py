"""Compare a fresh replay with the machine records shipped in a package.

Record integrity checks shape and internal consistency. They cannot show
who wrote a record: a hand-edited ``machine_records.json`` with valid-looking
hashes passes them. Authenticity comes from replay. ``reproduce.sh``
re-verifies the bundled sources and then calls this comparison, which fails
when any edge's status, engine result, rule, residual binding, or rule
conclusion differs from what the package claims.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .io import MAX_SOURCE_BYTES, read_bytes
from .schema import AuditError, AuditRecord, record_from_mapping

_HASH_SUFFIX = "; remainder certificate"


def load_record_file(path: Path) -> tuple[AuditRecord, ...]:
    """Records from a run's machine_records.json (list or {"records": [...]})."""
    try:
        payload = json.loads(read_bytes(Path(path), max_bytes=MAX_SOURCE_BYTES))
    except (OSError, ValueError) as exc:
        raise AuditError("RECORDS_FILE_INVALID", str(exc)[:300], path=str(path)) from None
    if isinstance(payload, dict):
        payload = payload.get("records")
    if not isinstance(payload, list) or not all(isinstance(r, dict) for r in payload):
        raise AuditError("RECORDS_FILE_INVALID", "expected a list of records", path=str(path))
    return tuple(record_from_mapping(item) for item in payload)


def _conclusion(record: AuditRecord) -> Optional[str]:
    if record.rule_certificate is None:
        return None
    # The remainder hash also covers numerical cross-check digits, which may
    # differ between library versions; the exact limit before it must match.
    return record.rule_certificate.conclusion.split(_HASH_SUFFIX)[0]


def _signature(record: AuditRecord) -> dict:
    return {
        "edge_type": record.edge_type,
        "status": record.status,
        "result": record.result,
        "rule_id": record.rule_certificate.rule_id if record.rule_certificate else None,
        "conclusion": _conclusion(record),
        "residual_hash": record.residual_hash,
    }


def compare_records(recorded: tuple[AuditRecord, ...],
                    replayed: tuple[AuditRecord, ...]) -> list[dict]:
    """Every difference between the claimed and the replayed records."""
    claimed = {r.edge_id: _signature(r) for r in recorded}
    fresh = {r.edge_id: _signature(r) for r in replayed}
    problems: list[dict] = []
    for edge_id in sorted(set(claimed) | set(fresh)):
        if edge_id not in fresh:
            problems.append({"edge_id": edge_id, "issue": "MISSING_FROM_REPLAY"})
        elif edge_id not in claimed:
            problems.append({"edge_id": edge_id, "issue": "NOT_IN_PACKAGE"})
        else:
            for field, value in claimed[edge_id].items():
                if fresh[edge_id][field] != value:
                    problems.append({"edge_id": edge_id, "issue": "FIELD_DIFFERS",
                                     "field": field, "package": value,
                                     "replay": fresh[edge_id][field]})
    return problems
