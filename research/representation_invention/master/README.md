# Owner: Subagent B — Master-object induction

Formalize `A_i = O_i[F]` hypotheses. Gold-free quality score.

Reject tautologies: `F := A1` used once.

Score axes: coverage, reuse, parameter coherence, operator coherence,
description-length gain, structural depth.

Public API: `score_master_hypothesis`, `instantiate_operator`.
Instantiation is fail-closed (`None`); shallow wrappers are scored, not rewritten.

Do not use hidden Guo names. Import V2 schema; do not edit it.
