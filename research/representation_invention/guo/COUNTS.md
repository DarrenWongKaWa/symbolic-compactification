# Guo DEV structural counts (evaluation only)

Not proposer-visible. Do not copy this file into a proposer packet.

Source path: `examples/long/Guo_Sigma_abc_dc_exact.txt`

These are source-shape measurements from `structure_summary` / the G####
catalog. They do not select a representation.

| quantity | expected |
|---|---:|
| n_sums | 4 |
| n_piecewise | 4 |
| n_piecewise_branches | 14 |
| catalog members (`sum` + `piecewise_branch`) | 18 |

Catalog ids are `G####` from `research.obligation_ir.source_index.build_index`.
The catalog wrapper does not add gold extra fields.

Evaluation queries (local confluence, Newton-DD candidate, repeated-node DD,
possible master families) live in `eval/queries.py` and are not given to the
proposer.
