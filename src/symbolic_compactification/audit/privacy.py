"""Privacy firewall and private-offline mode for derivation audit.

Unpublished local validation material is never release evidence.  Public
engineering decisions must be justified by public or synthetic fixtures.
This module contains no manuscript identifiers.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

from .schema import AuditError

PRIVATE_OFFLINE_ENV = "SSC_PRIVATE_OFFLINE"
PRIVATE_VALIDATION_DIRNAME = ".private_validation"
PRIVATE_DENYLIST_RELPATH = ".private_validation/private_denylist.txt"

# Paths that must never be packaged, documented as examples, or committed
# from an audit workspace into the public repository.
PRIVATE_PATH_PREFIXES = (
    ".private_validation/",
)

# Host-absolute prefixes that inventory/verify/package must refuse to read
# when private-offline mode is active.  Kept generic on purpose.
REFUSED_NETWORK_PREFIXES = (
    "http://",
    "https://",
    "ftp://",
)


def private_offline_enabled(environ: Optional[dict] = None) -> bool:
    env = os.environ if environ is None else environ
    return str(env.get(PRIVATE_OFFLINE_ENV, "")) == "1"


def refuse_network_if_private_offline(target: str) -> None:
    """Fail closed if a network-shaped target is requested in private mode."""
    if not private_offline_enabled():
        return
    lowered = target.strip().lower()
    if any(lowered.startswith(prefix) for prefix in REFUSED_NETWORK_PREFIXES):
        raise AuditError(
            "PRIVATE_OFFLINE_NETWORK_REFUSED",
            "private-offline mode allows only local deterministic verification",
        )


def refuse_proposer_if_private_offline() -> None:
    if private_offline_enabled():
        raise AuditError(
            "PRIVATE_OFFLINE_PROPOSER_DISABLED",
            "the proposer is disabled while SSC_PRIVATE_OFFLINE=1",
        )


def is_private_relpath(relative: str) -> bool:
    # Strip only "./" and leading slashes. str.lstrip("./") would also
    # consume the leading dots of ".private_validation/".
    normalized = relative.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.lstrip("/")
    return any(
        normalized == prefix.rstrip("/") or normalized.startswith(prefix)
        for prefix in PRIVATE_PATH_PREFIXES
    )


def load_denylist(root: Path) -> tuple[str, ...]:
    """Load an optional local denylist. Missing file => empty (public CI).

    The denylist file is gitignored.  Patterns are compared as case-sensitive
    substrings against candidate text.  Never commit the file or its hits.
    """
    path = root / PRIVATE_DENYLIST_RELPATH
    if not path.is_file():
        return ()
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        item = raw.strip()
        if not item or item.startswith("#"):
            continue
        lines.append(item)
    return tuple(lines)


def scan_text_for_denylist(text: str, denylist: Iterable[str]) -> tuple[str, ...]:
    """Return denylist items that occur in ``text``. Does not log the hits."""
    hits = []
    for item in denylist:
        if item and item in text:
            hits.append(item)
    return tuple(hits)


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def scan_paths(directory: Path, *, root: Optional[Path] = None) -> bool:
    """True if any UTF-8 file under ``directory`` matches the denylist.

    Denylist is loaded from ``root`` (default: ``directory``). A missing
    denylist is empty and returns False (public CI). Private validation
    paths are skipped so the denylist file cannot self-match.
    """
    directory = Path(directory)
    denylist_root = Path(root) if root is not None else directory
    denylist = load_denylist(denylist_root)
    if not denylist:
        return False
    try:
        if not directory.is_dir():
            return False
    except OSError:
        return False
    for path in directory.rglob("*"):
        try:
            if not path.is_file() or path.is_symlink():
                continue
        except OSError:
            continue
        relative = _relative_posix(path, denylist_root)
        if is_private_relpath(relative) or PRIVATE_VALIDATION_DIRNAME in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if scan_text_for_denylist(text, denylist):
            return True
    return False
