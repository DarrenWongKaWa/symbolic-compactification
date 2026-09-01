# Paper audit

A paper audit is a typed check of author-claimed derivations, not a
score of the paper. Public audit demos under `examples/audit/` and
`tests/fixtures/audit_demos/` are synthetic. They are not unpublished
manuscripts.

1. Inventory numbered equations (printed numbers, not TeX labels).
2. Record only source-supported relations. Adjacent numbering is not a
   derivation.
3. Lower what the frozen engine can check.
4. Emit a human-readable table. `ZERO` is generated, never authored.

```bash
cp -R examples/audit/minimal /tmp/ssc-audit
symbolic-compactification audit verify /tmp/ssc-audit
symbolic-compactification audit table /tmp/ssc-audit
```

That toy workspace contains:

- a definition (`STRUCTURAL`)
- two exact Laurent-coefficient identities (`ZERO`)
- an enclosing `O(g)` remainder (`UNKNOWN`)

Finite coefficient `ZERO` is not a remainder proof.

## Flagship

The Guo et al. full-paper audit inventories every numbered equation in
arXiv:2511.16422v2 and checks only source-grounded relations:

[examples/flagship/guo/RESULTS.md](../examples/flagship/guo/RESULTS.md)

Human-facing HTML projection (does not assign verdicts):
[examples/flagship/guo/human_audit/index.html](../examples/flagship/guo/human_audit/index.html).

Replay from frozen manifests:
[examples/flagship/guo/REPRODUCE.md](../examples/flagship/guo/REPRODUCE.md)

## Semantics

`ZERO` is never `CERTIFIED_BY_RULE`. Brillouin-zone integration by parts
is a local Leibniz `ZERO` plus a declared torus rule. See
[semantics.md](semantics.md) and [edge-types.md](edge-types.md).

Only obligations returning exact ZERO may appear as machine-verified.
