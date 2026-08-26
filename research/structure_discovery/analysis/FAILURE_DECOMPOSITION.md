# Failure decomposition

Question: are we failing because the discoverer cannot see structure, or
because the backend cannot prove it?

## Held-out B9_full

No positive type-hit misses. Negatives: correct abstain (broken orbit
NONZERO; invalid Piecewise NONZERO; distinct poles not collapsed to ZERO).

## DEV B9_full

| Item | Class | Notes |
|---|---|---|
| S2-pos-perturbation | A discoverer | two similar Born products are not identical sreprs; no H emitted |
| S1-neg-poles identical_kernel_merge | A wrong H, C3 pass | proposed; constructor `2*K` is NONZERO |
| S1-neg-broken-orbit equal-weight | A wrong H, C3 pass | NONZERO |
| S2-pos-green identical_kernel_merge | D verifier / C incomplete | some aggressive merges UNKNOWN under 8s budget |
| Sum-hosted orbits | C constructor | dummy-index swap inside `Sum` skipped (`orbit_host_contains_sum`) |

## Guo (DEV case study)

| Layer | Result |
|---|---|
| Discoverer | 8× `repeated_kernel` (epsilon, 1/pi, beta*gamma, …). Concrete targets, not a slogan. |
| Missing types | 4 Piecewise objects observed but **not emitted** (hypothesis cap filled by CSE kernels). 0 permutation pairs. |
| Constructor / verifier | not run on the 3911-op expression in this snapshot |
| L4–L7 | **not reached**. Independent of Method v2 L2 ceiling. |

Class: discoverer shallowness / ranking, not a false ZERO.

## Diversity

Single-agent B9 is diverse on S1/S2 toys (kernel, orbit, master, DD, confluence,
spectral). On Guo it collapses to kernels. Protocol would next allow a 3-role
ensemble; **not done after freeze**.

## LLM

Blocked. Cannot localize “AI imagination” vs observation heuristics.
