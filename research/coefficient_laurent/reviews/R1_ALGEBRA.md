# R1 algebra review — atom reconstruction and per-polygamma C0

**Reviewer:** R1 (symbolic algebra), isolated worktree `/private/tmp/wt-v5-review-r1`, branch `work/v5-review-r1` at parent `fb3b929`.
**Scope:** atom split, reconstruction, grouping, C0 matching. No ell-hop reruns. No hop retune. D2 stays LOCKED. No FAMILY_ZERO.
**Python:** `/Users/kawawong/Projects/symbolic-compactification/.venv/bin/python` (CPython 3.12), `PYTHONPATH=.`

## Verdict

**L-A edge ZERO is sound as an *edge* certificate** of (i) exact `pref * Sum T_i` reconstruction, (ii) negative Laurent coefficients vanishing by `expand == 0`, and (iii) per-polygamma C0 matching by rational-function identity (`together` numerator expands to 0). It is **not** a false ZERO of the C0 algebra.

It is **not** FAMILY_ZERO (7/7 families remain FAMILY_UNKNOWN; 12 ell-hops remain UNKNOWN). EDGE V_GAIN ≠ FAMILY V_GAIN. Track D2 must stay LOCKED.

Remainder at LEVEL_C is **not** discharged by `remainder_ok` (0/14 G0016 atoms; α has free symbols). The engine auto-sets `remainder_verdict = ZERO` when reconstruction and negatives succeed (`engine.py:151`). That is a composition assumption about Guo energy arguments, not a C0 identity. It does not reverse the C0 match. See patches.

No reproducer of a false C0 ZERO was found.

---

## 1. Reconstruction: `pref * Sum T_i`

**Answer:** on the claimed G0016 path the split is an **exact tree reconstruction** (`reconstruct == src`). The gate also accepts expand-zero or cancel-zero (`_exact_eq`). It is **not** a full-kernel `together` identity. `atoms/core.py` never calls `together`.

### Gate

```188:192:research/coefficient_laurent/atoms/core.py
        encoding_ok = _exact_eq(rebuilt_add, add)
    kernel_ok = pref_ok and _exact_eq(pref * add, original)
    reconstruction_ok = encoding_ok and kernel_ok
```

```417:430:research/coefficient_laurent/atoms/core.py
def _exact_eq(left: sympy.Expr, right: sympy.Expr) -> bool:
    if left == right:
        return True
    try:
        if sympy.expand(left - right) == 0:
            return True
    except Exception:
        pass
    try:
        if sympy.cancel(left - right) == 0:
            return True
    except Exception:
        pass
    return False
```

`_split_pref_add` (`atoms/core.py:270-292`) prefers structural `(pref * chosen) == expr`, then `_exact_eq`. Engine `_split_add` (`engine.py:42-54`) is `==` or `expand(pref * add - expr) == 0` only.

### Reconstruction table (live, Guo map)

| hop | n_atoms | classes | `reconstruction_ok` | `reconstruct == src` | expand-zero | cancel-zero | engine `_split_add` | `together` used |
|---|---:|---|---|---|---|---|---|---|
| `guo-p2-s0-i3:G0016→G0013` | 14 | 14×POLYGAMMA | True | **True** | True | True | True, same 14-term Add, `pref=pi**(-3)` | no |
| synthetic pg-sum `(ψ(y)-ψ(x))/(y-x)` | 2 | POLYGAMMA | True | True | True | True | True | no |
| cubic `(x³-y³)/(x-y)` | 2 | POWER/RATIONAL | True | True | True | — | — | no |

G0016 live:

- spectator `h1(a,m,n)*h1(b,ell,m)*h1(c,n,ell)` (no `epsilon(m)`).
- `pref = spectator / pi**3`.
- `split_note = exact_applied_undef_mul_args`.
- `atom_decomposition_hash` (content) `0ce6d05b080afe66165704caa0dddbf014132886959829f2bf63f5e5d6b48a06` matches `ATOM_MAP.json`.
- each atom has exactly one polygamma; orders `{0,1,2}`; 6 distinct arguments; 14 distinct `canonical_atom_hash`.
- source/target `text_sha256` match freeze: `aaa1debec0…` / `61476197f7…`.

