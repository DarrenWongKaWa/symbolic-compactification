"""Experimental DeepSeek abstraction-proposer namespace.

Does not modify frozen SOL, B9, LGG, or Beyond-LGG artifacts.
Observation reports relations; this module proposes hypotheses;
the existing verifier decides exact truth.
"""

def __getattr__(name: str):
    if name == "propose_abstraction":
        from research.llm_abstraction.proposer import propose_abstraction
        return propose_abstraction
    if name in {"LLMStructureHypothesis", "ProposeResult"}:
        from research.llm_abstraction import schema
        return getattr(schema, name)
    raise AttributeError(name)


__all__ = [
    "propose_abstraction",
    "LLMStructureHypothesis",
    "ProposeResult",
]
