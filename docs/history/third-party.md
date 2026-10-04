# Attribution

This observation layer wraps existing systems. It does not re-license them.

- SymPy — BSD-3-Clause, sympy.org
- MatchPy — MIT, HPAC/matchpy
- egglog / egglog-python / egg — MIT, egraphs-good
- Cadabra2 — GPL-3, Kasper Peeters; used only as an optional executable
- FORM — GPL, J.A.M. Vermaseren et al.; optional executable
- Metatheory.jl — MIT (not integrated in v1)

No third-party source was copied into `src/`.
No patches were applied to upstream trees.

## Optional second engine (Wolfram)

- Wolfram Engine / Mathematica / `wolframscript` — proprietary, Wolfram
  Research. Used only as an optional, user-installed executable by the
  opt-in `--second-engine wolfram` check. Never bundled, imported, or
  required; it needs the user's own license and activation.

## First-party port

`src/symbolic_compactification/second_engine.py` adapts the B3 independent
ZERO engine of *Repo-Native Symbolic Science*
(`repo-native-symbolic-science`: `tools/independent_zero_engine.py`,
`tools/wolfram_runtime.py`). That work is Copyright 2026 Kawa Wong and is
licensed under the Apache License, Version 2.0; its NOTICE reads "This
product includes software developed by Kawa Wong." The same copyright
holder contributes the adapted code here under this repository's MIT
license.

Changes from the original: the `ast` serializer follows this package's
strict parser grammar (which gates it first) and renames every declared
symbol and function; discovery via environment override,
`PATH` and standard install locations instead of the pinned, code-signed
`/Applications/Wolfram Engine.app` path; process-group timeout handling;
and the agree / disagree / inconclusive / unavailable record combined
fail-closed with this package's ZERO / NONZERO / UNKNOWN verdicts.
