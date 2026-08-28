# V5 Review R2 — Laurent remainder, pole window, iterated vs joint

Isolated review on `work/v5-review-r2` at parent `fb3b929`.
No other reviews read. No LLM. No hop retune. No D2 unlock. No edits to freeze/V3/V4/SOL/historical runs.
Python: `/Users/kawawong/Projects/symbolic-compactification/.venv/bin/python` with `PYTHONPATH=.`.

**Headline.** Claimed primary `G0016→G0013` LEVEL_C ZERO is **not remainder-sound**. `sparse_laurent_limit` never calls `remainder_ok` / `remainder_verdict`; it hardcodes `remainder_verdict=ZERO` from reconstruction plus vanished negatives. That is the falsifier trap `forbidden_ignore_remainder`. On the live primary hop every polygamma unit is affine but `α` is symbolic, so the remainder package itself returns UNKNOWN. Coordinator must fail-close the engine (`remainder_verdict=UNKNOWN` unless `remainder_ok`) without raising `NTERMS`/`PMIN`/`EDGE_SECONDS`/`PAIR_TOGETHER_CAP` and without opening D2.

---

## 1. Remainder wiring — LEVEL_C without a remainder certificate

### What V5-G claims

`research/coefficient_laurent/remainder/sufficiency.py` states: an atom `R(t)*polygamma(n,z(t))` with affine `z(t)=α+βt` is holomorphic in the polygamma factor at `t=0` iff `α∉{0,-1,-2,…}` (`n≤-2` entire). Then all poles come from `R`, the window `t^{pmin}…t^0` exhausts the principal part plus the regularized limit, and the tail is `O(t)→0` (`sufficiency.py:1–29`, `SUFFICIENCY_REASON` at `43–50`, `REQUIRED_PMAX=0` at `39`). If `z(0)` might be a polygamma pole, extra negative powers of order up to `n+1` can sit below `pmin`; then `remainder_ok` is False and the remainder verdict is UNKNOWN, never NONZERO (`28–29`, `remainder_ok` `74–90`, `remainder_verdict` `93–103`, `required_pmin` `106–128`). Callers are instructed to set `remainder_verdict=UNKNOWN` on False (`remainder/README.md:45–49`, `HANDOFF.md:18`).

Symbolic `α` is UNKNOWN even if a later assumption would exclude `Z_≤0` (`sufficiency.py:253–254`; `HANDOFF.md:22–23`).

METHODS assigns remainder to `remainder_verdict` only (`literature/METHODS.md:515`). Schema LEVEL_C ZERO requires `remainder_verdict==ZERO` (`schema.py:100–102`).

### What `engine.py` actually does

`engine.py` does **not** import `research.coefficient_laurent.remainder`. `sparse_laurent_limit` never mentions `remainder_ok` or the function `remainder_verdict`.

Docstring claims the opposite:

```89:89:research/coefficient_laurent/engine.py
    """LEVEL C ZERO only if negatives vanish, C0 matches, remainder OK."""
```

Reconstruction failure does fail-close remainder (`engine.py:113–117`). Success path:

```148:160:research/coefficient_laurent/engine.py
        # Affine polygamma arguments at t=0 are not nonpositive integers
        # for the frozen Guo kernels (energy arguments ~ 1/2 + i E). Remainder
        # is ZERO only when negatives and reconstruction succeeded; else UNKNOWN.
        rem = ZERO if (recon and neg == ZERO) else UNKNOWN
        cert.remainder_verdict = rem
        v, lvl = compose_hop_verdict(
            reconstruction_ok=True,
            atoms_expanded=True,
            negative_verdict=neg,
            constant_verdict=c0v,
            remainder_verdict=rem,
        )
        cert.final_verdict, cert.proof_level = v, lvl
```

That assignment is identical to the adversarial trap:

