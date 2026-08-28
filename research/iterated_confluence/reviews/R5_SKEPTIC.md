# Reviewer 5 — benchmark skeptic (Track V3)

Parent: `d977db457da2cd50b2b2a72968e8db3bd21d9405`
Branch: `work/v3-review-r5`

Attack: **toy-driven method construction.** Did the iterated-confluence
verifier get tuned on cubics and then fail-closed on Guo, or was Guo
silently given identities?

**Verdict: the first, not the second.** Cubic Newton/Hermite plus a
spectator-`h1` cubic kernel are the only live `FAMILY_ZERO` objects.
Five-branch Guo hops are `UNKNOWN` (timeout). The two Guo `ZERO` edges
are Track V series reuse on the already-certified 176-op pairs, not a
new pairing table. `edges/*.py` and `spectator/*.py` contain no
`Phi_Gamma` and no `guo_map` pairing table.

Do **not** read `GENERIC_SUITE.md` pass / `false FAMILY_ZERO = 0` as
evidence that the 5-branch method works. Publication **E** is the
correct reading of the scientific-scale result.

---

## 1. The attack question, answered

| Hypothesis | Holds? |
|---|---|
| Verifier unit tests and generic-suite `FAMILY_ZERO` are cubic toys | **Yes** |
| Cascade was retuned so previously certified 176-op Guo pairs stay `ZERO` | **Yes** (shape/budget, not identities) |
| 5-branch Guo was given a pairing table / `Phi_Gamma` / gold names | **No** |
| 5-branch hops fail-closed | **Yes** — 0 `FAMILY_ZERO`, 0 `FAMILY_NONZERO`, 7/7 `FAMILY_UNKNOWN` |
| The two s2-i4 `ZERO` edges are a V3 discovery | **No** — `check_limit:series` on G0005→G0004 and G0009→G0008, already listed as Track V `KNOWN_ZERO_PAIRWISE` |

The honest sentence is: *the method was built so cubic Newton and the
176-op two-member Guo pairs remain `ZERO`; the 327–567-op 5-branch hops
then timed out.* That is toy-driven construction plus an honest
negative transfer, not silent gold.

---

## 2. Source-ban: `edges/` and `spectator/`

Scope of the ban (protocol + package tests): no `Phi_Gamma`, no
`guo_map` pairing, no `if family_id == guo`, no L4–L7 defs.

Checked on this parent:

- `research/iterated_confluence/edges/__init__.py`
- `research/iterated_confluence/edges/certify.py`
- `research/iterated_confluence/spectator/__init__.py`
- `research/iterated_confluence/spectator/split.py`

`rg` over those `*.py` files: **zero** matches for `Phi_Gamma`,
`guo_map`, `pairing_table`, `PAIRING`, `G00`, or `family_id`.

`tests/test_ic_edges.py::test_source_ban_no_guo_pairing` and
`tests/test_ic_spectator.py::test_source_ban_no_gold_pairing_or_simplify_proof`
both pass.

`certify_one_parameter` does not load `GUO_OBLIGATION_MAP.json`. It
splits, then runs generic `prove_local` / `check_limit` / `certify_edge`.
Timeout and size-guard are mapped to `UNKNOWN` (`_BLOCKED_ZERO`); they
cannot become `ZERO`.

`split_edge` peels **any** common `AppliedUndef` from `Mul.args` and
requires `S * K = E` (or additive). That is a Guo-*shaped* spectator
(the `h1(a,m,n) h1(b,…) h1(c,…)` product), not a Guo *identity*. No
member-id table. No `Phi_Gamma`. Failed reconstruction discards the
kernel.

`Phi_Gamma` appears in V3 docs only as **forbidden** (`PROTOCOL.md`,
`edges/HANDOFF.md`). That is the ban statement, not a use.

**Out of ban scope (named so it is not confused with pairing):**

