# R4 — Track V5 verification / LEVEL C composition / cache identity

Isolated worktree `/private/tmp/wt-v5-review-r4`, branch `work/v5-review-r4`, parent `fb3b929`.
Python `/Users/kawawong/Projects/symbolic-compactification/.venv/bin/python`, `PYTHONPATH=.`.
No LLM. No hop retune. No D2 unlock. Frozen authorities not edited.
This file is the only write.

**Overall: FAIL on remainder-gated LEVEL C. PASS on schema-only hop ZERO, cache identity, FAMILY_ZERO=0, D2 locked.**

The hop composer cannot mint ZERO except the all-ZERO LEVEL_C tuple. The engine still feeds `remainder_verdict=ZERO` without calling `remainder_ok`. On the frozen primary hop that package returns UNKNOWN for 14/14 polygamma units. D2 stays locked.

---

## Closed-track claims

| Claim | Verdict | Notes |
|---|---|---|
| Artifact: 6 m→n hops LEVEL_C ZERO | **PASS** | `GUO_V5_RESCORE.json`: six `G0016→G0013` / `G0023→G0020` rows, `neg=c0=remainder=ZERO`, `together=false`, `max_ops=1696` |
| Artifact: 12 ell-hops UNKNOWN timeout | **PASS** (count) / **PARTIAL** (provenance) | 12 rows `UNKNOWN`+`LEVEL_A` with `neg/c0/remainder/max_ops/together = null`. JSON drops `provenance: timeout` |
| FAMILY_ZERO=0 | **PASS** | 7×`FAMILY_UNKNOWN`; majority PATH_ZERO is not FAMILY_ZERO |
| d2_unlocked=false | **PASS** | `n_fz>0 or FAMILY_NONZERO>0` is false; neither fired |
| Schema: only LEVEL C may be hop ZERO | **PASS** | Exhaustive compose: 1 ZERO cell, always `LEVEL_C` |
| LEVEL A atom-series is not ZERO | **PASS** | `atoms_expanded=True` + all UNKNOWN → `(UNKNOWN, LEVEL_A)` |
| t^0 match with surviving t^{-1} is NONZERO | **PASS** | `neg=NONZERO, c0=ZERO, rem=ZERO` → `(NONZERO, LEVEL_B)` |
| LEVEL C remainder independently certified | **FAIL** | Engine auto-ZERO remainder; `remainder_ok` unused and False on frozen Guo atoms |
| Cache keys include full member text SHA256 | **PASS** | `certificate_key` hashes source/target text; empty text refused |
| V4 alias G0014→G0012 onto G0016→G0013 forbidden | **PASS** | Keys differ even with missing `text_sha256`, same degeneration, colliding atom-count hash |
| Falsifier / generic false ZERO = 0 | **PASS** | Required pytest 60 passed; generic `false_ZERO=0` |
| `used_full_together` cannot be True on a ZERO cert | **PASS** | No assignment to True in-tree; frozen ZERO rows `together=false` |
| D2 stays locked | **PASS** | Not unlocked. Do not open. |

---

## Attack table