```91:101:research/coefficient_laurent/falsifier/checkers.py
def forbidden_ignore_remainder(
    *,
    negative_verdict: str,
    constant_verdict: str,
) -> str:
    """Forbidden composer: vanished poles (and optional t^0) skip remainder."""
    if negative_verdict == NONZERO or constant_verdict == NONZERO:
        return NONZERO
    if negative_verdict == ZERO:
        return ZERO
```

Engine also does not call `poles.certify_negative` or `pg_series.expand_polygamma_atom`. Negatives are a homemade `_is_zero` loop on `acc[p]` for `p∈[PMIN,0)` (`engine.py:132–140`). Remainder ZERO is **not** restricted to frozen Guo: any hop whose addends reconstruct and whose extracted negative coeffs vanish gets `rem=ZERO`, then LEVEL_C if C0 matches.

### Live primary hop: `α` is not remainder-certified

Inspected `guo-p2-s0-i3:G0016→G0013` only (parse + spectator split + affine classification; **no** 40s ell-hop rerun).

- `split_edge` certified (`exact_applied_undef_mul_args`); spectator `h1(a,m,n)*h1(b,ell,m)*h1(c,n,ell)`; `_split_add` reconstruction True; 14 polygamma addends; pref `π^{-3}`.
- After `ε(m)↦ε(n)+t`, all 14 polygamma arguments are affine in `t`.
- All 14 have `remainder_ok is False`, kind `unknown`, because `α` has free symbols (`beta,gamma,mu,epsilon(n)` or `epsilon(ell)`).
- Four distinct `α` of Guo shape `(βγ ± I β μ ∓ I β ε + π)/(2π)` with `β ∈ {0, ±Iβ/(2π)}`.
- `remainder_ok True = 0`, `False = 14`.

So the engine comment “energy arguments ~ 1/2 + i E” is informal domain talk, not a call to V5-G. V5-G **refuses** these `α`. Hardcoding ZERO is not “justified for frozen Guo kernels only”: it is a **soundness hole** — LEVEL_C without a remainder certificate, including on the claimed primary hop.

A parameter lemma that this `α` family never hits `Z_≤0` for real `(β,γ,μ,ε)` is conceivable (Im vanishes only on a thin set; `β=0` yields `α=1/2`). That lemma is **not implemented**. Fail-closed remainder_ok is the authority that exists.

### Live toy through the engine

| hop | `final_verdict` | level | neg | c0 | rem |
|---|---|---|---|---|---|
| `(1/u)+f` vs `f` | NONZERO | LEVEL_B | NONZERO | ZERO | UNKNOWN |
| `f+u` vs `f` | ZERO | LEVEL_C | ZERO | ZERO | ZERO |

First row: surviving pole is caught by negatives (good). Remainder is UNKNOWN only because `neg≠ZERO` in the hardcoded rule, not because `remainder_ok` ran. Second row: LEVEL_C minted with hardcoded rem ZERO and no remainder_ok.

### Verdict on LEVEL_C remainder soundness

**Unsound.** Frozen L-A “LEVEL_C ZERO / negatives vanish / C0 matches” can be true as a C0+pole statement and still fail LEVEL C as specified (`PROTOCOL.md:15–16`, `schema.py:100–102`), because remainder was never certified. Cached `GUO_V5_RESCORE.json` primary `remainder: "ZERO"` is that hardcoded bit, not V5-G.

Wiring remainder_ok as-is on G0016 atoms would drop the primary hop to UNKNOWN at LEVEL_B (`schema.py:100–101`). That is the correct fail-closed outcome. Restoring LEVEL_C would require a real remainder certificate for symbolic Guo `α`, not a comment and not hop retune.

---

## 2. Pole window — `NTERMS=3`, `PMIN=-6`, `PMAX=0`

Constants: `engine.py:23–25`. Extraction: `series(t,0,NTERMS)` then `coeff(t,p)` for `p∈[PMIN,PMAX]` (`125–129`).

### SymPy `n` vs Laurent window