- `eval/guo_iterated_rescore.py` and `eval/local_complexity.py` load
  `research/scalable_verification/guo_map/GUO_OBLIGATION_MAP.json` to
  fetch frozen member **texts**. That is data lookup, not an identity
  table inside the edge prover.
- `freeze_v3.py` `KNOWN_ZERO_PAIRWISE` records Track V authorities for
  G0005→G0004 / G0009→G0008. `certify.py` does not consult it.

---

## 3. The generic suite is not a holdout

`eval/generic_suite.py` is 8 rows. Live CAS is used on cubics and on
`x/(x+y)`. The rest is schema injection.

| id | live math? | `FAMILY_ZERO` path | What actually happened |
|---|---|---|---|
| A-joint-iterated-agree | cubic Newton `(x³−y³)/(x−y)` | **expect `FAMILY_ZERO`** | two `check_limit` ZEROs; **`CONSISTENT_ZERO` injected** |
| B-order-matters | `x/(x+y)` | expect `FAMILY_NONZERO` | both one-parameter limits ZERO vs their targets; **`INCONSISTENT_NONZERO` injected** |
| C-one-path-invalid | none | `FAMILY_NONZERO` | `PATH_ZERO` + `PATH_NONZERO` fed to `compose_family_verdict` |
| D-pairwise-zero-inconsistent | none | `FAMILY_NONZERO` | all edges hardcoded `ZERO`, consistency hardcoded inconsistent |
| E-hermite-cubic-consistent | cubic `F=z³` | **expect `FAMILY_ZERO`** | one live F[x,x] limit; **`rec_xxx = "ZERO"` hardcoded**; `PATH_ZERO` injected |
| F-hidden-pole | `1/(x−y)` | not `FAMILY_ZERO` | live `NONZERO` |
| G-spectator-small-kernel | `h1(x)` × cubic Newton | **expect `FAMILY_ZERO`** | Track V `split_multiplicative`, **not** V3 `split_edge` |
| neg-majority-unknown | none | `FAMILY_UNKNOWN` | `PATH_ZERO, PATH_ZERO, PATH_UNKNOWN` injected |

`false FAMILY_ZERO = 0` therefore means: *the composer does not promote
when you hand it a NONZERO or UNKNOWN*, plus *cubic Newton still
limits*. It does **not** mean the V3 edge cascade was run on a
scientific holdout.

Further:

- The suite never imports `certify_one_parameter`, `split_edge`, the
  path enumerator, or the consistency auditor.
- Case G’s note is `exact_applied_undef_factor` (Track V), not
  `exact_applied_undef_mul_args` (V3 peel).
- `Fcubic = z**3` is the same toy as Track V `eval/generic_suite.py`
  (`F = z**3`, Newton/Hermite positives). V3 did not add a new
  positive family; it re-hosted the cubic under `FAMILY_*`.
- Edge unit tests (`tests/test_ic_edges.py`) have the same cubic
  Newton as the only confluence `ZERO`, plus `h1`×cubic for split-first.
  There is **no** polygamma one-parameter confluence unit test.

A skeptic does not let a package score itself on the object it was
written against and then quote that score as a capability claim.

---

## 4. Construction was aimed at the 176-op Guo pair

This is the real “method constructed around a benchmark” fact. It is
**not** identity leakage. It **is** success-criterion leakage.

`LOCAL_COMPLEXITY.md` / `eval/local_complexity.py`:

```
CERTIFIED_TWO_MEMBER_FULL_OPS = 176   # G0005
vs_176 = local / 176
decomposition_to_176_scale = max(five-branch locals) ≤ 176   # False
```

The gate is not an independent complexity theory. It is “did spectator
peel bring 5-branch kernels to the already-certified two-member Guo
scale?” That hypothesis is the Track V3 question. Reporting `False` is
honest. Calling 176 a *generic* local-complexity unit is not.

