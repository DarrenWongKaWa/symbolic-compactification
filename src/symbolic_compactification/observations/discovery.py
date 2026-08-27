"""Backend availability. Optional backends never make the core unusable."""
from __future__ import annotations

import importlib.util
import shutil
from typing import Optional

BACKEND_ORDER = ("sympy", "matchpy", "egglog", "lgg", "cadabra", "form", "metatheory")

OPTIONAL = frozenset({"matchpy", "egglog", "lgg", "cadabra", "form", "metatheory"})

FUTURE_ABSTRACTION = ("dreamcoder", "llm")


def _has_mod(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def probe_backend(name: str) -> str:
    if name == "sympy":
        return "AVAILABLE" if _has_mod("sympy") else "UNAVAILABLE"
    if name == "matchpy":
        return "AVAILABLE" if _has_mod("matchpy") else "OPTIONAL / unavailable"
    if name == "egglog":
        return "AVAILABLE" if _has_mod("egglog") else "OPTIONAL / unavailable"
    if name == "lgg":
        try:
            import research.abstraction_invention.prototype.antiunify  # noqa: F401
            return "AVAILABLE"
        except Exception:
            return "OPTIONAL / unavailable"
    if name == "cadabra":
        exe = shutil.which("cadabra2") or shutil.which("cadabra")
        return "AVAILABLE" if exe else "OPTIONAL / unavailable"
    if name == "form":
        exe = shutil.which("form") or shutil.which("tform")
        return "AVAILABLE" if exe else "OPTIONAL / unavailable"
    if name == "metatheory":
        return "OPTIONAL / unavailable"
    return "UNKNOWN"


def backend_status() -> dict[str, str]:
    return {n: probe_backend(n) for n in BACKEND_ORDER}


def version_of(name: str) -> Optional[str]:
    try:
        if name == "sympy":
            import sympy
            return getattr(sympy, "__version__", None)
        if name == "matchpy":
            import matchpy
            return getattr(matchpy, "__version__", None)
        if name == "egglog":
            import egglog
            return getattr(egglog, "__version__", "installed")
        if name == "lgg":
            return "frozen-antiunify@efc0924"
    except Exception:
        return None
    return None
