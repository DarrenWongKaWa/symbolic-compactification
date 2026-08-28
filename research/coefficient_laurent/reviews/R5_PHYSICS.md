# Reviewer 5 — theoretical physics (Track V5)

Isolated review. No LLM. No hop retune. No D2 unlock. Frozen
authorities unread as writable. Charge: is G0016→G0013 an edge
identity of the original Guo energy kernel, or a family certificate
/ new physics theorem?

**Physics verdict.** Edge identity of one pairwise coincidence
(`m→n`) on one 3-index orientation of Guo `Σ_abc`. Not a family
certificate. Not a new energy identity. Publication letter **E**
only. Track D2 remains **LOCKED**.

The close (`TRACK_V5_CLOSED.md`, `VERDICT.md` §13, `STATUS.md`)
already writes **edge V_GAIN**, not family V_GAIN. This review
affirms that cut and attacks any reading that upgrades it.

---

## 0. What was reviewed

| artifact | role |
|---|---|
| `examples/long/Guo_Sigma_abc_dc_exact.txt` | raw scientific source (SHA-256 `63742cc4…652afc44`) |
| `examples/long/SOURCE.md`, `symbols.json` | provenance; `beta,gamma,mu` real; `h1,h2,epsilon` |
| `research/scalable_verification/guo_map/GUO_OBLIGATION_MAP.json` | full `node.text` of G0012–G0016 / G0019–G0023 |
| `research/obligation_ir/source_index.py`, `GROUNDING.md` | GID walk; `epsilon(m)→epsilon(n)` ≡ `Eq(m,n)` |
| `research/coefficient_laurent/FROZEN_INPUTS_V5.json` | primary hop `guo-p2-s0-i3:G0016->G0013` |
| `research/coefficient_laurent/{PROTOCOL,TRACK_V5_CLOSED,VERDICT,STATUS,GUO_V5_RESCORE}.md` | close, V_GAIN accounting |
| `research/coefficient_laurent/atoms/ATOM_MAP.json` | spectator peel, 14 polygamma atoms |
| `research/coefficient_laurent/engine.py` | remainder shortcut |
| `research/coefficient_laurent/remainder/{sufficiency.py,README.md}` | independent remainder contract |
| `research/coefficient_laurent/literature/CLASSIFICATION.md` | method labels (written pre-rescore) |
| `research/polygamma_confluence/{GUO_HOP_RESCORE.md,TRACK_V4_CLOSED.md,VERDICT.md}` | V4 diagonal→triple ZERO |
| `research/PROGRAM_STATUS_V5.md` | stale L-D snapshot |
| `research/PUBLICATION_DECISION.md` | letter E, no `paper/` |

Ell-hops were not rerun. Algebraic C0 / negative-coefficient
bookkeeping is not re-adjudicated here. Physics asks what object
was certified, under what domain, and whether that object is a
family or a theorem.

---

## 1. G0016 and G0013 are original scientific branches

**Yes.** They are source-index `piecewise_branch` members of the
original 5-branch 3-index summand, not aliases and not 220-character
catalog truncations.

### 1.1 Source tensor

`CompleteDCSigmaABC` is an `Add` of **four** Matsubara / band sums
(`examples/long/Guo_Sigma_abc_dc_exact.txt` header: Guo Appendix A
(A-3)–(A-12), B (B-1)–(B-6); exact finite `Gamma`; explicit
removable-limit branches). Structure:

| sum | dummies | Piecewise | spectators (Wolfram order) |
|---|---|---|---|
| 1 | `(n,m)` | 2 (`n==m`, default) | `h1[c,n,m] h2[a,b,m,n]` |
| 2 | `(n,m)` | 2 | `h1[b,n,m] h2[a,c,m,n]` |
| 3 | `(n,m,ell)` | 5 | `h1[a,m,n] h1[b,n,ell] h1[c,ell,m]` |
| 4 | `(n,m,ell)` | 5 | `h1[a,m,n] h1[b,ell,m] h1[c,n,ell]` |