ATOM_MAP `n_reconstruction_ok = 18/18` is evaluation-only (`does_not_adjudicate_zero: true`). Confirmed for the primary hop by live `decompose` + `reconstruct`.

### Engine vs atoms split (fail-closed, not a false ZERO)

If a Mul contains **two** polygamma `Add`s, engine keeps the last Add and puts the first into `pref` only when it is *not* a polygamma Add — so both Adds overwrite `add` and `pref=1`. Live: `small*large` → `recon ok=False`, `(pref*add)==prod` False. Hop would return UNKNOWN (`engine.py:113-119`). Atoms `max(pg_adds, key=_ops)` reconstructs. **G0016 has a single polygamma Add**; both splitters agree.

---

## 2. `_canon_pg` / `_group_by_polygamma`

Hop C0 uses `c0/match.py`, **not** `grouping/group.py` (that module is tests-only).

```170:218:research/coefficient_laurent/c0/match.py
def _group_by_polygamma(expr: sympy.Expr) -> dict[sympy.Expr, sympy.Expr]:
    ...
            if _is_polygamma_factor(factor):
                pg.append(_canon_pg(factor))
            else:
                rest.append(factor)
        ...
        key = sympy.Mul(*pg) if pg else _ONE
```

`_canon_pg` is `expand` then `together` on the polygamma **argument**, plus `Pow` of polygamma. It does **not** `cancel` the argument.

### Collision attempts (live)

| attempt | keys | `match_constant` | false ZERO? |
|---|---|---|---|
| mixed orders `2ψ₁+3ψ₂` vs `5ψ₁` | split `{ψ₁,ψ₂}` | NONZERO, residual `3*polygamma(2,z)` | no |
| `ψ₁(z)` vs `ψ₁(z+1)` | distinct | NONZERO | no |
| `ψ**2` vs `ψ*ψ` | same `ψ(1,z)**2` | ZERO (`identical`) — same function | no |
| uneval `x*(ψ₁+ψ₂)` | expand then 2 keys | — | no |
| `2**ψ(1,z)` vs `2**ψ(2,z)` (pg not a Mul factor) | both key `1` | **UNKNOWN** (not ZERO) | no |
| `x/ψ(z)` vs `x/ψ(z+1)` | keys `1/ψ` (Pow of pg) | NONZERO | no |
| `(x-y)ψ` vs `(y-x)ψ` (hidden sign) | same pg | NONZERO | no |
| `(x-y)ψ` vs `-(y-x)ψ` | same pg | ZERO — rational identity | no |
| `2*ψ(1,z)` vs `ψ(1,2z)` | distinct | NONZERO | no |
| `ψ(1,x)` vs `ψ(1,log(exp(x)))` | distinct | NONZERO | no |
| `ψ(1,1/x+1)` vs `ψ(1,(1+x)/x)` | same after together | ZERO — same meromorphic arg | no |
| removable arg `ψ(1,(x²-1)/(x-1))` vs `ψ(1,x+1)` | **distinct** (`together` does not `cancel`) | NONZERO | conservative miss, not false ZERO |
| `ψ(2-1,z)` vs `ψ(1,z)` | same (Integer) | ZERO | no |

`grouping/group.py` keys include a sign-normalized `denom_signature`, so `ψ/d₁ + ψ/d₂` stay split. C0 matcher **intentionally** sums all rational prefactors of the same canon polygamma (one key). That is required to compare C0 to G0013; it is not a hidden-factor collision.

Nested non-factor polygamma (`2**ψ`) falls under key `1`. Equality then goes through `_rational_coeffs_equal`, which returned UNKNOWN, not ZERO.

