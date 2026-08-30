# F0 — historical P0 RAW free-form baseline

Status: compatibility boundary only; no new scientific or live LLM run.

F0 byte-locks the historical P0 RAW system/condition prompt and parser to the
closed experiment authority `0cdde49`. A public RPS case is adapted without
reading source dossiers, reference programs, verification evidence, depth
labels, or gold roles. Member IDs are deterministically mapped to the legacy
`G0001` form; the mapping and all prompt/input hashes are recorded.

The old prompt/parser architecture is retained, but its former client-side
private-reasoning capture is not: new runs must retain only the final response,
usage, request provenance, and hashes. No private reasoning body, tail, hash,
or length may be accessed or stored.

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
