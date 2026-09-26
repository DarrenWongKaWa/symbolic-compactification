# Table 3 — Adversarial integrity attacks

Existing public tests. These are central experiments, not implementation
trivia.

| Attack | Expected outcome | Public test |
|---|---|---|
| LLM-authored `ZERO` in Markdown | ignored; no verified row | `test_a_markdown_zero_without_machine_evidence_is_not_verified`; `test_forged_markdown_zero_is_ignored_on_regeneration` |
| Forged `ZERO` record missing hashes | `integrity_ok` fails; excluded | `test_b_forged_zero_json_without_obligation_hash_is_invalid`; `test_forged_zero_without_hashes_is_rejected` |
| Source mutation | snapshot hash changes; prior row does not transfer | `test_e_source_snapshot_change_breaks_record_identity` |
| Assumption mutation | assumptions hash changes | `test_d_assumption_hash_change_breaks_record_identity` |
| Residual mutation | residual/obligation identity breaks | `test_c_residual_bytes_change_breaks_record_identity` |
| Relabel `UNKNOWN` as `ZERO` | rejected (`STATUS_ZERO_REQUIRES_ENGINE_ZERO`) | `test_f_unknown_cannot_be_relabeled_zero_without_engine_zero` |
| Hide `NONZERO` by editing Markdown | regeneration restores `TABLE_NONZERO` | `test_g_nonzero_is_never_in_verified_table`; `test_nonzero_reappears_if_deleted_then_regenerated` |
| `SPLIT` parent with uncertified child | cannot become `CERTIFIED_BY_CHILDREN`; never `ZERO` | `test_h_split_parent_with_uncertified_child_cannot_certify` |
| Asymptotic truncation as exact equality | parent stays out of verified table | `test_asymptotic_unknown_stays_out_of_verified_table`; `test_coefficient_zero_does_not_certify_enclosing_asymptotic` |
| BZ IBP parent as engine `ZERO` | parent is `CERTIFIED_BY_RULE` or `ASSUMPTION_REQUIRED`, never `ZERO` | `test_certified_by_rule_never_enters_verified_table`; `test_bz_ibp_requires_declared_periodicity` |
