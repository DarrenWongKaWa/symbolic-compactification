# R3 — Special-function review (Track V5 coefficient-space Laurent)

Isolated review of parent `fb3b929` (`Certify G0016 to G0013 at LEVEL C via per-polygamma C0 match.`).
Branch `work/v5-review-r3`. No hop retune. No D2 unlock. No edits to frozen
authorities. No LLM as proof. Live CAS checks only.

Python: `/Users/kawawong/Projects/symbolic-compactification/.venv/bin/python`
(SymPy 1.14.0). `PYTHONPATH=.`

---

## Verdict

**C0 identity: special-function sound.** The claimed G0016→G0013 `LEVEL_C`
`ZERO` does **not** rest on a Guo polygamma table, reflection, duplication,
recurrence, \(\Phi_\Gamma\), L4–L7, PRB masters, or generator names. The
series used on the certifier path is ordinary CAS Taylor of
`r(t)*polygamma(k, α+βt)` via
\(\partial_z\mathrm{polygamma}(k,z)=\mathrm{polygamma}(k+1,z)\). After
`m→n`, the constant term and G0013 share **exactly 12 polygamma keys**
(4 affine arguments × orders 0, 1, 2). Each key’s rational prefactors
satisfy `expand(together(c_L-c_R).numerator)==0`. That is one identity
class: rational equality of coefficients of the *same* polygamma atoms.
It is not a polygamma closed form.

**Claim “orders 0 and 2 expand-equal, order 1 only together-equal”: not
reproduced.** Live, *all 12 keys* fail `expand(c_L-c_R)==0`. All 12
succeed on the per-atom together-numerator path. Order 1 is larger, not
a different theorem.

**Remainder bit: certificate gap, not a polar counterexample.**
`engine.py` does not call `remainder_ok`. It sets `remainder_verdict=ZERO`
once reconstruction succeeded and negative Laurent coefficients vanished,
with a frozen-Guo energy comment. Live G0016 arguments at `t=0` are **not
identically** in \(\{0,-1,-2,\ldots\}\); they are affine of the form
\(1/2+\beta(\gamma\pm i(\mu-\varepsilon_\bullet))/(2\pi)\). `remainder_ok`
is `False` on all 14 atoms because α still has free symbols. Do **not**
invent a Guo identity to close that gap. Do **not** treat the gap as a
demonstrated extra polygamma pole.

**Banned-identity scan (V5 Python certifier path): clean.**
**Literature pack: stale (still L-D / GAP / UNKNOWN).**
**D2 stays LOCKED.** Ell-hops remain UNKNOWN. This review does not
promote `FAMILY_ZERO`.

---

## 1. Is `series(t,0,NTERMS)` standard polygamma Taylor, or a hidden Guo table?

### Certifier path is `engine.py`, not `pg_series/`

`sparse_laurent_limit` never imports `expand_polygamma_atom` or
`remainder_ok`:

```10:21:research/coefficient_laurent/engine.py
from research.coefficient_laurent.cache import certificate_key, sha256_text
from research.coefficient_laurent.c0 import match_constant
from research.coefficient_laurent.schema import (
    LEVEL_A,
    METHOD_VERSION,
    NONZERO,
    UNKNOWN,
    ZERO,
    LaurentCertificate,
    compose_hop_verdict,
)
from research.iterated_confluence.spectator import split_edge
```

Per-atom expansion is CAS `Expr.series` on `pref * term` after
`xreplace({var: point + t})`, `NTERMS=3`, window `t^{-6}…t^{0}`:

```23:25:research/coefficient_laurent/engine.py
NTERMS = 3
PMIN = -6
PMAX = 0
```

```123:129:research/coefficient_laurent/engine.py
        for term in terms:
            expr = (pref * term).xreplace({variable: target_value + t})
            s = expr.series(t, 0, NTERMS)
            core = s.removeO() if isinstance(s, sympy.Expr) and s.has(sympy.Order) else s
            max_ops = max(max_ops, _ops(core))
            for p in range(PMIN, PMAX + 1):
                acc[p] += core.coeff(t, p)
```