Coordinator patches (`MERGE_GATE_1.md`) exist **because** Track V
cancel-peel expanded those same 176-op pairs to 1355 ops:

1. Mul-args `AppliedUndef` peel without cancel expansion → 172 / 83
   with `S*K = E`.
2. Expanding splits rejected.
3. `check_limit` is not skipped at V2 `OPS_CAP=200` (that cap had
   blocked the 176-op pairs).

`edges/certify.py` says the quiet part out loud:

> Do not skip it at V2 certify_edge OPS_CAP=200: that cap blocked the
> already-certified ~176-op Guo pairs after cancel expansion.

`FULL_OPS_CAP = 250` is the V2 skip threshold, not a derived bound.
Split is forced first so a fat spectator cannot size-guard away a small
kernel — the unit test for that is again `h1(sum x**i)` × cubic Newton,
not a 5-branch polygamma hop.

So: **the cascade was edited until the previously passing Guo 2-member
edges still pass, then applied to 5-branch.** That is the cubic-and-
176-op construction. The 5-branch result is then allowed to fail
closed. That is the right experimental order, and it is also why the
generic suite cannot be cited as independent confirmation.

---

## 5. What Guo actually received

### 5.1 Five-branch hops — fail closed

`GUO_ITERATED_RESCORE.md`: 7 families, `FAMILY_ZERO=0`,
`FAMILY_NONZERO=0`, `FAMILY_UNKNOWN=7`, case **I-D**.

Committed edge records for 5-branch one-parameter hops:
`verdict=UNKNOWN`, `provenance=timeout`, `full_ops=null`,
`local_ops=null`, `split_certified=false`. The 25 s process budget
(`EDGE_SECONDS = 25.0`) killed `certify_one_parameter` before a local
ops number was stored. No series `ZERO`. No `prove_local` `ZERO`.

Static peel (`LOCAL_COMPLEXITY.md`), not the timed edge:

| class | full | local after h1 peel | vs 176 |
|---|---:|---:|---:|
| 5-branch triple (G0012 / G0019) | 33 | 27 | 0.15 |
| 5-branch diagonal (G0013 / G0020) | 333 | 327 | 1.86 |
| 5-branch generic (G0016 / G0023) | 573 | 567 | 3.22 |
| 2-member generic (G0005 / G0009) | 176 | 172 | 0.98 |

Peel is exact and cheap (~6 ops). It does not manufacture a 176-op
kernel. `CAPABILITY_BOUNDARY.md` is right that the missing object is a
generic polygamma confluence decision at 300–570 ops, not a path
enumerator.

### 5.2 The two `ZERO` edges — reuse, not a gift of names

```
guo-p2-s2-i4  G0005 → G0004  check_limit:series  full=176 local=172  split_certified=true
guo-p2-s2-i4  G0009 → G0008  check_limit:series  full=176 local=172  split_certified=true
guo-p2-s2-i4  G0005 → G0009  substitution        UNKNOWN
family                                       FAMILY_UNKNOWN
```

Provenance is generic series after certified peel, not `prove_local`,
not a pairing key. Those pairs are the Track V V_GAIN objects
(`PROTOCOL.md`, `freeze_v3.KNOWN_ZERO_PAIRWISE`, authority
`38d6d4a+fe53ebc`). `PATH_ZERO ≠ FAMILY_ZERO` still holds. That is
the opposite of silently marking the family done.

`prove_local` (V2 special pack, called from `certify.py` when
polygamma/gamma is present) admits only derivative and Newton-first
polygamma identities, size-guards at 80 ops / 4096 chars, and rejects
`Phi_Gamma` / L4–L7 as `master_or_L4_L7`. Guo 5-branch kernels do not
fit that box. The s2-i4 `ZERO`s did not come from it.

### 5.3 Composition gift that did **not** fire

