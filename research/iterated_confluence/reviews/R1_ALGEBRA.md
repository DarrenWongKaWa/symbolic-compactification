# R1 — algebraic audit of factor / local reduction

Reviewer 1 (symbolic algebra). Isolated worktree `work/v3-review-r1`.
Parent `d977db457da2cd50b2b2a72968e8db3bd21d9405`. No LLM. Frozen
inputs, historical runs, `schema.py`, and SOL were not edited.
Methods were not changed.

Scope: `spectator/split.py`, `edges/certify.py`, the local-complexity
gate, and the I-D close documents. Attacks were run with
`.venv/bin/python` against the frozen Guo members and synthetic
kernels. The 25 s / 90 s five-branch series timeouts were not
re-timed; those remain the frozen rescore facts.

---

## Verdict on I-D

**I-D is correct.** Track D2 stays locked.

The frozen five-branch covering edges are one-parameter graphs of
actual source `G####` members (not I-E). After an *exact* mul-args
`h1` peel they remain 327–567-op polygamma kernels, not the certified
two-member scale (176 full / 172 local). Local confluence of those
hops is UNKNOWN by timeout, so path consistency is never reached
(not I-C). No frozen family is `FAMILY_ZERO` or `FAMILY_NONZERO`.

The only ZERO edges are the reused Track V pairs
`G0005→G0004` and `G0009→G0008` (`guo-p2-s2-i4`), after the same
non-expanding peel (176→172). That is not new family-level V_GAIN.
`PATH_ZERO` on those two one-step paths plus an UNKNOWN substitution
correctly stays `FAMILY_UNKNOWN`.

---

## Is the mul-args peel exact?

**Yes, on the frozen Guo set, as a structural identity `S * K = E`.**

`split_edge` tries, in order: `_mul_undef_peel` (common
`AppliedUndef` factors taken from `Mul.args` by `==`, dropped by
`list.remove`, rebuilt with `Mul(*remaining)`), then Track V
`split_multiplicative`, then `split_additive`. A kernel is returned
only if reconstruction holds and `S` is not `±1` or `0`.

Live recount (34 members, 38 unique covering one-parameter edges):

| check | result |
|---|---|
| Per-member `S * K == expr` (structural, not cancel) | **34 / 34** |
| Cancel/expand-only reconstruction | **0** |
| `LOCAL_COMPLEXITY.json` full/local ops | **exact match** |
| Pair `split_edge` certified | **38 / 38** |
| Pair note | all `exact_applied_undef_mul_args` |
| Pair `S * A_local == A` and `S * B_local == B` | **38 / 38** |
| Nested `h1`/`h2` left inside the kernel | **0** |
| `epsilon(*)` as a top-level Mul `AppliedUndef` | **0** |
| `S` depends on the degeneration `epsilon(var)` | **0** |

Five-branch spectator is `h1(a,m,n)*h1(b,ell,m)*h1(c,n,ell)` (or the
s1-i3 / s2-i3 index permutation). Two-member spectator is
`h1*h2` (`h1(b,n,m)*h2(a,c,m,n)` and the G0008/G0009 swap). Pair `S`
equals the intersection of the two members’ top-level undefs.

The remaining kernel is still a `Mul` whose non-`h1` factors include
the confluence pole as a `Pow`, e.g. `(epsilon(m)-epsilon(n))**(-3)`
on G0005 and `(-epsilon(ell)+epsilon(n))**(-4)` on G0013. Those Pows
are *not* `AppliedUndef`, so they are correctly left in the local
kernel. That is why the peel removes only ~4 ops (two-member) or ~6
ops (three `h1`s): `count_ops(h1(a,m,n))=1`, product of three `h1`s
is 5 ops. It does not touch the polygamma sum.

`_drop_mul_factors` returns `None` if a claimed factor is missing,
and `_mul_undef_peel` then reports `reconstruction_failed` rather
than a partial drop. Multiplicity is matched one-for-one against
`Mul.args` (a second identical `h1` on only one side stays in that
side’s local kernel). Commutative reordering of `h1*h2*K` reconstructs
with `==`.

The local-complexity gate (`eval/local_complexity.py`) peels *all*
top-level undefs of a single member; `split_edge` peels the *common*
undefs of a pair. On these frozen families those sets coincide, so
the published 172 / 327 / 567 numbers are the proving kernels, not
an optimistic per-member over-peel.

**Exactness caveats (fail-closed, not false ZERO):**

- `h1**2` is a `Pow`, so mul-args does not peel it.
- Reconstruction *may* fall through to `cancel` / `together`
  (`_exact_eq`) when `==` fails. On frozen Guo it never needed that
  backup. On `Mul(h1(x), x+x, evaluate=False)` it accepts via cancel
  (`x+x` vs `2x`). That is a polynomial identity, not a Guo hole.
- `split_edge` does not know the limit variable (see false-ZERO
  section). That is independent of whether `S * K = E` holds.

---

## Is cancel-expansion rejection right?