`pg_series/expand.py` is the same constructor (`local.series(t, 0, nterms)`
at line 102) with an 80-op cap and an empty/`exact=False` failure mode. It
is **not** on the hop-ZERO path (`rg expand_polygamma_atom engine.py` is
empty; only tests + `pg_series/` itself reference it).

### What SymPy actually does

`polygamma` has no Guo table. `fdiff` is the textbook identity
(DLMF 5.15; SymPy 1.14.0
`site-packages/sympy/functions/special/gamma_functions.py:800-803`):

```
d/dz polygamma(n, z) = polygamma(n+1, z)
```

`polygamma` has two arguments, so `Function._eval_nseries` takes the
successive-derivative Taylor branch (`function.py:736-749`): substitute
`t=0`, then `e.diff`, divide by `n!`. That is exactly

\[
\mathrm{polygamma}(k,\alpha+\beta t)
=\sum_{n\ge 0}\mathrm{polygamma}(k+n,\alpha)\,(\beta t)^n/n!.
\]

The rational prefactor is expanded as an ordinary Laurent polynomial in
`t`. Product of those two germs is linearity of coefficients, not a
special-function identity.

`polygamma.eval` *can* collapse `polygamma(n, 1/2)` and small rationals
to `EulerGamma` / `zeta` / `harmonic`, and `_eval_expand_func` *can*
apply integer shifts and the multiplication formula. Default
`sympy.expand` does **not** pass `func=True`. Live C0 after series still
contains `polygamma(...)` of the energy-affine arguments, **not**
`EulerGamma`, `zeta(`, `harmonic(`, `cot(`, or `polygamma(n, 1-z)`
(section 3). Reflection/duplication did not fire.

### `pg_series` pole gate is not an integer-pole check

```175:191:research/coefficient_laurent/pg_series/expand.py
def _argument_singular(z: sympy.Expr, t: sympy.Expr) -> bool:
    if not z.has(t):
        return False
    ...
    try:
        sympy.Poly(sympy.expand(core), t, domain=sympy.EX)
    except Exception:
        return True
    return False
```

This rejects non-polynomial / log arguments (e.g. `1/t`). It does **not**
test \(z(0)\in\mathbb{Z}_{\le 0}\). Live samples: `polygamma(0,t)` and
`polygamma(0,-1+t)` still fail closed (`exact=False`, empty dict) because
`series` raises; `polygamma(0,1/t)` is empty; `polygamma(0,1/2+t)` is
exact with vanishing negative powers. Fail-closed on true poles, but the
*detector* is not the meromorphic-pole criterion. Engine does not use
this detector.

No hardcoded energy identities in V5 Python except the remainder
*comment* cited in §2.

---

## 2. Live G0016 argument regularity at `t=0`

Polygamma is meromorphic with poles only at nonpositive integers of the
argument (order `n+1` for `n≥0`; entire for `n≤-2`). That is the right
criterion. Frozen Guo energy *language* is not required and must not be
used as a ZERO identity.

Primary hop: `epsilon(m) → epsilon(n)`, `t = ε(n)`-shifted dummy.
`decompose` reconstruction_ok, **14 POLYGAMMA atoms** (6 of order 0, 4 of
order 1, 4 of order 2), matching `ATOM_MAP.json`.

After `ε(m) ↦ ε(n)+t`, every argument is affine in `t`. At `t=0` there
are **4 unique** `z0` (not 14):

| family | \(z(0)\) |
|---|---|
| \(\ell,+\) | \((\beta\gamma + i\beta\mu - i\beta\varepsilon(\ell) + \pi)/(2\pi)\) |
| \(n,+\) | \((\beta\gamma + i\beta\mu - i\beta\varepsilon(n) + \pi)/(2\pi)\) |
| \(\ell,-\) | \((\beta\gamma - i\beta\mu + i\beta\varepsilon(\ell) + \pi)/(2\pi)\) |
| \(n,-\) | \((\beta\gamma - i\beta\mu + i\beta\varepsilon(n) + \pi)/(2\pi)\) |

