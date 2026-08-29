# Program IR

Machine object for a representation program. Free-form prose is not a
search state and not a program.

## Object

```
H = (F, {A_i}, {O_i}, {theta_i}, assumptions)
A_i = O_i[F; theta_i]
```

Complete program fields:

| field | required |
|---|---|
| program_id | canonical hash of the rest |
| grammar_version | `RepresentationGrammarV1` |
| latent_objects | list of typed F’s with symbolic cores |
| node_structures | NODES[…] objects |
| operators | typed O_i with latent + args |
| member_assignments | catalog source_node_id → reconstruction |
| instance_maps | theta_i |
| assumptions_used | DECLARED or DERIVED only |
| reconstruction | executable rule per assigned member |
| obligations | exact identities to verify |

## Serialization

- JSON object, keys sorted, no NaN.
- Symbolic cores as strings in the frozen parser dialect (no silent
  whitelist extension).
- Canonical hash: SHA-256 of the canonical JSON **without** score,
  timestamps, or LLM traces.
- Two programs that differ only by renaming bound parameters must
  hash equal after α-normalization of latent parameter names
  (`z0`, `z1`, … in bind order). Member IDs are **not** α-renamed
  (they are source catalog IDs).

## Completeness

A program is **complete** iff every claimed `A_i` has:

1. a catalog `source_node_id`;
2. an explicit operator (not “other”);
3. explicit theta / nodes;
4. a reconstruction that compiles.

Partial programs (unexplained members) are valid **search states**,
not PROGRAM_SUCCESS.

## Compilation

Compilation produces a list of proof obligations. Fail-closed:

- unparseable latent or member → COMPILE_FAILURE
- ill-typed operator → COMPILE_FAILURE
- catalog ID not in the task catalog → invalid source member

Verifier outcomes: ZERO, NONZERO, UNKNOWN, COMPILE_FAILURE.

UNKNOWN is not rejection. NONZERO is a hard gate for success.

## Tautology (IR-level)

A program is tautological if each assigned member is reconstructed
only by VALUE of a latent that **is** that member, with no shared F
across ≥2 non-identical members and no nontrivial operator
(NEWTON_DD, HERMITE_DD, DERIVATIVE, RECURRENCE, BASIS_*, COMPOSE of
those). Independent memorization of each expression is not a
representation.