**Yes. It is required for both the complexity claim and the meaning
of “local kernel.”**

Track V `_peel_applied_undef` walks `expr.atoms(AppliedUndef)` and
divides with `cancel(rest / atom)`. That is not a Mul-arg peel:

On `G0005 / G0004` (15 s budget, succeeded):

| | mul-args (V3) | Track V cancel-peel |
|---|---|---|
| `S` | `h1(b,n,m)*h2(a,c,m,n)` | `epsilon(n)*h1(b,n,m)*h2(a,c,m,n)` |
| G0005 local ops | 172 | **1355** |
| G0004 local ops | 83 | 140 |
| `S * local == original` | True | **False** |
| `cancel(S*local - original)==0` | True | True |
| `expansion_not_reduction` | no | **would fire** (Δops +1232) |

One-sided `_peel_applied_undef(G0005)` is worse: `S` becomes
`epsilon(m)*epsilon(n)*h1*h2` (rest 1364 ops). That peels the
*degeneration parameter itself*. The pair-common `S` drops
`epsilon(m)` only because G0004 no longer contains it; it still
steals `epsilon(n)` from inside the kernel, not from `Mul.args`.

On `G0013 / G0012` and `G0016 / G0013`, Track V `cancel` **timed out
at 15 s**. Mul-args finished immediately with structural
reconstruction and locals 327 / 567.

So the coordinator rule “reject splits with `local_ops > full_ops`”
is right:

1. 176→1355 is not a reduction toward the certified two-member
   scale; it is the opposite.
2. The expanded kernel is not structurally `E / (h1 h2)`. It is a
   cancel-identity that also divided out `epsilon(n)`. Calling that
   object the “local kernel” would change the scientific claim.
3. V3 tries mul-args *first*, so the expanding Track V path is never
   used on the frozen covering edges.

When cancel-peel *does* reduce ops (synthetic: `h1` distributed into
an `Add`), V3 still accepts Track V `exact_applied_undef_factor`.
That is a different syntactic shape from Guo, where `h1`/`h2` are
top-level Mul factors. The rejection is of *expansion*, not of
Track V factoring as such.

`h1(x)**2 * (x+1)` vs `h1(x)**2 * (y+2)`: mul-args refuses (Pow);
Track V peels one `h1` and expands the rest; V3 then rejects with
`expansion_not_reduction` and returns no proving kernel. Fail
closed.

Cubic Newton `(x**3-y**3)/(x-y)` vs `3x**2` has no multiplicative
spectator. Additive Track V offers `S=x**2` and *increases* ops
(5+2 → 7+2); V3 discards it (`note=expansion_not_reduction`,
`certified=False`). No proving kernel, originals kept. Harmless.

---

## False ZERO risk

### Frozen Guo iterated rescore: **no false ZERO from this peel**

Reasons, all checked on the actual members:

- Reconstruction on covering edges is structural `==`, so
  `source = S * A_local` and `target = S * B_local` as expressions.
- `S` is `h1`/`h2` of discrete indices `{a,b,c,m,n,ell}`, not
  `epsilon(*)`.
- G0004 / G0008 (limit targets) do not contain `epsilon(m)`, the
  degeneration parameter of those ZERO edges.
- After peel the pole `(ε_i-ε_j)**(-k)` remains in the kernel, so
  the peel does not secretly cancel the confluence denominator.
- `certify_one_parameter` sanitizes timeout / size-guard / parse
  provenances: they cannot become ZERO (`_BLOCKED_ZERO`, `_sanitize`).
- Hidden pole with a true spectator: `h1(x)/(x-y)` vs `0` as `y→x`
  is **NONZERO** (valuation), not ZERO.
- Independent `h1` with a *wrong* finite target is **NONZERO**.
- Independent `h1` on cubic Newton is ZERO, and the unsplit pair
  is the same ZERO (together_cancel). Consistent, not a promotion.

The two frozen ZERO edges are the already-certified Track V series
certificates run on the *same* 172-op kernels after a non-expanding
peel. I confirmed the peel and ops; I did not re-run the ~13 s
series.

### Method hole, **not** exercised on frozen Guo — report loudly

`split_edge` never sees `variable`. A common factor that *depends
on the degeneration parameter* is treated as a spectator. Then
`certify_one_parameter` proves `lim A_local = B_local` and returns
that as the edge verdict. That is not equivalent to
`lim (S A_local) = S B_local` when `S` still depends on the dummy
and the target still carries `S`.

**Attack (polynomial gcd, Track V path after mul-args finds nothing):**

```
lim_{y→0}  y*(y+3)  =?  3y
```

- Unsplit `check_limit`: **NONZERO** (substitution `0` vs `3y`).
- `split_edge` certifies `S=y`, locals `y+3` and `3`
  (`note=exact_common_factor`).
- Local `check_limit`: **ZERO**.
- `certify_one_parameter`: **ZERO**. **False ZERO of the stated
  contract.**

**Attack (mul-args `AppliedUndef` depending on the dummy):**