Equivalently \(1/2 + \beta(\gamma \pm i(\mu-\varepsilon_\bullet))/(2\pi)\).
Orders 0/1/2 sit on the same four arguments.

Live checks on all 14 atoms:

- `expand(z0 - k) == 0` for \(k=0,-1,\ldots,-12\): **never**.
- `im(z0)` identically 0: **never**.
- `sin(π z0) == 0`: **never** (simplifies to
  `cos(β(γ ± iμ ∓ iε_•)/2)`, not 0).
- `_affine_coeffs` succeeds for every atom.
- `_classify_alpha(z0)`: **`unknown` for all 14** because α has free
  symbols (`remainder/sufficiency.py:263-264`;
  `tests/test_cl_remainder.py:80-83`).
- `remainder_ok(zloc, t)`: **False for all 14**.
- `remainder_ok` on `pref*atom` after xreplace: **0 True / 14 False**.

So: arguments are **not identically** nonpositive integers. They are also
**not remainder-certified**. The engine does not perform either check.
It assumes the second from the first, with a Guo-physics gloss:

```148:151:research/coefficient_laurent/engine.py
        # Affine polygamma arguments at t=0 are not nonpositive integers
        # for the frozen Guo kernels (energy arguments ~ 1/2 + i E). Remainder
        # is ZERO only when negatives and reconstruction succeeded; else UNKNOWN.
        rem = ZERO if (recon and neg == ZERO) else UNKNOWN
```

That is the LEVEL C remainder gate (`schema.py:100-102` requires
`remainder_verdict==ZERO` for hop ZERO). It is **not**
`remainder.sufficiency.remainder_ok`. If that function were the gate,
this hop would stay `LEVEL_B` / `UNKNOWN`.

Analytic content of the assumption, without Guo tables: for affine
\(z(t)=\alpha+\beta t\) with \(\alpha\not\equiv \mathbb{Z}_{\le 0}\),
`polygamma(k,z(t))` is holomorphic in `t` at 0 as a meromorphic function
of the remaining symbols. Polar behaviour of each atom is from the
rational prefactor \(1/(\varepsilon(m)-\varepsilon(n))^{\bullet}\). Live
engine-style series of all 14 local terms **succeeded** (max core ops
**1696**, matching `VERDICT.md` / `GUO_V5_RESCORE.md`). Negative window:

| power | ops | `_is_zero` | tree `==0` |
|---|---:|---|---|
| \(t^{-6}\) … \(t^{-2}\) | 0 | True | True |
| \(t^{-1}\) | 93 | True | False |

`C_{-1}` is algebraic cancellation of the summed principal part
(`engine.py:57-75`: `expand` / `cancel`, cap 400; 93 < 400), not a
polygamma identity. Truncation through \(t^0\) then leaves \(O(t)\),
which vanishes as \(t\to 0\) on the same generic set. That is Riemann
removable-singularity bookkeeping (`remainder/sufficiency.py:1-29`),
which the engine **does not call**.

**Flag:** remainder ZERO is assumed, not checked. **Do not** “fix” it
with a Guo energy identity. A honest remainder certificate is: α not
identically a nonpositive integer (live, yes) *or* `remainder_ok` (live,
no, because of free symbols). Those are different strengths. This review
does not retune the hop.

---

## 3. C0 grouping: 12 keys, expand vs together, identity class

G0016 local kernel: 14 polygamma atoms, 573/567 ops.
G0013 local kernel: **12** polygamma atoms, 333/327 ops.
`match_constant(C0, G0013_local)` live:

```
verdict ZERO
provenance pg_atoms
ops 1317
used_full_together False
steps ('ops:1317', 'pg_atoms:n=12', 'pg_atoms:ZERO')
```

