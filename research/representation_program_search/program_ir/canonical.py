"""Canonical serialization and alpha-normalized program hashes."""
from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any

from .model import RepresentationProgram

_IDENTIFIER = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")


def canonical_json(value: Any) -> str:
    """Return compact RFC-8259 JSON with deterministic key ordering."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _rename_identifier(text: str, renames: dict[str, str]) -> str:
    return _IDENTIFIER.sub(lambda match: renames.get(match.group(0), match.group(0)), text)


def _alpha_normalized_payload(program: RepresentationProgram) -> dict[str, Any]:
    """Normalize bound latent parameters, never source identities.

    Parameter scope is deliberately narrow.  It covers latent cores and
    parameter-designating operator/instance-map keys.  Source member ids,
    paths, hashes, node expressions, and external value expressions remain
    byte-for-byte unchanged.
    """
    payload = deepcopy(program.to_dict(include_program_id=False))
    by_latent: dict[str, dict[str, str]] = {}
    counter = 0
    for latent in payload["latent_objects"]:
        renames: dict[str, str] = {}
        for parameter in latent["parameters"]:
            renames[parameter] = f"z{counter}"
            counter += 1
        by_latent[latent["latent_id"]] = renames
        latent["parameters"] = [renames[item] for item in latent["parameters"]]
        latent["expression"] = _rename_identifier(latent["expression"], renames)

    all_renames: dict[str, str] = {}
    ambiguous: set[str] = set()
    for renames in by_latent.values():
        for old, new in renames.items():
            if old in all_renames and all_renames[old] != new:
                ambiguous.add(old)
            else:
                all_renames[old] = new
    for old in ambiguous:
        all_renames.pop(old, None)

    for operator in payload["operators"]:
        renames = by_latent.get(operator.get("latent_id"), {})
        args = operator["arguments"]
        for key in ("parameter", "variable"):
            if isinstance(args.get(key), str):
                args[key] = renames.get(args[key], args[key])
        if isinstance(args.get("parameters"), list):
            args["parameters"] = [renames.get(item, item) for item in args["parameters"]]
        if isinstance(args.get("values"), dict):
            args["values"] = {
                renames.get(name, name): value
                for name, value in args["values"].items()
            }

    for _member_id, instance_map in payload["instance_maps"].items():
        if isinstance(instance_map, dict):
            if instance_map and set(instance_map) <= set(by_latent) and all(
                isinstance(value, dict) for value in instance_map.values()
            ):
                for latent_id, values in instance_map.items():
                    renames = by_latent[latent_id]
                    instance_map[latent_id] = {
                        renames.get(name, name): value
                        for name, value in values.items()
                    }
                continue
            replacement: dict[str, Any] = {}
            for name, value in instance_map.items():
                replacement[all_renames.get(name, name)] = value
            instance_map.clear()
            instance_map.update(replacement)
    return payload


def canonical_program_hash(program: RepresentationProgram) -> str:
    """SHA-256 of the alpha-normalized program, excluding ``program_id``."""
    encoded = canonical_json(_alpha_normalized_payload(program)).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