---

## 3. Per-atom `together(diff)` vs exact rational identity

```225:269:research/coefficient_laurent/c0/match.py
def _rational_coeffs_equal(a: sympy.Expr, b: sympy.Expr) -> Optional[bool]:
    ...
        tog = sympy.together(diff)
    ...
        if sympy.expand(num) == 0:
            return True
```

`PAIR_TOGETHER_CAP = 4000`. True is returned only for (i) tree equality, (ii) `expand(diff)` identically 0, (iii) `together(diff)==0`, or (iv) `expand(together-numerator)==0`. Non-polynomials that do not cancel return `None` (UNKNOWN), **not** ZERO.

### Synthetic rationals

| pair | `_rational_coeffs_equal` | hop-style match | false ZERO |
|---|---|---|---|
| identical | True | ZERO/identical | no |
| `(x²-1)/(x-1)` vs `x+1` | True | ZERO/pg_atoms | no (removable, true identity) |
| `1/(x-y)` vs `-1/(y-x)` | True | ZERO/pg_atoms | no |
| `1/(x-y)` vs `8/(8x-8y)` | True | ZERO/pg_atoms | no |
| `1/(y-x)²` vs `1/(x-y)²` | True | ZERO/pg_atoms | no |
| `x/x` vs `1` | True | ZERO/identical | no |
| `1/(x-y)` vs `1/(x-z)` | **None** | UNKNOWN | no (missed NONZERO) |
| `x+1` vs `x+2` | False | NONZERO | no |
| `1` vs `0` | False | NONZERO | no |
| large unequal dens (ops>80) | None | UNKNOWN | no |
| `sin²+cos²-1` vs 0 | None | — | no |
| `exp(x)exp(-x)-1` vs 0 | True (`expand==0`) | — | true CAS identity, not a mismatch |
| `Abs(x)-x` vs 0 | None | — | no |

**False-ZERO count on the attack set: 0.**

Returning True is equivalent to a rational (or expand) identity wherever the denominator is not the zero expression (`den == 0` → None). It can fail to prove NONZERO (conservative UNKNOWN). That cannot mint a G0016 ZERO.

### Live G0016 C0 vs G0013 (12 keys)

`C0 ops = 990`, `work_t ops = 327`, union ops 1317 > `OPS_CAP=800`. Grouping runs **before** the size-guard (`match.py:67-75`); `pg_atoms` is size-guard-exempt (`_ZERO_EXEMPT`, `match.py:340-347`).

| | C0 | G0013 local | union |
|---|---:|---:|---:|
| polygamma keys | 12 | 12 | 12 |
| C0-only / tgt-only | ∅ | ∅ | — |
| keys with pg in the **coefficient** | 0 | 0 | — |

Every pair: `a != b`, `expand(a-b) != 0`, **`expand(together(a-b).numerator) == 0`**, `_rational_coeffs_equal` True. Several pairs also have `together(diff)==0`.

Largest live coeff ops: L=1155 / R=838 (ψ₁ at ell+μ argument) and L=331 / R=1506 (ψ₁ at n±μ). Sum ≲ 1837 < 4000.

`match_constant(C0, work_t)`: **ZERO / `pg_atoms`**, steps `('ops:1317', 'pg_atoms:n=12', 'pg_atoms:ZERO')`, `used_full_together=False`.

This is the claimed identity: 12 shared polygamma atoms, each rational prefactor difference has together-numerator 0. Not 27k together of the kernel.

---

## 4. Grouping-key collisions on the Guo hop

Source atoms: 14 polygamma terms, 6 arguments `{ε(ell), ε(m), ε(n)} × {±iμ}`. After `ε(m) → ε(n)+t`, m-arguments collide with n-arguments. C0 and G0013 both have **4 arguments × orders {0,1,2} = 12 keys**, identical as sympy expressions.