| # | Attack | False ZERO? | Fires on frozen artifacts? | Result |
|---|---|---|---|---|
| 1 | `compose_hop_verdict` ZERO combinations other than all-ZERO LEVEL_C | No | No | Only `(recon=True, atoms=True, neg=ZERO, c0=ZERO, rem=ZERO)` → ZERO LEVEL_C |
| 1b | Engine remainder auto-ZERO (composition *input*) | Uncertified ZERO, not schema-false | **Yes** on all 6 recorded LEVEL_C hops | `remainder_ok` False on 14/14 primary polygamma units |
| 2 | Timeout payload `LEVEL_A` + missing neg/c0 treated as partial LEVEL_C | Schema: no. Reader `or ZERO`: **yes** | Not in committed composer | JSON also drops `provenance` |
| 2b | `cache.put` of timeout poisons a later ZERO | Blocks true ZERO; does not mint ZERO | Not on frozen 6 vs 12 (distinct keys) | In-process first-writer on the **same** key |
| 3 | V4 alias: missing `text_sha256`, same degeneration | No | No | `k14 != k16`; `cache.get(k16)` is None after ZERO on k14 |
| 3b | Empty text | N/A | No | `ValueError: refusing cache key: empty member text` |
| 3c | Colliding ops-count `atom_decomposition_hash`, different texts | No | No | Keys still differ via text SHA256 |
| 4a | Hardcoded `reconstruction_verdicts=["ZERO"]` | Would FAMILY_ZERO if paths+cons already ok | **No** (covering mixed PATH_UNKNOWN; cons UNKNOWN) | Latent hole |
| 4b | Single covering PATH_ZERO skips consistency (V3 R2) | Would FAMILY_ZERO | **No** (covering counts 3 or 2, never 1) | Latent hole |
| 4c | Majority PATH_ZERO as FAMILY_ZERO | No | No | 5 PATH_ZERO / family still FAMILY_UNKNOWN |
| 4d | `d2_unlocked` | N/A | No | False |
| 5 | Falsifier / generic false ZERO | No | N/A | 0 false ZERO |
| 5b | Surviving pole + matching t^0 | NONZERO, not ZERO | N/A | Schema + falsifier `V5L_01` |
| 5c | Atoms-only | UNKNOWN LEVEL_A | N/A | Schema + generic `A-atoms-only-not-zero` |
| 5d | Size-guard / cancel cap ZERO a 1317-op blob | Cancel cannot. `pg_atoms`/`identical` exempt can ZERO *true* identities above OPS_CAP | Frozen C0 match is per-polygamma, not blob cancel | See Q6 |
| 6 | `_ZERO_EXEMPT={pg_atoms,identical}` bypass OPS_CAP | Identical huge trees: true ZERO. `pg_atoms` on key-1 (no polygamma) can ZERO algebraic identities above 800 ops. Wrong-pg grouping did **not** mint a false ZERO on the attacks below | Not a frozen false ZERO | Exempt is live |
| 7 | `used_full_together=True` on ZERO | No | No | Always False; never assigned True |

---

## 1. `schema.compose_hop_verdict` — only all-ZERO LEVEL_C

Source: `research/coefficient_laurent/schema.py:79-102`.

```79:102:research/coefficient_laurent/schema.py
def compose_hop_verdict(
    *,
    reconstruction_ok: bool,
    atoms_expanded: bool,
    negative_verdict: str,
    constant_verdict: str,
    remainder_verdict: str,
) -> tuple[str, str]:
    ...
    if not reconstruction_ok:
        return UNKNOWN, LEVEL_A
    if any(v == NONZERO for v in (negative_verdict, constant_verdict)):
        return NONZERO, LEVEL_B if negative_verdict == NONZERO else LEVEL_C
    if not atoms_expanded:
        return UNKNOWN, LEVEL_A
    if negative_verdict != ZERO:
        return UNKNOWN, LEVEL_A
    if constant_verdict != ZERO or remainder_verdict != ZERO:
        return UNKNOWN, LEVEL_B
    return ZERO, LEVEL_C
```

Enumeration (bools × `{ZERO,NONZERO,UNKNOWN,None,"","LEVEL_C","TIMEOUT"}` = **1372** tuples):

| `(final, level)` | count |
|---|---|
| UNKNOWN, LEVEL_A | 1148 |
| NONZERO, LEVEL_B | 98 |
| NONZERO, LEVEL_C | 84 |
| UNKNOWN, LEVEL_B | 41 |
| **ZERO, LEVEL_C** | **1** |

The unique ZERO cell is `recon=True, atoms=True, neg='ZERO', c0='ZERO', rem='ZERO'`.

Spot checks:

| Input | Output |
|---|---|
| atoms-only all UNKNOWN | `(UNKNOWN, LEVEL_A)` |
| `neg=NONZERO, c0=ZERO, rem=ZERO` | `(NONZERO, LEVEL_B)` |
| `neg=c0=ZERO, rem=UNKNOWN` | `(UNKNOWN, LEVEL_B)` — not ZERO |
| `neg=c0=ZERO, rem=NONZERO` | `(UNKNOWN, LEVEL_B)` — remainder NONZERO is **not** hop NONZERO |
| `recon=False`, rest ZERO | `(UNKNOWN, LEVEL_A)` |
| `atoms=False`, rest ZERO | `(UNKNOWN, LEVEL_A)` |
| timeout `None` neg/c0/rem | `(UNKNOWN, LEVEL_A)` |
| `neg=UNKNOWN, c0=rem=ZERO` | `(UNKNOWN, LEVEL_A)` |

**Schema PASS.** Remainder is not inspected for NONZERO as a hop-NONZERO trigger; that is fail-closed, not a ZERO mint.

### 1b. Engine remainder input (live LEVEL C hole)

`research/coefficient_laurent/engine.py` never imports `remainder_ok`. After negatives vanish it writes remainder ZERO from reconstruction+neg only:

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
```

The remainder package is fail-closed on symbolic α (`remainder/HANDOFF.md`, `tests/test_cl_remainder.py:80-83`: `remainder_ok(a+t,t) is False`). Frozen primary hop `G0016→G0013` (split certified, 14 additive terms, 14 polygamma units) was checked **without** rerunning 40s series:

- `remainder_ok` True: **0**
- `remainder_ok` False: **14/14**
- Sample argument: `polygamma(0, (beta*gamma + I*beta*mu - I*beta*(_t + epsilon(n)) + pi)/(2*pi))` → `UNKNOWN`

If engine consulted `remainder_ok`, compose would see `rem=UNKNOWN` with `c0=ZERO` and return **`(UNKNOWN, LEVEL_B)`**, not LEVEL_C ZERO. The six recorded LEVEL_C ZEROs rest on a comment, not the remainder checker. That is a **live** composition-input failure on the closed-track hops, not a latent family hole.

D2 is still locked because families are UNKNOWN. This finding does not unlock D2 and does not retune hops.

---

## 2. Timeout payload vs LEVEL_C / cache poison

`research/coefficient_laurent/eval/guo_v5_rescore.py:78-82`:

```78:82:research/coefficient_laurent/eval/guo_v5_rescore.py
            except BudgetExceeded:
                existing = {"final_verdict": "UNKNOWN", "proof_level": "LEVEL_A", "provenance": "timeout"}
            except Exception as exc:
                existing = {"final_verdict": "UNKNOWN", "proof_level": "LEVEL_A", "error": type(exc).__name__}
            cache.put(key, existing)