`set(keys_C0) == set(keys_G0013)`, 12 keys, 0 only-left, 0 only-right.
Each key is a **single** `polygamma(n, z)` with polygamma-free rational
coefficient (`coeff_has_pg=False`). The 12 keys are exactly the 4
arguments of §2 at orders 0, 1, 2.

Raw C0 has **13** `polygamma` expressions: series distributes some
arguments to `… + 1/2` while others stay `(… + π)/(2π)`. `_canon_pg`
(`c0/match.py:196-211`) does `expand`/`together` **on the argument
only** and merges them. That is rational arithmetic, not a Guo identity.
The docstring states the same (`c0/match.py:197`).

Grouping itself (`c0/match.py:170-193`) is `sympy.expand` of C0 (default:
`func=False`) then peel polygamma factors. It never `together`s the
C0−G0013 pair (`used_full_together` always False; `_ZERO_EXEMPT` is
`pg_atoms` / `identical`, `c0/match.py:340`).

### Per-key decision procedure (live)

`_rational_coeffs_equal` (`c0/match.py:225-269`): tree equality →
`expand` + polynomial `_is_identically_zero` → `together(diff)` →
`expand(numerator)==0` → small `cancel`.

| order | n keys | tree equal | `expand(diff)==0` | polynomial | `together==0` | `expand(num)==0` |
|---|---:|---|---|---|---|---|
| 0 | 4 | 0 | 0 | 0 | 2 | **4** |
| 1 | 4 | 0 | 0 | 0 | 2 | **4** |
| 2 | 4 | 0 | 0 | 0 | 0 | **4** |

**No key is expand-equal.** Every key is together-numerator-zero.
Order-1 pairs are the largest (`ops` 1665–1993, still `< PAIR_TOGETHER_CAP=4000`).
Order 0/2 also need that path. The frozen slogan “order-1 pairs need
per-atom together” is **true and incomplete**. The slogan “orders 0 and
2 expand-equal, order 1 only together-equal” is **false** on this hop.

### Same identity class?

Yes. For a fixed polygamma key \(P\), both sides are \(R_L P\) vs
\(R_R P\) with \(R\) polygamma-free. `expand(R_L-R_R)==0` and
`expand(numer(together(R_L-R_R)))==0` are two algorithms for the **same**
rational-function identity \(R_L=R_R\). together is common-denominator /
GCD, not \(\mathrm{polygamma}(n,1-z)\), not duplication, not a Guo
kernel reduction. A larger order-1 rational does not change the class.

C0 after series still has only `epsilon` and `polygamma` heads; no
`zeta`/`harmonic`/`EulerGamma`. Series mixed orders in the way Taylor
must: an order-0 atom can contribute `polygamma(1)` and `polygamma(2)`
to \(t^0\). Those land on keys G0013 already carries. That is the
derivative identity, not a new relation among Guo kernels.

---

## 4. Reflection / recurrence / banned-token scan

V5 Python (`research/coefficient_laurent/**/*.py`):

| token | hits |
|---|---|
| `Phi_Gamma`, `phi_gamma`, `PhiGamma` | none |
| `Hermite` | none |
| `reflection`, `duplication` | none |
| `polygamma(n, 1-`, `1 - z` | none |
| `identity_table`, `pairing_table`, `use Hermite` | none |
| L4–L7 / PRB / generators as code | none |

`Hermite` appears only in literature as Newton/Hermite interpolation
citation (`literature/METHODS.md:67`), not as a ZERO rule.
\(\Phi_\Gamma\) / L4–L7 appear in literature as **bans**.

`together(` in V5 Python (not full-kernel C0−target):

| file:line | role |
|---|---|
| `c0/match.py:205` | canonicalise polygamma *argument* |
| `c0/match.py:247` | per-key rational `together(c_L-c_R)` |
| `pg_series/expand.py:133` | `together(core * t**shift)` to read `Poly.nth` |
| `grouping/group.py:140,150,157` | term key (order / arg / denom); unused by `engine.py` |
| `remainder/sufficiency.py:225` | affine split of `z(t)` |
| `falsifier/expr.py:124,130,278` | residual / probe helper, **not** the hop certifier |

