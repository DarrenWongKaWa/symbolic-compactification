# Invalid `0*` overlay (archived)

Identifiers beginning with `0` / `0*` were produced by an incorrect
audit overlay (workspace lowerer chips on frozen `UNSUPPORTED` rows).

They are **not** engine `ZERO`, **not** frozen Exact, and **not** part
of the reviewer workflow.

This directory keeps the historical lowering queue and algebra-gap
encodings so scientific history is not silently deleted. Do not copy
these chips into `examples/guo-evidence-ledger/output/`.