`Expr.series(t,0,n)` is remainder order `O(t^n)`, not “n Laurent coefficients” and not the width of `[PMIN,PMAX]` (7 slots). Live:

- Holomorphic `polygamma(0,1+t)` at `n=3`: `O(t^3)`, includes `t^0,t^1,t^2`.
- Same at `n=0`: `O(1)` — **`t^0` is dropped**. If engine ever set `NTERMS=PMAX=0`, C0 would be missing.
- V5-B maps the window correctly: `nterms = hi+1` (`pg_series/expand.py:99–102`). Engine ignores that package and hardcodes `NTERMS=3` (`PMAX+1` would be 1). Extra positive powers are computed and discarded; they are not used as remainder.

### Order-3 rational pole × holomorphic polygamma

Toy `t^{-3} polygamma(0,1+t)`:

- `n=3` and `n=1` and `n=8` all give the same `C_0=π^4/90 = polygamma(3,1)/6`.
- Principal part `t^{-3}…t^{-1}` is present at `n=3`.
- `remainder_ok(1+t)` True; `remainder_ok(t)` False / UNKNOWN.

So for a **certified holomorphic** polygamma, a rational pole of order 3 is inside `t^{-6}…t^0`, and `NTERMS=3` does not truncate C0 on this class. The n-count vs window mismatch is real but, for C0 of order ≤3 holomorphic atoms, not the bug that mints false ZERO.

### If pole order exceeds 6

Toy `t^{-7} polygamma(0,1+t)` at `n=3`: `C_{-7}=-γ` is in the series, but the engine never reads `p<-6`. Here `C_{-6}=π^2/6≠0`, so the truncated window would still report NONZERO, not silent ZERO. False LEVEL_C from a too-shallow `PMIN` requires a principal part supported only below `-6` after summing atoms (possible in principle, not observed on frozen Guo rationals).

### Frozen Guo rational orders (no ell-hop series)

Original G0016 **does** contain cubic energy poles: `(ε(ell)-ε(m))^{-3}` and `(ε(ell)-ε(n))^{-3}`, plus `^{-2}` and `^{-1}` on those differences. They are **direction-dependent**:

| degeneration | per-term rational `pole_order` (pg→1) | min |
|---|---|---|
| `ε(m)→ε(n)` (primary) | `{0:10, -1:4}` | **-1** |
| `ε(ell)→ε(n)` | `{0:4, -1:3, -2:3, -3:4}` | **-3** |

Primary hop: cubic factors are spectators in `t` (holomorphic unless a further coincidence). Matches frozen VERDICT “order-1 removable pole” as a **rational** statement. Ell hop: genuine order-3 poles, not merely slower CAS.

`PMIN=-6` covers these rational orders with margin on `m` and some margin on `ell` (order 3). Combined with a **singular** polygamma of order `n+1` (`n=2` → extra 3) a term could approach the window floor. That is exactly why remainder_ok must gate the claim that `pmin` bounds the valuation (`sufficiency.py:27–29, 115–118`). Engine skips the gate.

**Pole-window argument.** For holomorphic polygamma and rational order ≤3, `t^{-6}…t^0` plus `series n=3>0` is enough to see C0 and the principal part. It is **not** a certificate that Guo polygamma is holomorphic (symbolic `α`). It is **not** enough if valuation `<-6`. Do not raise `PMIN`/`NTERMS` to “decide” ell-hops; the m-hop remainder hole is wiring, not window size.

---

## 3. Removable vs true poles — leftover `t^{-1}` is NONZERO

Schema (`schema.py:89–95, 100–102`):

- Any `negative_verdict==NONZERO` or `constant_verdict==NONZERO` → hop **NONZERO** (LEVEL_B if the leftover is a negative coeff, else LEVEL_C).
- Matching `t^0` does not skip a leftover pole.
- LEVEL_C ZERO iff reconstruction, atoms expanded, negatives ZERO, constant ZERO, **and** remainder ZERO.

