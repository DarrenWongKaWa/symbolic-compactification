# Search-state IR

A search state is a (possibly partial) program plus search metadata.
Natural-language transformations are not actions.

## State schema

```json
{
  "latent_objects": [],
  "member_assignments": {},
  "operators": [],
  "node_structures": [],
  "unexplained_members": [],
  "compiled_obligations": [],
  "verified_obligations": [],
  "complexity": 0,
  "score": null,
  "depth": 0,
  "grammar_id": "G_FULL",
  "canonical_hash": "",
  "parent_hash": null,
  "action_from_parent": null
}
```

`score` is null until the frozen scoring policy is applied. Score
never overrides NONZERO.

## Legal actions

CREATE_LATENT,
ADD_MEMBER,
GROUP_MEMBERS,
ADD_PARAMETER,
SUBSTITUTE_PARAMETER,
ADD_DERIVATIVE,
ADD_NEWTON_DD,
ADD_REPEATED_NODE,
ADD_HERMITE_DD,
ADD_RECURRENCE,
ADD_PERMUTATION,
ADD_LINEAR_COMBINATION,
CREATE_BASIS,
RECONSTRUCT_FROM_BASIS,
REMOVE_REDUNDANT_OBJECT.

Each action has a typed payload (latent id, catalog ids, NODES, etc.).
Illegal or free-form actions are rejected. LLM outputs that are not
in this set are discarded; they are not repaired into nearby legal
actions.

## Pruning (gold-free)

Allowed:

- exact NONZERO on a required obligation
- invalid source member
- impossible typing
- duplicate canonical_hash
- complexity bound
- assumption violation (NOT_DECLARED used)
- dominated state (same coverage, strictly higher complexity, no extra ZERO)

Forbidden:

- prune because it disagrees with hidden gold
- prune UNKNOWN (retain, lower priority per frozen policy)

## Budgets

Headline unit: **states expanded**.

Curves at 10, 50, 100, 500, 1000 states.

Also record wall time and LLM tokens. Do not substitute tokens for
state budget in the headline comparison.

## LLM audit fields (when used)

Every LLM-guided decision records:

- current search-state hash
- candidate legal actions or states
- LLM ranking / action JSON
- chosen next state hash
- token usage

No private chain-of-thought as a method input. No hidden NL search
outside this log.
