# DEV decision (structure discovery)

Split: DEV only. Test items were generated but **not used to select**
features, thresholds, or constructors. **No second architecture revision.**

## Headline

- B9 type-hit (positive): 0.9375 (15/16)
- B6 direct type-hit (positive): 0.0
- B1 type-hit (positive): 0.125
- B9 gold-type certified (positive): 0.9375
- B9 unsafe merges on negatives: 0
- B9 false promotions: 0
- B9 D3–D5 gold subset: **9/9 type-hit and gold-certified** vs B1 **0/9** vs B6 **0/9**
- B9_no_obs type-hit: 0.0

B6 reports a high self-labeled D3+ count from Method v2 tautological `Phi`/`Kbody`
names. Those labels **do not match gold types**. C2 is scored on gold type-hit,
not on self-reported abstraction_level.

## Did the intervention attack the diagnosed bottleneck?

The diagnosed bottleneck was *shallow proposal* (expressions, not
typed structure). B9 emits typed hypotheses; B1/B6 generally do not
match gold *types* even when they rewrite algebra.

## Causal check

- Observations matter: B9_no_obs type-hit = 0. Removing `repeated` drops
  type-hit 0.9375 → 0.625; removing `permutation` → 0.8125.
- Decomposed typed H beats direct E→E' on the type axis (0.9375 vs 0.0).
- C3 holds on DEV: aggressive `identical_kernel_merge` is proposed on
  distinct poles and is NONZERO; forbidden reconstructions never ZERO.
- Single DEV miss: `S2-pos-perturbation` (two similar but non-identical
  Born-like products `V(p)*G0(p)*V(p)` vs `V(q)*G0(q)*V(q)`). Not revised.

## Freeze

Method v3 = this deterministic observe→H→construct→verify pipeline.
No further DEV tuning. Held-out test runs next, once.

## Summary table

```json
{
  "B0": {
    "n": 21,
    "pos_type_hit": 0.0,
    "pos_gold_certified": 0.0,
    "neg_unsafe_merge": 0,
    "false_promotion": 0,
    "mean_n_zero": 0.0,
    "mean_n_nonzero": 0.0,
    "d3plus_attempted": 0,
    "d3plus_certified": 0
  },
  "B1": {
    "n": 21,
    "pos_type_hit": 0.125,
    "pos_gold_certified": 0.0,
    "neg_unsafe_merge": 0,
    "false_promotion": 0,
    "mean_n_zero": 0.7619047619047619,
    "mean_n_nonzero": 0.0,
    "d3plus_attempted": 0,
    "d3plus_certified": 0
  },
  "B6_direct": {
    "n": 21,
    "pos_type_hit": 0.0,
    "pos_gold_certified": 0.0,
    "neg_unsafe_merge": 0,
    "false_promotion": 0,
    "mean_n_zero": 1.5238095238095237,
    "mean_n_nonzero": 0.0,
    "d3plus_attempted": 14,
    "d3plus_certified": 14
  },
  "B9_full": {
    "n": 21,
    "pos_type_hit": 0.9375,
    "pos_gold_certified": 0.9375,
    "neg_unsafe_merge": 0,
    "false_promotion": 0,
    "mean_n_zero": 2.142857142857143,
    "mean_n_nonzero": 0.42857142857142855,
    "d3plus_attempted": 15,
    "d3plus_certified": 12
  },
  "B9_conservative": {
    "n": 21,
    "pos_type_hit": 0.9375,
    "pos_gold_certified": 0.9375,
    "neg_unsafe_merge": 0,
    "false_promotion": 0,
    "mean_n_zero": 2.142857142857143,
    "mean_n_nonzero": 0.14285714285714285,
    "d3plus_attempted": 15,
    "d3plus_certified": 12
  },
  "B9_no_obs": {
    "n": 21,
    "pos_type_hit": 0.0,
    "pos_gold_certified": 0.0,
    "neg_unsafe_merge": 0,
    "false_promotion": 0,
    "mean_n_zero": 0.0,
    "mean_n_nonzero": 0.0,
    "d3plus_attempted": 0,
    "d3plus_certified": 0
  },
  "B9_no_perm": {
    "n": 21,
    "pos_type_hit": 0.8125,
    "pos_gold_certified": 0.8125,
    "neg_unsafe_merge": 0,
    "false_promotion": 0,
    "mean_n_zero": 1.9523809523809523,
    "mean_n_nonzero": 0.3333333333333333,
    "d3plus_attempted": 11,
    "d3plus_certified": 10
  },
  "B9_no_repeated": {
    "n": 21,
    "pos_type_hit": 0.625,
    "pos_gold_certified": 0.5625,
    "neg_unsafe_merge": 0,
    "false_promotion": 0,
    "mean_n_zero": 0.8095238095238095,
    "mean_n_nonzero": 0.42857142857142855,
    "d3plus_attempted": 15,
    "d3plus_certified": 12
  },
  "B9_no_denoms": {
    "n": 21,
    "pos_type_hit": 0.875,
    "pos_gold_certified": 0.875,
    "neg_unsafe_merge": 0,
    "false_promotion": 0,
    "mean_n_zero": 1.8571428571428572,
    "mean_n_nonzero": 0.14285714285714285,
    "d3plus_attempted": 11,
    "d3plus_certified": 8
  }
}
```