```

Timeout dict has no `negative_coefficients_verdict` / `constant_term_verdict` / `remainder_verdict` / `used_full_together`. Hop rows copy those with `.get(...)` → JSON `null` (`GUO_V5_RESCORE.json` ell-hop rows). **`provenance` is not copied into `hop_rows`**, so a later reader of the committed JSON cannot distinguish timeout from any other LEVEL_A UNKNOWN.

| Reader | Compose result |
|---|---|
| raw `None` into `compose_hop_verdict` | `(UNKNOWN, LEVEL_A)` — not LEVEL_C |
| `existing.get(...) or "ZERO"` | **`(ZERO, LEVEL_C)`** — false ZERO if a reader defaults missing slots |

Cache:

- `CertificateCache.get_or_put` is first-writer (`cache.py:81-86`). Timeout occupying a key **blocks** a later ZERO on that key. Fail-closed; does not mint ZERO.
- `put` overwrites; **rescore does not overwrite** (`get` then put only if `None`, `guo_v5_rescore.py:67-82`).
- Cache is in-memory per `rescore()` call. No disk poison across processes.

Frozen 18 hops collapse to **6 identity keys** (same source/target **text**, degeneration, point, concatenated SHA256) reused across family ids:

- 4× `G0016→G0013` (m→n ZERO) share one key
- 4× `G0016→G0014` (ell timeout) share another
- 4× `G0016→G0015` share a third
- 2× `G0023→G0020` / `G0023→G0021` / `G0023→G0022`

Timeout keys ≠ ZERO keys (different target text and `epsilon(ell)` vs `epsilon(m)`). Freeze order scores m→n before ell-hops, so a timeout cannot occupy a ZERO key. **No frozen ZERO is poisoned.** Same-hop timeout would stick for later families of that ell-hop (already UNKNOWN).

LEVEL_A on timeout is the same label as atom-series UNKNOWN. It is not a partial LEVEL_C object: no neg/c0/rem, no atom records. Schema will not promote it. A sloppy reader who defaults nulls to ZERO **would**.

---

## 3. Cache identity (V4 alias replay)

`research/coefficient_laurent/cache.py:21-66`. Key tuple is

`(src_text_sha256, tgt_text_sha256, degeneration_variable, target_value, assumptions_hash, proof_method_version, atom_decomposition_hash)`.

`member_text_hash` always returns SHA256 of the **canonical full text**. Empty text raises. Stored `text_sha256` is never used as the key fragment even when it matches (both branches return `canonical`, `cache.py:36-38`). Disagreement with stored hash still uses text.

Freeze: 18/18 hops have empty `stored_text_sha256` (V4 MAP members lacked it) and a computed 64-hex `text_sha256` that matches `GUO_OBLIGATION_MAP.json` member text.

### Replay results

| Attack | Equal keys? | Cache alias? |
|---|---|---|
| Missing `text_sha256`, same `epsilon(m)→epsilon(n)`, colliding atom hash `"14-atoms"`, texts `G0014-kernel-text` vs `G0016-kernel-text` | **No** | `put(k14, ZERO)`; `get(k16) is None` |
| Same as tests `test_cl_cache.py:36-63` / `test_cl_cache_audit.py:88-97` | No | false alias count 0 |
| Empty text | refused | `ValueError: refusing cache key: empty member text` |
| Ops-count hash `sha256("12\|12\|12")`, texts `expr-A-twelve-atoms` vs `expr-B-twelve-atoms` | **No** | text SHA256 distinguishes |
| Reordered atoms, same count hash | No | `test_v5k_02` |
| Bogus shared stored hash `0*64` | No | hashes the real text (`test_v5k_05`) |
| Empty `atom_decomposition_hash` (defaults to `sha256("")`) | still distinct via text | `test_v5k_06` |

Rescore passes `atom_decomposition_hash=hop["source"]["text_sha256"]+hop["target"]["text_sha256"]` (`guo_v5_rescore.py:63`), **not** the engine ops-count hash (`engine.py:111` `sha256("|".join(str(_ops(t))...))`). Even if the engine hash collided on atom-count, `certificate_key` still includes full member text.

**G0014 keys ≠ G0016 keys.** No freeze hop is `G0014→G0012`; ell hops are `G0016→G0014` with a different target SHA256 (`436f5257…` vs G0013 `61476197…`) and `epsilon(ell)`.

Legitimate reuse (not alias): identical Guo kernels cached across family ids (6 keys / 18 hops). That is the same mathematical hop, not G0014 onto G0016.

---

## 4. Family compose holes (latent; do not fire)

`guo_v5_rescore.py:144-162`:

```144:162:research/coefficient_laurent/eval/guo_v5_rescore.py
        covering = [p for p in path_rows if len(p.steps) >= 2] or path_rows
        cons = [CONSISTENCY_UNKNOWN] if len(covering) > 1 else []
        fam_v = compose_family_verdict(
            path_verdicts=[p.path_verdict for p in covering],
            consistency_verdicts=cons,
            reconstruction_verdicts=["ZERO"],
            require_path_independence=bool(cons),
        )
        ...
    report["d2_unlocked"] = n_fz > 0 or report["FAMILY_NONZERO"] > 0
