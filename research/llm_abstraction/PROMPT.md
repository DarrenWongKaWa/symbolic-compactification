# Proposer prompts

System prompt is frozen in `prompts.py` (`SYSTEM_PROMPT`).

The model is told:

- it is **not** a verifier;
- it may propose speculative structure;
- it must not claim exact equivalence;
- it must not invent physical interpretation unless supplied;
- it should prefer hypotheses that explain multiple non-identical expressions;
- it must not introduce interpolation / geodesics / latent-space machinery unless the source requires it;
- every hypothesis lists members, latent object, generation maps, and proof obligations;
- the verifier decides truth.

User payloads differ **only** by condition:

| condition | contents |
|---|---|
| A0 / L0 / G0 | raw expression, symbols, functions, assumptions, generic task |
| A1 / L1 / G1 | A0 + basic size/symbol/function/branch/index summary |
| A2 / L2 / G2 | A0 + ranked SOL packets |
| A3 / L3 / G3 | packets + local member expressions only (full raw omitted) |

Packets contain observations (relation type, backend, exactness class, witness).
They must not contain scientific slogans.

Do not retune prompts on TEST. Flash uses the same prompts as Pro.