GID numbering follows `source_index.build_index` /
`Add.make_args`, not file order. The frozen primary family is the
5-branch Piecewise whose spectator is
`h1(a,m,n)*h1(b,ell,m)*h1(c,n,ell)` — Wolfram sum 4. The other
3-index orientation is G0019–G0023.

Wolfram first-match conditions of that Piecewise:

```
n == m && m == ell     # triple
n == m                 # m identified with n, ell generic
n == ell               # ell identified with n, m generic
m == ell               # ell identified with m, n generic
<default>              # all three indices distinct
```

That is the exclusive partition lattice of three dummy indices.
No extra branch; no missing pairwise.

### 1.2 Frozen members vs source

`GUO_OBLIGATION_MAP.json` hypothesis `seed=0,index=3` (and the
identical member texts on `s1-i2`, `s2-i2`, `s4-i1`):

| member | cond | ops | text_len | parent | parent_sum | role |
|---|---|---:|---:|---|---|---|
| G0012 | `And(Eq(ell,m), Eq(m,n))` | 33 | 191 | G0011 | G0010 | triple |
| G0013 | `Eq(m,n)` | 333 | 1865 | G0011 | G0010 | diagonal `m=n` |
| G0014 | `Eq(ell,n)` | 379 | 2090 | G0011 | G0010 | diagonal `ell=n` |
| G0015 | `Eq(ell,m)` | 379 | 2043 | G0011 | G0010 | diagonal `ell=m` |
| G0016 | `True` | 573 | 3152 | G0011 | G0010 | generic |

`FROZEN_INPUTS_V5.json` primary hop records the same conds, parents,
ops, and full-text SHA-256:

- G0016 `text_sha256 = aaa1debec01b7e81…ab716688` (len 3152)
- G0013 `text_sha256 = 61476197f7c78efe…d833f9c7` (len 1865)

Independent rehash of map `node.text` matches those prefixes.
`in_index: true`. Kind `piecewise_branch`. Shared parent G0011
(the Piecewise) and parent sum G0010 (the `Sum`). Degeneration
on the primary hop is `epsilon(m) → epsilon(n)`, which
`obligation_ir/GROUNDING.md` declares as the source synonym of
the `Eq(m,n)` Piecewise condition (conditions are on indices;
`epsilon` is the energy coordinate of that index).

G0016 generic text is the source default branch: 14 polygamma
atoms (orders 0,1,2) in `ε(m),ε(n),ε(ell)` with overall
`h1…h1…h1 / π^3`. G0013 text is the source `n==m` branch:
polygamma 0,1,2 in the remaining pair `(ell,n)`, overall
`h1…h1…h1 / (16 π^3 (ε(n)-ε(ell))^4)`. Both are already written
by Guo as regularized limits. The hop asks whether the generic
branch, taken as `ε(m)→ε(n)`, recovers the author’s own diagonal
formula. That is a consistency check of a removable-limit
construction, not a newly proposed energy identity.

### 1.3 Not catalog truncations, not aliases

Historical 220-character catalog texts caused false
`COMPILE_FAILURE` (`research/representation_invention/VERDICT.md`
§9; `grounded_proposer/catalog.py` `text_cap: 220`). G0013 and
G0016 are far above that cap (1865, 3152). G0012 (191) would have
survived the cap; the generic and `m=n` branches would not.

`tests/test_sv_guo_map.py::test_local_texts_are_full_node_text_not_catalog_cap`
and `guo_map/README.md` require the obligation map to attach full
`node.text`, not the 220-cap catalog. The freeze hashes those full
texts. Cache keys include source/target full-text hashes
(`PROTOCOL.md`); G0014 cannot alias G0016.

Aliases are a different failure mode (`PARSE_FAILURE` in
representation-invention). These members are exact-bound source
nodes.

**Q1 answer:** G0016 and G0013 are the original generic and
`m=n` scientific branches of one 3-index Guo summand.

---

## 2. Spectators: remaining kernel is still the energy integrand