```

`compose_family_verdict` (`research/iterated_confluence/schema.py:188-221`): FAMILY_ZERO requires all covering paths PATH_ZERO, all reconstruction ZERO, and — if `require_path_independence` — all consistency CONSISTENT_ZERO. PATH_ZERO is not FAMILY_ZERO. Majority is forbidden.

### Frozen covering-path counts (`PATH_CANDIDATES.json`)

| family | n_paths | n one-step | n covering (`len(steps)≥2`) | n_path_zero | covering verdicts | cons | family |
|---|---:|---:|---:|---:|---|---|---|
| guo-p2-s0-i3 | 9 | 6 | **3** | 5 | PATH_ZERO + 2×PATH_UNKNOWN | `[UNKNOWN]` | FAMILY_UNKNOWN |
| guo-p2-s1-i2 | 9 | 6 | 3 | 5 | same pattern | `[UNKNOWN]` | FAMILY_UNKNOWN |
| guo-p2-s1-i3 | 9 | 6 | 3 | 5 | `G0023→G0020→G0019` ZERO; ell UNKNOWN | `[UNKNOWN]` | FAMILY_UNKNOWN |
| guo-p2-s2-i2 | 9 | 6 | 3 | 5 | same as s0-i3 | `[UNKNOWN]` | FAMILY_UNKNOWN |
| guo-p2-s2-i3 | 9 | 6 | 3 | 5 | same as s1-i3 | `[UNKNOWN]` | FAMILY_UNKNOWN |
| **guo-p2-s2-i4** | 2 | 2 | **0 → fallback 2** | 2 | two one-step PATH_ZERO, **different ends** | `[UNKNOWN]` | FAMILY_UNKNOWN |
| guo-p2-s4-i1 | 9 | 6 | 3 | 5 | same as s0-i3 | `[UNKNOWN]` | FAMILY_UNKNOWN |

Five PATH_ZERO on the 5-branch families are: three V4 diagonal one-steps (`G0013/14/15→G0012` or analog) + V5 m→n one-step + the two-step `G0016→G0013→G0012` (V5 ZERO + V4 ZERO). Sibling two-steps stay PATH_UNKNOWN because ell-hops timed out. Majority PATH_ZERO ≠ FAMILY_ZERO.

### Hole A — hardcoded reconstruction ZERO

`reconstruction_verdicts=["ZERO"]` is a constant. Actual spectator/reconstruction is not consulted.

Replay (not frozen):

- covering all PATH_ZERO + `CONSISTENT_ZERO` + rec ZERO → **FAMILY_ZERO**
- same + rec UNKNOWN → **FAMILY_UNKNOWN**

So a family with **failed** reconstruction can still FAMILY_ZERO if paths and consistency already pass. **Does not fire:** frozen covering is mixed PATH_UNKNOWN and cons is UNKNOWN. If ell-hops later became ZERO while this line still injects `CONSISTENCY_UNKNOWN`, FAMILY_ZERO would still be blocked by consistency. The hole becomes live if someone also flips consistency to CONSISTENT_ZERO without measuring reconstruction.

### Hole B — single covering skips consistency (V3 R2 hole)

`cons = [CONSISTENCY_UNKNOWN] if len(covering)>1 else []` and `require_path_independence=bool(cons)`.

When `len(covering)==1`: `cons=[]`, `require_path_independence=False`, schema skips consistency. Combined with hardcoded rec ZERO:

```
PATH_ZERO × 1, cons=[], rec=["ZERO"], require_ind=False  →  FAMILY_ZERO
```

That is the V3 R2 skip (single covering PATH_ZERO without path independence). **Does not fire on the 7 frozen families:** covering counts are 3 (5-branch) or 2 (s2-i4 fallback), never 1.

s2-i4: no two-step paths, fallback to two one-step PATH_ZERO (`G0005→G0004` and `G0009→G0008`, different ends). V5 injects `CONSISTENCY_UNKNOWN` because `len(covering)==2`, so FAMILY_UNKNOWN. A V3-style “different-end pair ⇒ skip consistency” would have FAMILY_ZERO here; the **count>1** injection blocks it. That is fail-closed on this artifact, not a proof that Hole B is gone.

### Hole C — `d2_unlocked`

`d2_unlocked = n_fz > 0 or FAMILY_NONZERO > 0` (`guo_v5_rescore.py:162`). Artifact: `FAMILY_ZERO=0`, `FAMILY_NONZERO=0`, `d2_unlocked=false`. Neither clause fired.

---

## 5. Falsifier + generic suite

`falsifier/` + `eval/generic_suite.py`. Required tests passed (see Commands).

| Case | expect | got |
|---|---|---|
| generic `B-full-cancel` | ZERO | ZERO (schema all-ZERO) |
| generic `C-surviving-pole` | NONZERO | NONZERO |
| generic `E-wrong-order` | NONZERO | NONZERO |
| generic `A-atoms-only-not-zero` | UNKNOWN | UNKNOWN |
| falsifier `V5L_01` t^0 + surviving pole | NONZERO | NONZERO LEVEL_B |
| `V5L_02` wrong polygamma order | NONZERO | NONZERO |
| `V5L_03` missing atom | UNKNOWN | UNKNOWN LEVEL_A (`recon=False` beats trap NONZERO) |
| `V5L_04` sign flip | NONZERO | NONZERO |
| `V5L_05` insufficient order | UNKNOWN | UNKNOWN LEVEL_B (`rem≠ZERO`) |
| two positive controls | ZERO LEVEL_C | ZERO LEVEL_C |
| `false_ZERO` | 0 | **0** |

Generic suite feeds **pre-set** slot verdicts into `compose_hop_verdict`; it does not run `sparse_laurent_limit`. Falsifier uses its own remainder (`order_n`, `falsifier/checkers.py:265-270`), not engine auto-ZERO. Toy remainder discipline is stricter than the Guo engine.

1317-op blob: `cancel` is skipped above `CANCEL_OPS_CAP=80` (`c0/match.py:117-119`). Size-guard at `OPS_CAP=800` returns UNKNOWN, not ZERO, **unless** provenance is in `_ZERO_EXEMPT`. Unbounded cancel of a 1317-op blob is not a ZERO path.

---

## 6. `_ZERO_EXEMPT = {pg_atoms, identical}` vs OPS_CAP

`c0/match.py:340-385`. `_by_polygamma_atoms` runs **before** the size-guard (`match.py:67-75`). `_zero` / `_result` then allow ZERO when `ops > OPS_CAP` if provenance is `identical` or `pg_atoms`.

`_group_by_polygamma` expands the full expression and buckets terms with **no** polygamma under key `1`. `_rational_coeffs_equal` may then `expand` / `together` (cap `PAIR_TOGETHER_CAP=4000`) those “coeffs”. So `pg_atoms` is not polygamma-only: it is a pre-guard identity prover with a 4000-op together budget.

Attacks run here (no hop retune):

| Pair | ops | verdict | provenance | False ZERO? |
|---|---:|---|---|---|
| Identical huge `Add(d**i, evaluate=False)` ~1796/side | 3592 | ZERO | identical | No (tree equality) |
| ~1398-op blob vs blob+1 | 2797 | NONZERO | pg_atoms n=1 | No |
| `(d**400-1)/(d-1)` vs `sum d^k` | 801 (>800) | ZERO | pg_atoms n=1 | Algebraically true; **size-guard bypassed** |
| `(x**2-1)/(x-1)` vs `x+1` | 5 | ZERO | pg_atoms | Algebraic identity except at `x=1` |
| `gamma(z+1)` vs `z*gamma(z)` | 4 | UNKNOWN | UNKNOWN | No false ZERO |
| `pg(1,(z**2-1)/(z-1))` vs `pg(1,z+1)` | 7 | NONZERO | pg_atoms n=2 | **Did not** collapse via `_canon_pg` |
| `pg(1, z*(z-1)/(z-1))` vs `pg(1,z)` | 2 | ZERO | **identical** | SymPy parsed the argument to `z` before grouping |
| Uneval vs eval same 700-term poly | 2796 | ZERO | pg_atoms | True same polynomial |
| Huge `F(i)` sum vs +extra | 3600 | NONZERO | pg_atoms | No |

`_canon_pg` (`match.py:196-211`) `expand`+`together`s polygamma arguments; it does **not** `cancel`. `(z**2-1)/(z-1)` stayed a distinct key from `z+1` → NONZERO, not a false ZERO.

Identical huge trees mint ZERO by design (`tests/test_cl_c0.py:53-59`). That is not a false ZERO. The OPS_CAP story is: blob **cancel** cannot ZERO a 1317-op mismatch; **exempt** paths can ZERO true identities above 800 ops. Frozen G0016 C0 match is per-polygamma grouping (VERDICT: full-blob expand of C0−G0013 is not 0). No frozen false ZERO from this exempt.

`grouping/group.py` is not called by `match.py` (separate grouping implementation). Not used in hop ZERO.

---

## 7. `used_full_together` always False

Repo-wide search: **no** `used_full_together = True`.

| Site | Value |
|---|---|
| `schema.LaurentCertificate` default `schema.py:73` | False |
| `engine.sparse_laurent_limit` init `engine.py:101` | False, never updated from `c0_match` |
| `c0.match._result` `match.py:384` | hardcoded False; docstring `match.py:43` |
| Falsifier cert `falsifier/checkers.py:310` | False |
| Frozen ZERO rows | `"together": false` |
| Timeout JSON rows | `"together": null` (key absent on payload) |

A ZERO certificate from this pipeline cannot carry `used_full_together=True`. PASS.

---

## D2

`d2_unlocked` is false in `GUO_V5_RESCORE.json`. FAMILY_ZERO=0, FAMILY_NONZERO=0. Track D2 **LOCKED**. Do not open. Ell-hops remain UNKNOWN. Holes in §4 are latent and must not be “fixed” by weakening consistency or treating majority PATH_ZERO as FAMILY_ZERO.

---

## Commands and results

Worktree: `git worktree add /private/tmp/wt-v5-review-r4 -b work/v5-review-r4 fb3b929`  
HEAD: `fb3b929432b3de024e510835ff6f9fd4700c2ae1` — `Certify G0016 to G0013 at LEVEL C via per-polygamma C0 match.`

```
cd /private/tmp/wt-v5-review-r4
export PYTHONPATH=.
/Users/kawawong/Projects/symbolic-compactification/.venv/bin/python -m pytest \
  tests/test_cl_schema.py tests/test_cl_cache.py tests/test_cl_cache_audit.py \
  tests/test_cl_falsifier.py tests/test_cl_generic.py tests/test_cl_c0.py \
  tests/test_cl_freeze.py -q
