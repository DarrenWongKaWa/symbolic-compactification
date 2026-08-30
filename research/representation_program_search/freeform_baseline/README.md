# F0 — historical P0 RAW free-form baseline

Status: compatibility boundary and auditable runner implemented; no new
scientific or live LLM run.

F0 byte-locks the historical P0 RAW system/condition prompt and parser to the
closed experiment authority `0cdde49`. A public RPS case is adapted without
reading source dossiers, reference programs, verification evidence, depth
labels, or gold roles. Member IDs are deterministically mapped to the legacy
`G0001` form; the mapping and all prompt/input hashes are recorded.

The old prompt/parser architecture is retained, but its former client-side
private-reasoning capture is not: new runs must retain only the final response,
usage, request provenance, and hashes. No private reasoning body, tail, hash,
or length may be accessed or stored.

`runner.py` implements that boundary. It writes a hash-bound run header before
the provider call, accepts only the frozen DeepSeek model/configuration, and
persists the final assistant content plus explicit usage/provenance. It never
reads `reasoning_content`. Provider/API/provenance failures make the run
unavailable; there is no fallback. A malformed final JSON response remains an
available method outcome with `PARSE_FAILURE`, because format failure is a
scientific failure of F0 rather than missing infrastructure.

The runner does not evaluate its own output. `evaluator.py` implements the
separate evaluator-side boundary, so neither hidden representation labels nor
reference programs cross the proposer call:

- every parseable legacy equality is replayed through a persisted exact
  verifier session before the frozen legacy scorer sees a verdict;
- the legacy axis records only a hash of its evaluator-only authority;
- the no-repair typed translator accepts only complete unary-specialization
  programs with exact member/operator/instance maps and exact assumption-ID or
  canonical-predicate references;
- all other free-form programs are `FREEFORM_UNCOMPARABLE`;
- translated programs receive current `PROGRAM_SUCCESS` only through M1
  compilation and session-recorded ZERO for every required member.

## Outcome compatibility

Historical `OPERATIONAL_CORRECT` is not silently renamed `PROGRAM_SUCCESS`.
The old schema permits arbitrary operator prose and does not by itself create
a typed `RepresentationGrammarV1` program. New F0 reporting therefore has two
separate axes:

1. `F0_LEGACY_OPERATIONAL`: the frozen old parser/compiler outcome, retained
   for continuity and clearly labeled with its historical semantics;
2. `PROGRAM_SUCCESS`: available only if a deterministic, no-repair translator
   can construct a complete M1 program, every required equality receives
   session-recorded ZERO, and all current admission/leakage/non-tautology gates
   pass.

An untranslatable free-form response is `FREEFORM_UNCOMPARABLE`, not a search
failure and not evidence for or against the grammar. The headline comparison
must display the legacy and current axes together. This avoids granting F0 a
weaker success criterion or defining it to fail merely because it predates the
typed grammar.