`ATOM_MAP.json` primary hop:

```
spectator = h1(a, m, n)*h1(b, ell, m)*h1(c, n, ell)
pref      = h1(a, m, n)*h1(b, ell, m)*h1(c, n, ell)/pi**3
n_atoms   = 14 POLYGAMMA
split     = exact_applied_undef_mul_args
reconstruction_ok = true
```

`h1` is `AppliedUndef` of discrete indices `(a,m,n)`, `(b,ell,m)`,
`(c,n,ell)`. It does **not** depend on the degeneration coordinate
`epsilon(m)`. `split_edge` therefore peels it (`spectator_depends_on_degeneration`
does not fire). Units and zero are not spectators; reconstruction
`S * A_local == A` is required.

Physically `h1` is a discrete mode-overlap / hopping amplitude.
It labels which spatial/mode matrix element multiplies the
summand. It is not the energy kernel. The overall `π^{-3}` is
the source generic branch’s Fourier / thermal normalization
(Wolfram default ends `/Pi^3`).

After peel, the remaining object is

```
π^{-3} × (14-term rational × polygamma sum in ε(m), ε(n), ε(ell), β, γ, μ).
```

That **is** the energy integrand of this summand — the special-function
kernel whose removable singularities Guo wrote as explicit Piecewise
branches. It is not a different physics object (not a current, not a
form factor, not a reduced matrix element of a new operator). The
confluence lives entirely in that kernel: poles in
`(ε(m)-ε(n)), (ε(ell)-ε(m)), (ε(ell)-ε(n))` regularized to diagonal
and triple formulae.

G0013’s extra `1/16` and `1/(ε(ell)-ε(n))^4` are **not** spectators;
they belong to the diagonal energy formula and must be matched by
`t^0`. The hop compares peeled generic C0 to peeled G0013. Same
physics object, two branches.

---

## 3. `m→n` is not `ell→n` or `ell→m`; edge ≠ family

These are three distinct coincidences of external dummy indices
on a kernel that is **not** S3-symmetric.

| hop | degeneration | source cond → target cond | ops | V5 |
|---|---|---|---:|---|
| G0016→G0013 | `ε(m)→ε(n)` | `True` → `Eq(m,n)` | 573→333 | LEVEL_C ZERO |
| G0016→G0014 | `ε(ell)→ε(n)` | `True` → `Eq(ell,n)` | 573→379 | UNKNOWN (40s timeout) |
| G0016→G0015 | `ε(ell)→ε(m)` | `True` → `Eq(ell,m)` | 573→379 | UNKNOWN (timeout) |

Evidence they are different physical limits, not a relabeling:

- Target ops 333 vs 379 vs 379.
- G0013 (after `m=n`) still depends on the pair `(ell,n)` and
  uses polygamma orders 0,1,2. G0014/G0015 use orders 0,1,2,**3**.
- Spectator `h1(a,m,n)` is tied to the pair `(m,n)`. Coalescing
  that pair is not the same as coalescing `(ell,n)` or `(ell,m)`
  in the cyclic product `h1(a,m,n) h1(b,ell,m) h1(c,n,ell)`.
- Covering path through `m=n` then `ell=n` is
  `G0016→G0013→G0012`. Sibling coverings
  `G0016→G0014→G0012` and `G0016→G0015→G0012` need the uncertified
  ell-hops.

V4 already certified **diagonal→triple** on this family
(`research/polygamma_confluence/GUO_HOP_RESCORE.json`):
G0013→G0012, G0014→G0012, G0015→G0012 all `ZERO` by
`atom_series:t0`. So `G0016→G0013→G0012` is a composite of
V5 generic→diagonal `m→n` plus V4 `G0013→G0012`. `VERDICT.md`
§10 may call that covering path `PATH_ZERO`. That is **one
path on the Hasse diagram**, not path-independence.

`PROTOCOL.md`: new edge verdicts are V_GAIN only; path
consistency is not auto-`CONSISTENT_ZERO`.
`eval/guo_v5_rescore.py` forces `CONSISTENCY_UNKNOWN` when more
than one covering path exists. Result in `GUO_V5_RESCORE.json`:

```
FAMILY_ZERO = 0
FAMILY_NONZERO = 0
FAMILY_UNKNOWN = 7
d2_unlocked = false
```

`guo-p2-s0-i3` reports `n_path_zero: 5` and still
`FAMILY_UNKNOWN`. The other five 5-member families are the same
cut on the same two 3-index orientations, repeated across
proposer seeds — not five independent tensors.

The six V5 ZERO edges are four cached copies of G0016→G0013
plus two copies of the sibling-orientation analog G0023→G0020
(`h1(a,m,n)*h1(b,n,ell)*h1(c,ell,m)`). That is **two physical
`m→n` hops** (two spectator orientations of `Σ_abc`), not six
theorems and not a family.

**Docs that correctly refuse family upgrade**

- `TRACK_V5_CLOSED.md`: “This is **edge V_GAIN**, not family V_GAIN.”
- `VERDICT.md` §11–§13, §19: no family ZERO/NONZERO; edge V_GAIN;
  publication **E**.
- `PROTOCOL.md`: V_GAIN only; D2 locked until FAMILY_ZERO/NONZERO.
- `STATUS.md`: “closed (CASE L-A edge; family UNKNOWN)”.
- Literature HANDOFF: “Even a later hop ZERO is V_GAIN only.”

**No V5 close document claims the family is solved.** A reader
who quotes `VERDICT.md` §10 `PATH_ZERO` without §11
(`FAMILY_ZERO`: No) would overclaim. Physics forbids that quote.

G2/G3 of representation-invention are not this result. One
certified edge of an already-written Piecewise is not
formalization of a latent master and is not a compile-level
discovery.

---

## 4. Literature honesty: engineering, not a new physics identity

`literature/CLASSIFICATION.md` (audit 2026-08-28, companion
`METHODS.md`) labels:

| method | mathematics | Track-V5 use |
|---|---|---|
| Laurent series | known standard (Laurent 1843; Ahlfors) | known standard |
| sparse Laurent / poly coeff maps | known standard (Geddes–Czapor–Labahn; FORM) | known standard |
| polygamma Taylor | known standard (DLMF 5.15) | known standard |
| residues / `[t^k]` | known standard | known standard |
| removable singularities | known standard (Riemann) | known standard |
| linearity of coefficients, LEVEL A/B/C, full-text cache | known standard math | engineering adaptation |
| packaged coefficient-space routing of G0016→G0013 | — | **GAP** |

The GAP cell is **stale relative to L-A**, not an overclaim.
It was written at freeze `7102e8a` / V4 J-C, when G0016→G0013
was still `UNKNOWN` (“That experiment has not run”). The pack
already states the only honest remainder *if* the hop later
returns LEVEL_C ZERO:

> coefficient-space routing at scientific-expression scale
> (verification-engineering, not mathematics).

That sentence is still the honest claim after L-A. Sparse
Laurent and polygamma Taylor did not become theorems because
a 573-op kernel now routes. Track V4’s one-pager already banned
“we introduce polygamma confluence.” Guo already wrote both
branches. The engine checks that the author’s generic germ
matches the author’s diagonal germ.

`research/PROGRAM_STATUS_V5.md` is **more stale** (CASE L-D;
18/18 UNKNOWN; no LEVEL C). It must not be quoted as live
status, and it must not be “fixed” into a family win. Live
close is `TRACK_V5_CLOSED.md` / `VERDICT.md` / `STATUS.md` at
L-A, family UNKNOWN, publication E.

What a knowledgeable physicist would reject immediately (aligned
with the classification table, now that the hop exists):

- “We discovered a new Guo / polygamma energy identity.”
  Guo wrote the branches; the hop is confluence of those texts.
- “Sparse Laurent / polygamma Taylor is the contribution.”
  Textbook.
- “The Guo family is solved.” Ell-hops UNKNOWN; 7/7
  FAMILY_UNKNOWN.
