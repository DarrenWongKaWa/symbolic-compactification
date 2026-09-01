# Product gaps (record only)

Frozen product peel `783ec64`. Do **not** implement these here.

1. No product status `CERTIFIED_UNDER_DECLARED_APPROXIMATION`. The overlay
   lives only in this experiment. Adding it would be a field-driven parent
   certificate analogous to `CERTIFIED_BY_RULE`, never engine `ZERO`.
2. Mode A cannot record approximation provenance
   (`AUTHOR_DECLARED` / `USER_DECLARED` / `MODEL_PROPOSED`).
3. Remainder certification remains unsupported (NR-004, capability boundary).
   `DECLARED_ONLY` is not `REMAINDER_CERTIFIED`.
4. Substitution identities (Guo \(e_{21}=-e_{12}\)) are still not Mode A
   assumptions. That is the forward-replay G1 gap, not an approximation gap.
5. No shipped detector for undeclared hidden approximations. AA-04 used a
   known \(T_A\) probe (`drop_G_degree_geq_2`), not a general search.
6. Do not weaken `ZERO` to mean "approximately zero".