Tests: `tests/test_cl_schema.py:33–41` (`t0` match + surviving pole → NONZERO); `tests/test_cl_poles.py:80–117` (`certify_negative({-1:1, 0:K})` NONZERO, then `compose_hop_verdict` NONZERO). PROTOCOL `t^0` match with surviving `t^{-1}` is NONZERO (`PROTOCOL.md:18`).

Live: `1/u+f` vs `f` → `summed['-1']='nonzero'`, hop NONZERO LEVEL_B. `f+u` vs `f` is the removable/holomorphic case (engine LEVEL_C, remainder uncertified).

Engine negatives use `_is_zero`, not `certify_negative`, but the composer still forbids treating leftover `t^{-1}` as ZERO. Confirmed.

---

## 4. Iterated vs joint — family gate still injects `CONSISTENCY_UNKNOWN`

Track V3 rule (`iterated_confluence/schema.py:41–48, 188–221`): PATH_ZERO is not FAMILY_ZERO; iterated limit is not joint limit unless consistency is `CONSISTENT_ZERO` when `require_path_independence`. Two PATH_ZERO paths with `CONSISTENCY_UNKNOWN` → FAMILY_UNKNOWN (`tests/test_ic_schema.py:65–83`). Empty consistency + independence required → FAMILY_UNKNOWN even for one PATH_ZERO (`41–49`).

V5 rescore (`eval/guo_v5_rescore.py:144–151`):

```144:151:research/coefficient_laurent/eval/guo_v5_rescore.py
        covering = [p for p in path_rows if len(p.steps) >= 2] or path_rows
        cons = [CONSISTENCY_UNKNOWN] if len(covering) > 1 else []
        fam_v = compose_family_verdict(
            path_verdicts=[p.path_verdict for p in covering],
            consistency_verdicts=cons,
            reconstruction_verdicts=["ZERO"],
            require_path_independence=bool(cons),
        )
```

Frozen family `guo-p2-s0-i3` has **three** covering paths with `len(steps)≥2`:

- `G0016→G0013→G0012`
- `G0016→G0014→G0012`
- `G0016→G0015→G0012`

So `cons=[CONSISTENCY_UNKNOWN]`, `require_path_independence=True`. One PATH_ZERO covering path cannot mint FAMILY_ZERO. Live `compose_family_verdict` on `[PATH_ZERO, PATH_UNKNOWN, PATH_UNKNOWN]` + cons UNKNOWN → `FAMILY_UNKNOWN`. Two PATH_ZERO + cons UNKNOWN → `FAMILY_UNKNOWN` (the `xy/(x^2+y^2)` joint-vs-iterated shape).

`GUO_V5_RESCORE.json`: all 7 families `FAMILY_UNKNOWN`; primary family `n_path_zero=5` (V5 `G0016→G0013`, V4 diagonal `G0013/14/15→G0012`, and the composed `G0016→G0013→G0012`); `FAMILY_ZERO=0`; `d2_unlocked=false`.

`guo-p2-s2-i4` has no 2-step covering path; the `or path_rows` fallback still has two 1-step paths, so cons is still injected. No frozen family is a single PATH_ZERO auto-FAMILY_ZERO.

**Family gate: hold.** V5 does not auto-FAMILY_ZERO from `G0016→G0013→G0012`.

Caveat (not triggered on freeze): if `len(covering)==1`, code sets `require_path_independence=False` and would allow FAMILY_ZERO without consistency. Frozen Guo covering graphs are multi-path.

---

## 5. Ell-hops — timeout is UNKNOWN, not LEVEL_C; harder analytically **and** at runtime

Timeout payload (`guo_v5_rescore.py:78–79`):

```python
existing = {"final_verdict": "UNKNOWN", "proof_level": "LEVEL_A", "provenance": "timeout"}
```