A false ZERO would require two *unequal* polygamma kernels to share a canon key **and** matching leftover rationals. Live keys are the explicit affine arguments

`(βγ ± iβμ ∓ iβ ε(ell|n) + π)/(2π)`.

`_canon_pg` did not cancel distinct meromorphic arguments on the attack set (it even *failed* to merge `(x²-1)/(x-1)` with `x+1`). Hidden rational prefactors stay in the coefficient and are compared. **No collision that equalizes unequal kernels on this hop.**

---

## 5. `atom_decomposition_hash` vs hop ZERO / cache

Engine hash is an **ops-count join**, not atom content:

```111:111:research/coefficient_laurent/engine.py
        cert.atom_decomposition_hash = sha256_text("|".join(str(_ops(t)) for t in terms))
```

Live G0016: engine hash `fcef3113a37e58dab52a9d87539fb1cf7b16692767dd5f43a3ab23e6e767a642` from term ops `[25,26,26,26,49,33,33,36,36,50,43,43,70,68]`. Distinct from atoms content hash `0ce6d05b…`.

**Collision:** two different 2-term sums with ops `(1,1)` share that hash.

**Does it participate in hop ZERO? No.**

- `compose_hop_verdict` (`schema.py:79-102`) does not read the hash.
- `engine.py` imports `certificate_key` and never calls it.
- Rescore keys on **full text** plus concatenated member `text_sha256`, not the ops-count digest:

```58:66:research/coefficient_laurent/eval/guo_v5_rescore.py
        key = certificate_key(
            source_text=src_t,
            target_text=tgt_t,
            ...
            atom_decomposition_hash=hop["source"]["text_sha256"] + hop["target"]["text_sha256"],
            source_member=hop["source"],
            target_member=hop["target"],
        )
```

`certificate_key` (`cache.py:41-67`) always includes `src_h`, `tgt_h` from full text. Same ops-hash + different text → distinct keys. G0014 cannot alias G0016.

Hygiene risk only if a later consumer treats `cert.atom_decomposition_hash` as a content identity. See patches.

---

## 6. Spectator peel

`split_edge(..., degeneration=var)` refuses a spectator that `S.has(degeneration)` (`spectator/split.py:79-80, 168-174, 198-199`).

**Control `y(y+3)` vs `3y` as `y→0`:**

| call | certified | note | hop |
|---|---|---|---|
| `split_edge(A,B)` no degeneration | True, `S=y`, locals `y+3` and `3` | `exact_common_factor` | — |
| `split_edge(A,B, degeneration=y)` | **False** | `spectator_depends_on_degeneration` | — |
| `sparse_laurent_limit(A,B,y,0)` | locals unpeeled | — | **NONZERO** LEVEL_C, `c0=NONZERO`, `C0=0` vs `3y` |

If `y` were peeled, series of `y+3` at 0 would give C0=3 vs target 3 → false ZERO of the original pair. Peel blocks that. `S = ε(m)-ε(n)` is also refused under `degeneration=ε(m)`.

G0016 spectator is the three `h1` factors (`exact_applied_undef_mul_args`), independent of `ε(m)`.

---

## 7. `used_full_together` on G0016→G0013

Hard-wired False in every `ConstantMatchResult` (`match.py:33, 43, 384`). Engine certificate initializes `used_full_together=False` (`engine.py:101`) and never sets it True.

Live hop with `sympy.together` tracer:

- hop **ZERO LEVEL_C**, `used_full_together=False`, `max_intermediate_ops=1696`
- negatives: `C_{-6}…C_{-2}` structurally 0; **`C_{-1}` ops=93, `==0` False, `expand==0` True, `together==0` False, has polygamma**. Vanishes by expand, not together.
- `together` calls during the hop: **90**, **0 with polygamma in the argument**, max ops **1994**
- calls with ops≥800: 4 (1994, 1838, 1838, 1666) — rational coeff *differences* of ψ₁ groups, matching PAIR_TOGETHER of ~1500-op prefactors
- C0−G0013 blob: ops 1317, **has polygamma**. Never passed to `together` (would have been a `has_pg=True` call)