No `together` of the 1317-op C0−G0013 blob. Live matcher stops at
`pg_atoms:ZERO` and never reaches `_by_expand` / `_by_cancel` on that
blob (`c0/match.py:67-71` grouping-first).

`sympy.expand_func` appears only in `falsifier/expr.py:106,171`
(adversarial residual / numeric probe). Not imported by `engine.py` or
`c0/match.py`.

Engine comment at `engine.py:148-150` is the only Guo-energy sentence in
V5 Python. It is a regularity *assumption*, not a polygamma closed form.
Flagged in §2; not a hidden reflection table.

---

## 5. `basis/taylor.py`: CONTROL remainder, cannot mint hop ZERO

The derivative basis writes the same identity without CAS series:

```16:17:research/coefficient_laurent/basis/taylor.py
    polygamma(k, z0 + b t)
        = sum_n polygamma(k + n, z0) * (b t)^n / n!
```

```77:87:research/coefficient_laurent/basis/taylor.py
def polygamma_taylor_basis(...):
    """Rewrite ``polygamma(k, z0 + b t)`` in the derivative basis.

    Returns a CONTROL report. Does not certify a hop. Does not propose.
    """
```

- Status is `CONTROL` or `UNKNOWN`, never `ZERO` (`tests/test_cl_basis.py:135-147`).
- Not imported by `engine.py`.
- CAS `series` is comparison-only (`basis/taylor.py:143-155`); construction
  does not require it (`test_construction_does_not_require_cas_series`).
- Live: `polygamma_taylor_basis(0,z0,b,t,nterms=2)` matches
  `polygamma(0,z0+b t).series(t,0,2).removeO()` and equals
  `polygamma(0,z0)+polygamma(1,z0)*b*t`.
- No remainder certificate and no `compose_hop_verdict`. It cannot mint
  hop ZERO.

---

## 6. Literature pack staleness (`literature/CLASSIFICATION.md`)

Written around **L-D / experiment-not-run**. It still asserts that
G0016→G0013 is not `LEVEL_C` `ZERO` and that the packaged cell is a
**GAP**.

| location | stale claim |
|---|---|
| `CLASSIFICATION.md:13` | GAP “would require later hop LEVEL_C ZERO … That experiment has **not** run.” |
| `CLASSIFICATION.md:19` | “G0016→G0013 is not `LEVEL_C` `ZERO`.” |
| `CLASSIFICATION.md:72-73` | “G0016→G0013 is `UNKNOWN`.” |
| `CLASSIFICATION.md:326-365` | packaged routing is GAP; “No V5 rescore exists”; “PROTOCOL.md has not produced hop LEVEL_C ZERO” |
| `CLASSIFICATION.md:401-443` | “do not change the GAP label” until the primary hop is LEVEL_C ZERO |
| `literature/README.md:10-13,51-52` | “G0016→G0013 is UNKNOWN”; packaged contribution is GAP |
| `literature/HANDOFF.md:56-60` | GAP until G0016→G0013 is LEVEL_C ZERO |

This is inconsistent with freeze-parent evidence the pack is forbidden
to rewrite:

- `STATUS.md:5` — `LEVEL_C ZERO (pg_atoms C0; …)`
- `TRACK_V5_CLOSED.md` — case **L-A**, primary LEVEL_C ZERO
- `VERDICT.md` — G0016→G0013 decided ZERO (LEVEL C)
- `GUO_V5_RESCORE.md` — primary ZERO LEVEL_C, max_ops 1696
- this review’s live `match_constant` / 12-key reconstruction