```
lim_{y→0}  h1(y)*(y+3)  =?  h1(y)*3
```

- Unsplit: UNKNOWN.
- Mul-args `S=h1(y)`, locals `y+3` and `3`.
- `certify_one_parameter`: **ZERO**. False ZERO relative to the
  unsplit claim.

This is a soundness bug in the *local-reduction contract*, not a
bug in `S * K = E`. I am **not** patching it here (no method
change, no papering over). It does **not** fire on the frozen Guo
families, whose spectators are discrete `h1`/`h2` independent of
`epsilon`. Any later peel of polynomial or `epsilon(*)` spectators
must refuse `S` that depend on the degeneration parameter.

### Fail-closed traps (not false ZERO)

- `gcd(A, 0) = A`: `lim_{y→0} y(y+3) = 0` is a true ZERO unsplit,
  but `certify_one_parameter` returned NONZERO after treating the
  whole vanishing product as `S`. Completeness loss, fail-closed
  for ZERO.
- `count_ops` in `split.py` fail-closes to 0; in `certify.py` it
  fail-closes to `OPS_CAP+1`. If `count_ops` threw, expansion
  rejection could be skipped. Did not throw on Guo.
- If `split_edge` failed to import, `certify.py` would call Track V
  `split_multiplicative` directly and could accept the 1355-op
  cancel peel. In this freeze `split_edge` is present and wins.

Timeout rows in `GUO_ITERATED_RESCORE.json` show
`split_certified: false` and null ops because the 25 s process
wrapper discards the inner certificate. Split itself succeeds in
milliseconds on those hops. That is a reporting artifact, not
evidence that peel failed.

---

## Attacks tried

1. Structural `S*K == E` on every frozen member (34).
2. Pair `split_edge` on every covering one-parameter edge (38),
   including `S` vs `epsilon(var)` and pair-`S` vs intersection of
   per-member undefs.
3. Track V `cancel` peel vs mul-args on G0005/G0004, G0009/G0008
   (succeeded), G0013/G0012 and G0016/G0013 (15 s timeout).
4. One-sided factor; units; partial extra `h1`; commutative
   reorder; missing `list.remove` factor; `evaluate=False` `x+x`.
5. `h1**2` (Pow) vs Track V cancel-peel + expansion gate.
6. `h1` distributed into an `Add` (mul-args refuses; Track V
   cancel-peel reduces ops and is accepted).
7. Fake expanded kernel and fake reconstruction (`_try_mode`
   rejects).
8. Unevaluated `(x-y)*1/(x-y)` vs `(x-y)*0` (no false spectator).
9. Cubic Newton: no multiplicative spectator; expanding additive
   `S=x**2` rejected.
10. Hidden pole with spectator → NONZERO.
11. Independent `h1` Newton → ZERO; independent `h1` wrong target
    → NONZERO.
12. **False ZERO:** `S = y` on `y*(y+3)` vs `3y` as `y→0`.
13. **False ZERO:** `S = h1(y)` on `h1(y)*(y+3)` vs `h1(y)*3`.
14. `epsilon(a)` as an independent top-level undef (would peel;
    does not occur on Guo members).
15. G0005/G0004 live split: 176→172, `S` has no `epsilon(m)`,
    structural reconstruction, pole stays in `K`.

No attack produced a false ZERO *on frozen Guo*. Two synthetic
attacks produced false ZERO of `certify_one_parameter` when `S`
depends on the limit variable.

---

## Local complexity vs the 176-op certificate

Confirmed live, matching `LOCAL_COMPLEXITY.md`:

| class | full | local after mul-args | vs 176 |
|---|---:|---:|---:|
| 2-member generic (G0005/G0009) | 176 | 172 | 0.98 |
| 5-branch diagonal (G0013-class) | 333 | 327 | 1.86 |
| 5-branch generic (G0016-class) | 573 | 567 | 3.22 |
| 5-branch triple (G0012-class) | 33 | 27 | 0.15 |

`decomposition_to_176_scale` is False. The 327-op diagonal→triple
hop is the honest “small” five-branch edge; it is still ~1.86× the
certified pair. Spectator peel cannot make the Track V cascade
decide it.

---

## I-D, D2, publication

Agree with `VERDICT.md` / `CAPABILITY_BOUNDARY.md` / `TRACK_V3_CLOSED.md`:

- Case **I-D**, not I-C, not I-E, not I-A/B.
- Track D2 **LOCKED**.
- Publication **E**.
- `STOP_VERIFICATION_LINE` for iterated-path V3 increments is the
  right research decision: a longer `sympy.series` timeout is not
  the missing object. The missing object is a generic polygamma /
  repeated-argument local prover that can decide the 327-op hop
  without Guo tables.

Do not treat the method hole in var-dependent spectators as a
reason to reopen D2. It is a contract defect for a class of peels
this freeze does not perform. Do not patch it by weakening
reconstruction, by accepting cancel-expansion, or by converting
timeout to ZERO.
