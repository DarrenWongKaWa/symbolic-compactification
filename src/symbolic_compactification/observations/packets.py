"""Ranked structural packets for a future proposer. No interpretation."""
from __future__ import annotations

from collections import defaultdict

from symbolic_compactification.observations.ir import ObservationBundle


def rank_packets(bundle: ObservationBundle, *, cap: int = 24) -> list[dict]:
    by_type: dict[str, list] = defaultdict(list)
    for r in bundle.relations:
        by_type[r.relation_type].append(r)
    packets = []
    n = 0
    for rtype, rels in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        members = []
        for r in rels:
            members.extend(r.source_ids)
        members = list(dict.fromkeys(members))
        n += 1
        packets.append({
            "packet_id": f"F{n:02d}",
            "relation_type": rtype,
            "members": members[:16],
            "n_relations": len(rels),
            "backends": sorted({r.backend for r in rels}),
            "exactness_classes": sorted({r.exactness_class for r in rels}),
            "note": "observation only; not a scientific object name",
        })
        if n >= cap:
            break
    return packets