- “Hop ZERO unlocks D2 / Hermite proposer.” Protocol forbids it.
- “Hartogs certifies G0016→G0013.” Several-complex-variables
  holomorphy is the wrong object for real Piecewise polygamma
  (classification already).

**Q4 answer:** after L-A the honest remainder is engineering —
coefficient-space routing at scientific-expression scale — not
a new physics identity. The GAP row is stale vs the rescore;
staleness is not family overclaim.

---

## 5. Engine remainder is a Guo-domain shortcut, not a certified remainder

`remainder/sufficiency.py` contract: series through `t^0` is
enough only if the affine polygamma argument `z(t)=α+βt` has
`α` certified **not** a nonpositive integer. Symbolic `α` is
`UNKNOWN`. `remainder_ok is False` ⇒ remainder verdict UNKNOWN,
never NONZERO. `engine.py` does **not** import or call this
package.

Instead (`engine.py` after C0 match):

```
# Affine polygamma arguments at t=0 are not nonpositive integers
# for the frozen Guo kernels (energy arguments ~ 1/2 + i E). Remainder
# is ZERO only when negatives and reconstruction succeeded; else UNKNOWN.
rem = ZERO if (recon and neg == ZERO) else UNKNOWN
```

That is a Guo-only remainder shortcut smuggled into LEVEL C.

Independent check on the 14 primary-hop atoms in `ATOM_MAP.json`:
`remainder_ok(argument, t)` is **False for 14/14**. Every
argument is of the source form

```
z_{±,k} = [π + β(γ ± iμ ∓ i ε(k))] / (2π)
        = 1/2 + β(γ ± i(μ − ε(k))) / (2π),
```

`k ∈ {m,n,ell}`. `α` carries free symbols `{beta, gamma, mu, epsilon(*)}`.
The remainder module therefore refuses. LEVEL C in the rescore
does not rest on that module.

### Physical reading of the slogan `1/2 + i E`

This *is* the standard finite-temperature / Matsubara digamma
argument (`β` inverse temperature, `γ` a real gap/energy-like
parameter, `μ` chemical-potential-like, `ε(k)` a mode energy).
Polygamma poles sit at `z ∈ {0,−1,−2,…}`. Extra polar terms at
`t=0` would require `Im z(0)=0` and `Re z(0) ∈ ℤ_≤0`.

For generic `β≠0` and `μ ≠ ε(k)`, `Im z ≠ 0` and the argument
is off the polar lattice. If the imaginary part vanishes, 
`Re z = 1/2 + βγ/(2π)`, which is a nonpositive integer only on
a discrete real locus in `(β,γ)`. That is a **physical domain**
(typical thermal CFT/QFT: `β>0`, `γ` such that `Re z > 1/2`),
not an algebraic remainder identity, and not independently
certified for these kernels.

`examples/long/symbols.json` declares `beta, gamma, mu` merely
`real`. It does **not** impose `β>0`, `γ>0`, or `μ ≠ ε`. The
engine comment therefore inserts a Guo-regime assumption that
the remainder package was written to refuse.

Physics review **rejects** this shortcut as a remainder
certificate:

- It is not `remainder_ok`.
- It is not a new reflection / multiplication identity of
  polygamma.
- It is not licensed by a domain clause in the freeze.
- Selling it as LEVEL C remainder ZERO is a Guo-specific
  promotion the track’s own remainder agent forbade.

This review does **not** retune the hop and does not convert
the algebraic C0 / negative-coefficient work into NONZERO.
Those are germ identities of rational×polygamma summands
under sympy series, owned by algebra/verification. Physics
says: do not read LEVEL C as an independently certified
remainder theorem for the Guo energy kernel; do not package
`1/2 + i E` as a ZERO rule.

If the remainder contract were enforced, the honest ceiling
on this hop would be LEVEL B (negatives vanished, C0 matched,
remainder UNKNOWN). The published close is LEVEL C. That
gap is a physics objection to the letter of LEVEL C, not a
license to claim a family or a new identity.

