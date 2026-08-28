# Owner: V8 — Guo obligation minimizer

Read frozen P2 only. No gold names. Output `GUO_OBLIGATION_MAP.json`.

The map is evaluation-only. It copies claimed types, operators, and
truncated reconstruction rules, then attaches full source-index `node.text`
for each `G####` member (not the catalog 220-character cap) and the parent
sum gid. It does not decide whether a claim is true.
