"""Certificate cache keys. Never reuse a proof across different expressions.

Track V4 hazard: MAP members may lack ``text_sha256``. A key of
(None, None, var, point) reused G0014→G0012 for G0016→G0013.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Optional

from research.coefficient_laurent.schema import METHOD_VERSION

PROOF_METHOD_VERSION = METHOD_VERSION


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode()).hexdigest()


def member_text_hash(member: Mapping[str, Any] | None, *, text: str = "") -> str:
    """Prefer explicit hash only if it matches the canonical full text.

    If ``text_sha256`` is absent or disagrees with ``text``, hash ``text``.
    Empty text is not a reusable key fragment.
    """
    canonical = sha256_text(text)
    stored = ""
    if member:
        stored = str(member.get("text_sha256") or "")
        if not text:
            text = str(member.get("text") or "")
            canonical = sha256_text(text)
    if not text:
        raise ValueError("refusing cache key: empty member text")
    if stored and stored != canonical:
        return canonical
    return canonical


def certificate_key(
    *,
    source_text: str,
    target_text: str,
    degeneration_variable: str,
    target_value: str,
    assumptions: Mapping[str, Any] | None = None,
    proof_method_version: str = PROOF_METHOD_VERSION,
    atom_decomposition_hash: str = "",
    source_member: Mapping[str, Any] | None = None,
    target_member: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    src_h = member_text_hash(source_member, text=source_text)
    tgt_h = member_text_hash(target_member, text=target_text)
    assum = sha256_text(json.dumps(assumptions or {}, sort_keys=True, default=str))
    if not atom_decomposition_hash:
        atom_decomposition_hash = sha256_text("")
    return (
        src_h,
        tgt_h,
        str(degeneration_variable),
        str(target_value),
        assum,
        str(proof_method_version),
        str(atom_decomposition_hash),
    )


class CertificateCache:
    """In-memory cache. Collision of distinct expressions is a hard error."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, ...], dict[str, Any]] = {}

    def get(self, key: tuple[str, ...]) -> Optional[dict[str, Any]]:
        return self._store.get(key)

    def put(self, key: tuple[str, ...], cert: Mapping[str, Any]) -> None:
        self._store[key] = dict(cert)

    def get_or_put(self, key: tuple[str, ...], cert: Mapping[str, Any]) -> dict[str, Any]:
        existing = self.get(key)
        if existing is None:
            self.put(key, cert)
            return dict(cert)
        return existing