`eval/guo_iterated_rescore.py` always passes
`reconstruction_verdicts=["ZERO"]` into `compose_family_verdict`.
That is not a pairing table, but it **is** a silent reconstruction
pass. If 5-branch hops had been `ZERO` and consistency
`CONSISTENT_ZERO`, a `FAMILY_ZERO` could have issued without a live
`S*K = E` family reconstruction on the 5-branch members.

On this freeze it did not matter: required edges stayed `UNKNOWN`.
It still means the Guo rescore is **not** a complete `FAMILY_ZERO`
gate. The generic suite does the same injection (cases A–D, F, G,
majority). Schema tests with gifted reconstruction are not family
certificates.

---

## 6. Artifact hygiene (skeptic, not a pairing finding)

`CAPABILITY_BOUNDARY.md` and `VERDICT.md` report a **90 s** timeout on
G0013→G0012 (327-op diagonal). The committed rescore is **25 s only**
(`GUO_ITERATED_RESCORE.json` `"edge_seconds": 25.0`;
`REPRODUCIBILITY_V3.md` documents 25 s). There is no 90 s JSON/CSV
next to the 25 s run.

I-D does not depend on 90 s: 25 s already fail-closed, and 327 ≫ 176
is in `LOCAL_COMPLEXITY.md`. Do not cite 90 s as a frozen number until
a rescore artifact exists. Do not treat a longer series timeout as the
next program (`CAPABILITY_BOUNDARY.md` already says this).

Timeout rows store `local_ops: null`, so the rescore cannot by itself
prove “timeout after h1 peel.” That claim is the static peel table plus
the process budget. Keep those two instruments distinct.

---

## 7. Claims that survive this attack

- No `Phi_Gamma` / no `guo_map` pairing table in `edges/` or
  `spectator/` Python. Source-ban holds.
- Timeout / size-guard cannot become `ZERO` in `certify.py`.
- `PATH_ZERO` is not `FAMILY_ZERO` (s2-i4: 2 `PATH_ZERO` + unknown
  substitution → `FAMILY_UNKNOWN`).
- Order-dependent toys are never `FAMILY_ZERO` (schema + falsifier
  attack ids). That is a composer property, demonstrated on toys.
- Spectator mul-args peel is exact on these Guo `Mul`s and does **not**
  bring 5-branch kernels to 176 ops.
- Track D2 stays locked. Case I-D is the only family-level reading
  supported by the frozen rescore.

## 8. Claims that do not survive

- “Generic suite PASS” as a scientific-scale soundness result. It is
  cubic Newton + schema unit tests, overlapping Track V’s cubic suite.
- “Iterated 1-parameter decomposition decides 5-branch confluence.”
  Falsified by the rescore (`VERDICT.md` §17). Do not rephrase I-D as
  a near-miss that the cubic suite already solved.
- Treating the two s2-i4 series `ZERO`s as V3 V_GAIN. They are Track V
  reuse after a non-expanding peel.
- Treating `vs_176` as an independent complexity unit. It is the
  previously certified Guo pair.
- Treating hardcoded `reconstruction_verdicts=["ZERO"]` as a checked
  family obligation.

---

## 9. Recommendation

Keep publication **E**. Keep **STOP_VERIFICATION_LINE**.

The benchmark-skeptic reading of Track V3 is:

1. Method and tests were built on cubic Newton/Hermite and on the
   176-op two-member Guo pair (spectator shape + series cascade).
2. That pair still `ZERO`s; 5-branch hops `UNKNOWN`.
3. Guo was **not** given `Phi_Gamma` or a pairing table in the edge
   or spectator packages.
4. Therefore the close is an honest negative transfer, not a cooked
   positive.

What would change this review: a holdout positive that is not `z**3`
and not G0005/G0009 — e.g. a generic polygamma / repeated-argument
local identity that decides the 327-op diagonal hop without Guo member
ids — with reconstruction actually checked, not injected. Until that
exists, do not advertise the cubic suite as the 5-branch method.
)
