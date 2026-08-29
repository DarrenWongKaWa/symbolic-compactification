# A4 — assumption-witness falsifier

Owner: A4 (`work/ac-a-falsify`). Parent: `f987fcc`.
Owned: `audit/falsify/`, `tests/test_ac_falsify.py`.
Did not edit: `schema.py`, miner dossiers, Guo hops, sibling A/C directories.

No LLM. Guo G3 stays sealed (`G0016 → G0013 = UNKNOWN LEVEL_B`).
Do not admit DEV.

## Job

For every non-rejected, non-Guo candidate, search for a **parameter
witness**: an assignment that satisfies the *declared* symbol flags,
positivity conditions, and concrete nonzero/analytic exclusions, and
still hits a required pole, branch cut, or division by zero.

If such a witness exists, the task is **DISQUALIFIED**
(`PROBLEM_UNDERSPECIFIED`) until a human fixes the problem statement.
That is the Guo pattern: frozen real-only β, γ allow `z0 = 0 ∈ Z_≤0`.

Declared pole-exclusion (DLMF `z ∉ Z`, `z ≠ n π i`, …) blocks the
assignment, so it is **not** a witness.

## API

```python
from research.assumption_complete_representation.audit.falsify import (
    run_scan,
    write_witnesses,
)

report = run_scan()
write_witnesses()  # regenerates WITNESSES.json
```

Pool: `SCREENING.json` keepers + flagged (37 scanned). Miner-rejected
and Guo are skipped, not deleted.

## Headline clean case

`thermal-01-fermi-im-digamma` (DLMF 5.4.17). `y` real is DECLARED.
`psi` poles are `Z_≤0`. `Re(1/2 + i y) = 1/2`, so the pole-exclusion
is DERIVED. `y = 0` is allowed and finite. Same pattern:
`thermal-03` (DLMF 5.5.4, declared `z ∉ Z`) and `thermal-05`
(DLMF 5.15.1, declared `z ∉ Z_≤0`).

## Disqualified (interior witnesses, SymPy `zoo`)

| case | witness | required predicate |
|---|---|---|
| `ac-r04-lindhard-occupation-dd` | `hbar = 0`; also `m = 0` | Lindhard denominator / `E = ħ²k²/(2m)` |
| `ac-r05-lehmann-spectral-master` | bosonic `ω_n = 0`, `ξ = 0`; also `η = 0` | `1/(-i ω_n + ξ)` and retarded `1/(-(ω+iη)+ξ)` |
| `ac-r06-matsubara-pole-family` | `η = +1`, `ξ = 0` | Bose occupancy `1/(e^{βξ}-1)`; Matsubara coincidence |
| `ac-r07-lippmann-schwinger-iepsilon` | `ε = 0`, `E = E_β` | causal resolvent `1/(E - E_β + iε)` |
| `thermal-07-green-spectral-hilbert` | `ω_n = 0`, `x = 0` | Hilbert kernel on the real axis (bosonic zero mode) |

Fixes are problem-statement patches (declare `ħ ≠ 0`, `ε > 0`,
occupancy poles disjoint from `{i ω_n}`, fermionic Matsubara, …),
not verifier extensions and not silent positivity insertion.

`ac-r06` is the unfixed sibling of rejected `thermal-08`, which already
labeled occupancy / Matsubara-pole exclusion `NOT_DECLARED`.

## Gaps (no interior witness)

- `ac-r02`: `ε` has no positive flag; the identity is a declared `ε → 0+`
  distributional limit, so `ε = 0` is the boundary, not an interior point.
- `sciml-phi-hermite-01` / `sciml-vanloan-blockexp-01`: `(e^z-1)/z` at
  `z = 0` is removable; entire continuation is DECLARED.
- Helmholtz `n ∈ {2,3}` vs a written 3D kernel: formula mismatch, not a pole.
- Algebraic tensor cases: empty `analytic_domains` is correct (no meromorphic poles).

## Guo analogue (optional note only)

Sealed audit `9fc3c8a`: `β = 1`, `γ = -π`, `μ = 0`, `ε(n) = 0` ⇒ `z0 = 0`.
This falsifier does **not** load `FROZEN_G0016_ATOMS.json`, Guo hop
tables, or `nc-guo-sigma-abc` as a candidate. The analogue is the
*shape* of the hole (declared reals too weak for a required pole
predicate), not the atoms.

## Counts (this freeze)

Scanned 37; CLEAN 31; DISQUALIFIED 5; GAP-only 1; miner-rejected skipped 3.
Guo not in the miner pool.
