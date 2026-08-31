# Merge log — derivation audit v0.2

## PHASE 0 — interface freeze

- Branch `engineering/derivation-audit-v0.2` created from
  `research-preview-v0.1.0-alpha` (`c27378f`).
- Frozen: status taxonomy, edge types, table inclusion, evidence record
  fields, CLI names, privacy rules, audit workspace layout.
- `audit init` / `audit inspect` implemented against the freeze.
- Remaining layers are stubbed with stable function signatures.

Subsequent swarm commits are recorded below as they merge.

## PHASE 1–2 — implementation swarm (merged)

- E2 inventory (`2c5d61f`)
- E3 edges (`67009fd`)
- E4 lowering (`ee49b83`)
- E5 evidence (`82a7625`)
- E6 tables/report (`8aeb8e1`)
- E8 reviewer package (`dd2d3ed`)
- E9 HTML (`55a0d14`)
- E14 privacy (`f2204af`)
- E15 docs (`d79b6ba`)
- Public demos A/B/C (`aa2b7d1`)

Coordinator integration: edge YAML aliases (`id`/`edge_id`, `type`/`edge_type`,
`from`/`source_from`); assumption gate lists only undeclared names, not every
workspace symbol on every edge; inspect probes optional layers; adversarial
and demo e2e release-critical tests.
