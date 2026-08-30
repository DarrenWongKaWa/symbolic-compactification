"""Typed, fail-closed executable IR for RepresentationGrammarV1.

The compiler constructs exact candidate expressions and proof obligations.  It
does not call the verifier and never assigns ZERO/NONZERO/UNKNOWN verdicts.
"""

from .canonical import canonical_json, canonical_program_hash
from .compiler import compile_program, is_tautological
from .loader import LoadedCasePackage, load_case_package
from .model import (
    CompileContext,
    CompiledObligation,
    CompilationResult,
    LatentObject,
    MemberAssignment,
    NodeStructure,
    Obligation,
    Operator,
    RepresentationProgram,
    SourceMember,
)

__all__ = [
    "CompileContext",
    "CompiledObligation",
    "CompilationResult",
    "LatentObject",
    "LoadedCasePackage",
    "MemberAssignment",
    "NodeStructure",
    "Obligation",
    "Operator",
    "RepresentationProgram",
    "SourceMember",
    "canonical_json",
    "canonical_program_hash",
    "compile_program",
    "is_tautological",
    "load_case_package",
]