**Needed correction (do not apply here):** retarget the GAP cell to the
*empirical* hop: G0016→G0013 is claimed LEVEL_C ZERO via per-polygamma
C0, false hop ZERO still 0 on the generic suite, no 27k together, no Guo
polygamma identities. Keep polygamma Taylor / sparse Laurent as **known
standard** (do not mint novelty). Record the remainder-certificate gap
(§2) instead of implying LEVEL C remainder was `remainder_ok`. Do **not**
upgrade hop ZERO to `FAMILY_ZERO` or unlock D2. Companion
`METHODS.md` / `README.md` / `HANDOFF.md` need the same L-D → L-A
status sentence. This review does not edit the literature pack.

(`research/PROGRAM_STATUS_V5.md` is also still L-D / “18/18 UNKNOWN”;
out of scope. Frozen authority, not rewritten.)

---

## D2

`STATUS.md:9` `TRACK D2 LOCK STATUS: LOCKED`.
`PROTOCOL.md:3-4` D2 locked until `FAMILY_ZERO` or `FAMILY_NONZERO`.
`VERDICT.md` Q12: not unlocked. Ell-hops UNKNOWN; families
`FAMILY_UNKNOWN`. This review does not open D2.

---

## Commands and results

Worktree: `/private/tmp/wt-v5-review-r3` on `work/v5-review-r3` @ `fb3b929`.

### Required pytest

```
cd /private/tmp/wt-v5-review-r3
export PYTHONPATH=.
/Users/kawawong/Projects/symbolic-compactification/.venv/bin/python -m pytest \
  tests/test_cl_pg_series.py tests/test_cl_c0.py tests/test_cl_basis.py tests/test_cl_atoms.py -q
```

```
..................................                                       [100%]
34 passed in 1.46s
```

### Banned-token / together grep (V5 Python)

```
rg -n -g '*.py' -e 'Phi_Gamma' -e 'phi_gamma' -e 'PhiGamma' -e 'Hermite' \
  -e 'reflection' -e 'duplication' -e 'polygamma\(n, 1-' -e '1 - z' \
  research/coefficient_laurent
# (no matches)

rg -n -g '*.py' -e 'together\(' research/coefficient_laurent
# c0/match.py:205,247
# pg_series/expand.py:133
# grouping/group.py:140,150,157
# remainder/sufficiency.py:225
# falsifier/expr.py:124,130,278

rg -n 'pg_series|expand_polygamma_atom' research/coefficient_laurent/engine.py
# not imported
```

### Live primary-hop sample (read-only; not a retune)

Parse G0016/G0013 from `GUO_OBLIGATION_MAP.json` via `parse_flex`;
`decompose` + `split_edge` + engine-style `series(t,0,3)` +
`c0.match._group_by_polygamma` / `_rational_coeffs_equal` /
`match_constant` / `remainder_ok`.

| quantity | live value |
|---|---|
| src/tgt ops | 573 / 333 |
| src/tgt polygamma atoms | 14 / 12 |
| reconstruction_ok | True |
| unique `z(0)` | 4, none identically in \(\mathbb{Z}_{\le 0}\) |
| `remainder_ok` on 14 atoms | 0 True |
| series max core ops | 1696 |
| series wall | 1.82 s |
| `C_{-6}`…`C_{-2}` | tree 0 |
| `C_{-1}` | ops 93, `_is_zero` True |
| C0 ops / raw polygamma | 990 / 13 → 12 keys after `_canon_pg` |
| key equality | 12 shared, 0 leftover |
| expand-equal keys | 0 |
| together-numerator-zero keys | 12 (orders 0,1,2) |
| `match_constant` | ZERO, `pg_atoms`, ops 1317, no full together |
| C0 `EulerGamma`/`zeta`/`harmonic`/`cot`/`1-z` | absent |
| `polygamma_taylor_basis` status | CONTROL; matches CAS series through \(t^1\) |

---

## What this review does not claim

- Not a family certificate. Not path independence. Not D2.
- Not a proof that `remainder_ok` would accept G0016 (it would not).
- Not an endorsement of the Guo-energy comment as a ZERO rule.
- Not novelty of polygamma Taylor or sparse Laurent (literature pack is
  right on that, even while stale on hop status).
- No other reviews read or written.