`_canon_pg` together is only on affine arguments (~11 ops). Per-atom together is scoped to polygamma-free rationals under cap 4000. **The 990+327 blob is never `together`'d.**

---

## Remainder (not a C0 false ZERO; LEVEL_C assumption)

```148:152:research/coefficient_laurent/engine.py
        # Affine polygamma arguments at t=0 are not nonpositive integers
        # for the frozen Guo kernels (energy arguments ~ 1/2 + i E). Remainder
        # is ZERO only when negatives and reconstruction succeeded; else UNKNOWN.
        rem = ZERO if (recon and neg == ZERO) else UNKNOWN
```

`remainder.sufficiency.remainder_ok` is **not called**. Live: 0/14 G0016 atoms `remainder_ok`. Failure mode: `_classify_alpha` returns `"unknown"` because `α` has free symbols `{mu, beta, gamma, ell}` (and `ε(n)` on m-atoms). Fail-closed remainder would be UNKNOWN → hop LEVEL_B UNKNOWN, not a C0 mismatch.

Series evidence that extra polygamma poles did not appear: `PMIN=-6` window, `C_{-6}…C_{-2}` empty, `C_{-1}` expand-zero. That is empirical for this kernel, not `remainder_ok`.

---

## Commands and pass/fail

```
cd /private/tmp/wt-v5-review-r1
export PYTHONPATH=.
/Users/kawawong/Projects/symbolic-compactification/.venv/bin/python -m pytest \
  tests/test_cl_atoms.py tests/test_cl_c0.py tests/test_cl_grouping.py tests/test_cl_schema.py -q
```

**35 passed** in 1.36s.

Live attacks (not committed): reconstruct G0016 from `GUO_OBLIGATION_MAP.json`; `sparse_laurent_limit(G0016,G0013)` with together tracer (~11s, not an ell-hop); C0 grouping dump; spectator control hop; synthetic grouping/`_rational_coeffs_equal` matrix.

Ell-hops were **not** rerun.

---

## Recommended coordinator patches

Do **not** retune ell-hops. Do **not** unlock D2. Do **not** convert UNKNOWN/timeout/size-guard to ZERO. Do **not** promote FAMILY_ZERO.

1. **Hash hygiene (no verdict change).** Store `atoms.core.decomposition_hash` (pref srepr + atom content hashes) on the certificate instead of `sha256("|".join(ops))`. Rescore already keys on full text; this only prevents a later ops-count alias.
2. **Remainder composition (scientific, not C0).** Stop auto-ZERO of remainder. Either call `remainder_ok` per atom (will fail closed on symbolic α) or keep an explicit `remainder_assumption: guo_energy_not_nonpos_int` distinct from algebraic ZERO. Do not treat that assumption as C0 evidence. If remainder stays UNKNOWN, G0016 is LEVEL_B UNKNOWN and L-A as *LEVEL_C* would need a remainder-track close — **C0 matching itself remains sound**.
3. **Unify `_split_add` with `_split_pref_add`.** Engine last-Add vs atoms max-ops. Current engine fail-closed is safe; unify to avoid a future two-Add UNKNOWN that atoms could reconstruct. Not needed for G0016.
4. **Optional: `_canon_pg` `cancel` after together.** Would merge removable arguments. Current behaviour is conservative (false NONZERO risk). Do not weaken UNKNOWN→ZERO elsewhere.
5. **Optional: `_rational_coeffs_equal` NONZERO for `expand(num) != 0` when den is a non-zero polynomial.** Closes UNKNOWN holes such as `1/(x-y)` vs `1/(x-z)`. Must not be used to flip size-guard UNKNOWN to ZERO.

No patch to `schema.py` composition rules. No Guo identity tables. No hop-engine timeout/size retune.