No `remainder_verdict`, no negatives, no C0. Cached ell rows: `verdict=UNKNOWN`, `level=LEVEL_A`, `remainder=null`. Cannot be read as LEVEL_C. Exception path is the same LEVEL_A UNKNOWN (`80–81`). Schema never sees a timeout as ZERO.

**Analytic difference, not only runtime.**

Same source G0016. `ε(m)→ε(n)` hits `(ε(m)-ε(n))^{-1}` (order 1) while cubic `(ε(ell)-ε(*))^{-3}` stays holomorphic in `t`. `ε(ell)→ε(n)` hits `(ε(ell)-ε(n))^{-3,-2,-1}` (rational min order 3). Polygamma `t`-dependence: 4 args move with `m`, 6 with `ell`, 4 with neither, 0 with both. V4 already: m-hop `old_unknown_reason=laurent` (27327-op together), ell-hops `timeout`. V5: m-hop ~11s LEVEL_C claim, ell-hops 40s process timeout.

Do not raise `EDGE_SECONDS` / `NTERMS` / `PMIN` to convert timeout into ZERO. Timeout stays UNKNOWN.

---

## 6. Numeric probes must not mint ZERO

`numeric/probe.py:1–5, 20, 52–53, 85–88, 101–103`. `ALLOWED_STATUSES={agree,disagree,undecided}`. `ZERO` not in the set; `numeric_probe` returns UNDECIDED on forbidden status. Strong disagreement is `SUSPECT_NONZERO` **investigation** only (`3–4, 338–346`). Live: cubic `agree` (not ZERO); `1/u` vs `0` `undecided` (not ZERO). Tests `tests/test_cl_numeric.py` enforce this.

Numeric is not in the engine ZERO path.

---

## Coordinator action (remainder only)

| item | action |
|---|---|
| Engine remainder | **Must patch, fail-closed:** set `remainder_verdict` from `remainder_ok` / `remainder_verdict` on each polygamma atom (UNKNOWN unless all True). Do not keep `rem = ZERO if (recon and neg == ZERO)`. |
| Expected effect on claimed L-A | Primary hop demotes to UNKNOWN LEVEL_B under current V5-G (14/14 symbolic `α`). That is sound. Do not weaken `_classify_alpha` to restore LEVEL_C in the same patch. |
| Ell-hops | Do not retune `NTERMS`, `PMIN`, `PMAX`, `EDGE_SECONDS`, `PAIR_TOGETHER_CAP`. Leave timeout as UNKNOWN LEVEL_A. |
| Family / D2 | Leave locked. `d2_unlocked` is already false; remainder patch does not create FAMILY_ZERO. |
| Frozen authorities | Do not edit freeze/V3/V4/SOL/historical runs. Cached `remainder: ZERO` on G0016→G0013 is not a V5-G certificate. |

D2 remains LOCKED (`STATUS.md:9`, `TRACK_V5_CLOSED.md:24`, `GUO_V5_RESCORE.json:335`).

---

## Commands and results

```
cd /private/tmp/wt-v5-review-r2
export PYTHONPATH=.
/Users/kawawong/Projects/symbolic-compactification/.venv/bin/python -m pytest \
  tests/test_cl_remainder.py tests/test_cl_poles.py tests/test_cl_schema.py \
  tests/test_cl_numeric.py tests/test_cl_basis.py -q
```

**53 passed in 0.34s.**

Live inspection (same interpreter): engine has no remainder import; hardcoded rem line present; `NTERMS,PMIN,PMAX = 3,-6,0`; series toys as in §2; engine `1/u+f` vs `f` NONZERO LEVEL_B; `f+u` vs `f` ZERO LEVEL_C rem ZERO; G0016→G0013 `remainder_ok` 0/14; family compose FAMILY_UNKNOWN; numeric never ZERO.

No 12×40s ell-hops rerun. No NTERMS/PMIN/EDGE_SECONDS change.
