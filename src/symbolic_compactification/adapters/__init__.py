"""Ingestion adapters: translate foreign expression TEXT into SymPy objects.

Adapters are translation layers only. They never execute a second CAS and
never certify anything: every expression they produce still flows through
the engine's strict parser and exact verifier before it can earn a verdict.
"""
from .wolfram_text import (
    DEFAULT_FUNC_MAP,
    TranslationResult,
    WolframAdapterError,
    WolframStructureError,
    WolframSyntaxError,
    WolframTokenError,
    extract_expression_text,
    strip_wolfram_comments,
    translate_wolfram_text,
)

__all__ = [
    "DEFAULT_FUNC_MAP",
    "TranslationResult",
    "WolframAdapterError",
    "WolframStructureError",
    "WolframSyntaxError",
    "WolframTokenError",
    "extract_expression_text",
    "strip_wolfram_comments",
    "translate_wolfram_text",
]