---

## 6. Publication boundary: E only; D2 locked; no paper directory

The slogan

> Compositional symbolic proof decomposition converts otherwise
> undecidable scientific-scale confluence claims into small
> exact certificates

needs **more than one Guo family**, and more than one edge of
that family.

What exists:

- One scientific source (`Σ_abc` exact DC).
- Two spectator orientations of the **same** 3-index tensor
  (G0016-family and G0023-family), plus 2-index sums that were
  not the V5 primary object.
- One pairwise coincidence class (`m→n` generic→diagonal)
  certified; ell-hops UNKNOWN.
- One covering path composable with V4 diagonal→triple.
- 7/7 families `FAMILY_UNKNOWN`.
- Remainder not independently certified (`§5`).
- Methods: known standard + engineering routing (`§4`).
- Not G2/G3. Not a master-function discovery. Not Φ_Γ / L4–L7.

That is a stronger *edge-level engineering* exhibit than V4 J-C
(generic hop no longer UNKNOWN on `m→n`). It is not a method
paper, not a family certificate, and not a physics identity
paper. `VERDICT.md` §19 letter **E** is the only honest letter.
`research/PUBLICATION_DECISION.md` is E and forbids a `paper/`
directory; this review does not create one.

Track D2 stays **LOCKED** (`PROTOCOL.md`, `TRACK_V5_CLOSED.md`,
`VERDICT.md` §12, `STATUS.md`, `GUO_V5_RESCORE.json`
`d2_unlocked=false`, `PROGRAM_STATUS_V5.md`). One edge is not
`FAMILY_ZERO`. Do not start a Hermite proposer. Do not retune
ell-hops as a substitute for a family.

---

## 7. Attacks the close already survives, and one it does not

| attack | result |
|---|---|
| G0016/G0013 are catalog aliases | **fails** — full source branches, hashes match freeze |
| peeled kernel is a different physics object | **fails** — energy integrand times discrete `h1` |
| `m→n` certifies ell-hops / the family | **fails** — close already says edge V_GAIN; ell UNKNOWN; 7/7 FAMILY_UNKNOWN |
| literature pack overclaims a theorem | **fails** — GAP is stale, not an overclaim; honest remainder is engineering |
| `1/2 + i E` remainder is independently certified | **hits** — `remainder_ok` 0/14; engine bypasses V5-G |
| publication A/B/C, or D2 open | **fails** — E and LOCKED are the only honest status |
| compositional decomposition as a general theorem | **hits as overclaim** if sold from one Guo edge |

---

## 8. Physics verdict (binding)

1. **Edge, not family.** G0016→G0013 is a LEVEL_C-labelled
   algebraic confluence of Guo’s own generic and `m=n` energy
   branches (edge V_GAIN). Sibling ell-hops UNKNOWN. Families
   7/7 FAMILY_UNKNOWN. Covering path `G0016→G0013→G0012` is at
   most one PATH_ZERO, not path-independence.
2. **Spectator peel is legitimate.** Remaining kernel is
   `π^{-3}` × polygamma energy integrand, not a new object.
3. **`m→n` ≠ `ell→n` ≠ `ell→m`.** Distinct coincidences of a
   non-symmetric 3-index kernel. Do not cite the edge as a
   family certificate.
4. **No new physics identity.** Honest remainder after L-A:
   coefficient-space routing at scientific-expression scale.
   Literature GAP cell is stale vs the rescore; it is not an
   overclaim of a theorem.
5. **Remainder shortcut rejected.** `engine.py` “energy
   arguments ~ 1/2 + i E” is a Guo-domain assumption, not
   `remainder_ok`. Physics will not treat it as a remainder
   theorem. Do not retune; do not silently keep it as a
   general ZERO rule.
6. **Publication E. D2 LOCKED.** One Guo edge is not enough
   for the compositional-proof slogan as a general claim.
   No paper directory. No Hermite. No gold leakage.

Independent. No LLM. No frozen-authority edits.
