# RepresentationGrammarV1

Versioned grammar for representation **programs**. Do not add operators
because a TEST task needs them. Optional operators (RESOLVENT,
GENERATING_FUNCTION, BLOCK_OPERATOR) only if **DEV** evidence requires
them, and only as a new grammar version.

## Latent-object forms

| form | meaning |
|---|---|
| FUNCTION_1 | univariate F(z) |
| FUNCTION_2 | bivariate F(z,w) |
| MATRIX_FUNCTION | f of a matrix/algebra element |
| SCALAR_KERNEL | scalar kernel, e.g. 1/(z-a) |
| TENSOR_GENERATOR | generating tensor / invariant seed |
| BASIS_OBJECT | finite basis / projector family |

A program may contain several latent objects. Prefer one.

## Primitive operators

| operator | arity / notes |
|---|---|
| VALUE | evaluate F at a node |
| SUBSTITUTE | substitute a parameter |
| DERIVATIVE | d/dθ or ∂/∂node |
| SHIFT | translate an argument |
| PERMUTE | permute arguments / indices |
| NEWTON_DD | first (or iterated) Newton divided difference on **distinct** nodes |
| HERMITE_DD | divided difference on a **NODES** object with multiplicity |
| RECURRENCE | one-step recurrence in an index |
| LINEAR_COMBINATION | finite explicit linear combination |
| BASIS_PROJECT | project onto a declared basis element |
| BASIS_RECONSTRUCT | reconstruct from basis coefficients |
| COMPOSE | compose operators / functions |

`ADD_COMPOSE` is the legal search action that instantiates the already-declared
`COMPOSE` operator. This access path is required for `G_PRIMITIVE`; its
presence does not add a new mathematical primitive to the grammar.

NEWTON_DD and HERMITE_DD are **structurally different**. Hermite is not
Newton plus English “repeated node.”

## Node structures (multiplicity is first-class)

```
NODES[x, y]        # two distinct simple nodes
NODES[x, x]        # multiplicity 2 at x
NODES[x, x, y]     # Hermite: x twice, y once
NODES[x, x, x]     # multiplicity 3
```

Do not encode repeated nodes as prose. A search state that claims
Hermite without a NODES object with a repeated label is ill-typed.

## Grammar ablations (frozen names)

| id | operators |
|---|---|
| G_FULL | all primitives above |
| G_NO_HERMITE | G_FULL minus HERMITE_DD (repeated NODES still allowed; Hermite must be composed) |
| G_PRIMITIVE | VALUE, DERIVATIVE, SUBSTITUTE, LINEAR_COMBINATION, COMPOSE only |

If PROGRAM_SUCCESS exists only under a named HERMITE_DD / MASTER-like
primitive, do not overclaim invention (outcome CASE C).

## Typing

- Every operator has an explicit latent, explicit arguments, explicit
  output member or intermediate.
- VALUE(F, x) is well-typed only if F is FUNCTION_1 / SCALAR_KERNEL /
  MATRIX_FUNCTION as declared.
- NEWTON_DD(F, NODES[x,y]) requires x ≠ y in the node list (as labels).
- HERMITE_DD(F, NODES[…]) requires at least one repeated label.
- Illegal free-form operators are rejected at the grammar, not repaired.

## What the heuristic may see

Source expressions, catalog, assumption contract, structural
observations, **legal** grammar actions/states.

## What it may not see

Target representation type, gold program, gold operator sequence,
hidden member roles.