```

**60 passed in 1.37s.** Ell-hops (12×40s) were **not** rerun. Frozen `GUO_V5_RESCORE.json` inspected.

Independent compose/cache/family/c0/remainder probes (same interpreter, no writes, no hop rescore): 1372-tuple compose enumeration; V4 alias replay; PATH_CANDIDATES covering counts; `remainder_ok` on 14 primary-hop polygamma units (0 True); `_ZERO_EXEMPT` attacks above.

---

## Bottom line

1. **Hop schema is closed:** only the all-ZERO LEVEL_C tuple is hop ZERO. LEVEL A is not ZERO. Surviving pole + matching t^0 is NONZERO.
2. **LEVEL C remainder is not closed:** engine auto-ZERO remainder; `remainder_ok` is unused and False on the frozen Guo atoms that received LEVEL_C. Treat recorded hop ZERO as **C0+negatives**, not remainder-certified LEVEL C.
3. **Cache identity holds:** full text SHA256 in every key; empty text refused; G0014 cannot alias G0016; ops-count hash collision is not an alias.
4. **Timeout cannot schema-compose to ZERO**; it can first-writer-block a later ZERO on the same key; JSON drops timeout provenance; a reader who defaults null slots to ZERO would mint LEVEL_C.
5. **Family compose still contains the V3 R2 single-covering skip and hardcoded reconstruction ZERO.** Neither fires on the 7 frozen families. Majority PATH_ZERO is not FAMILY_ZERO.
6. **D2 stays locked.**
