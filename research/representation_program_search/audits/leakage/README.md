# Duplicate and target-leakage audit

`audit.py` performs deterministic, gold-free screening of every new case
dossier against the repository's previous case and benchmark corpora.

It detects:

- exact source-formula reuse;
- alpha-renamed formula reuse;
- reviewable near-duplicate similarity;
- explicit references to Historical Diagnostic identities;
- sealed Guo names or the sealed `G0016 -> G0013` hop;
- literal grammar/action syntax and natural operator names in proposer-visible
  fields;
- target/member-role metadata inside the proposer projection;
- trivial top-level repeated-term CSE;
- declared R0/R1 or explicitly first-order-LGG-only tasks.

## Gold firewall

Similarity uses only source formula/catalog fields, title, and public source
identifiers. It excludes `latent_structure`, `proposed_ladder`, target types,
hidden instance maps, gold programs, and operator sequences. Those metadata may
be inspected only for the independent first-order-LGG screen. No gold
representation is needed or read to score a pair.

If a dossier defines `proposer_view`, leakage checks use only that object.
Otherwise the frozen fallback is `title`, `expression_sketch`,
`source_catalog`, and `catalog`. The fallback is conservative and means the
final benchmark packager must still construct and freeze an explicit proposer
view.

## Decisions

Every similarity finding has `auto_reject: false` and
`recommendation: MANUAL_REVIEW`. The report's `admission_decision` is always
`null`. Negative controls are marked separately so their expected flags do not
pollute the scientific-case review queue.

Run from the repository root:

```bash
python -m research.representation_program_search.audits.leakage.audit \
  --root . \
  --json-out research/representation_program_search/audits/leakage/CURRENT_AUDIT.json \
  --md-out research/representation_program_search/audits/leakage/CURRENT_AUDIT.md
```
