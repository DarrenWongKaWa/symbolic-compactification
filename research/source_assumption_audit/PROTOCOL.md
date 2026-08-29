# Protocol — source assumption audit

Parent: `c6fac1e` (remainder CASE R-B). D2 LOCKED.

Frozen authorities (read-only):

- `examples/long/Guo_Sigma_abc_dc_exact.txt`
- `examples/long/symbols.json`
- `examples/long/SOURCE.md`
- `research/llm_abstraction/tasks.py` `load_guo_item`
- V5 freeze `research/coefficient_laurent/FROZEN_INPUTS_V5.json`
- remainder close `research/remainder_certification/{VERDICT,FROZEN_G0016_ATOMS}.json`

Do not edit those files. Do not edit hop engines. Do not rerun ell-hops.

## Inventory scope

Count as **declared** only what is written in those artifacts:

- Wolfram header comments
- `symbols.json` flags (`real`, `nonzero`, absence of `positive`)
- `load_guo_item` symbol dicts and `required_assumptions`
- Wolfram translator defaults used at ingest
- Piecewise conditions that are actually on the members (index equalities)

Not declared: reviewer comments, thermal-field-theory folklore,
`energy arguments ~ 1/2 + iE`.
