# ssc-structure-bench-v0.1

Structure-discovery benchmark. Does **not** overwrite `ssc-bench-v0.1` or
`ssc-bench-v0.2-hard`.

Evaluates discovery of typed structure, not only verification or `count_ops`.

| Split | n | Role |
|---|---:|---|
| DEV | 21 | method development |
| TEST | 12 | frozen held-out |
| Guo | — | DEV case study from `examples/long/`, not an item here |

Tiers: S1 synthetic, S2 semi-synthetic scientific algebra, S3
physics-shaped author-constructed skeletons (Kubo, Green, thermal,
transport, scattering, tensor). Positive and negative items both present.

`proposer_view` strips `hidden_gold`, gold types, reconstructions, polarity.
Scientific context is generic. Guo is not in TEST.

Rebuild: `python -m research.structure_discovery.prototype.build_benchmark`
