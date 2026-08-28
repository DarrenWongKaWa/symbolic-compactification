# Reviewer 3 — theoretical physics (Track V3)

Charge: attack whether the frozen Eq / And lattice and
`epsilon(m) -> epsilon(n)` operators reflect the original scientific
expression `examples/long/Guo_Sigma_abc_dc_exact.txt` (Guo Σ_abc exact
DC), without using gold names as proposer targets. Question: any
mismatch that would make the iterated decomposition **I-E**
(invalid under source semantics)?

Read: `FROZEN_INPUTS_V3.json` (conds, ops),
`paths/PATH_CANDIDATES.json`, `coordinates/DEGENERACY_COORDINATES.json`,
`GUO_ITERATED_RESCORE.md`. Source SHA-256
`63742cc4e6bf401dd48e258ecb86676b0d7570cc075cae38b91dc188652afc44`.
No method edits. No LLM. No Φ_Γ / L4–L7 targets.

**Verdict: I-E does not hold.** The 5-branch covering is the Hasse
diagram of the source 3-index Piecewise. Case remains **I-D**.

---

## 1. What the source actually is

`CompleteDCSigmaABC` is an `Add` of **four** Matsubara / band sums,
not one kernel:

| sum | limits | Piecewise | branches | spectators |
|---|---|---:|---:|---|
| 1 | `(n,1,Nb),(m,1,Nb)` | 2 | `n == m`, default | `h1(b,n,m) h2(a,c,m,n)` |
| 2 | same | 2 | `n == m`, default | `h1(c,n,m) h2(a,b,m,n)` |
| 3 | `+ (ell,1,Nb)` | 5 | see below | `h1(a,m,n) h1(b,ell,m) h1(c,n,ell)` |
| 4 | same | 5 | same conds | `h1(a,m,n) h1(b,n,ell) h1(c,ell,m)` |

`structure_summary`: 4 sums, 4 Piecewise, **14 branches**, ops 3911.
Indexed names `{epsilon, h1, h2}` only. No named master in the input.

Wolfram 5-branch conditions, first-match order (Mathematica
`Piecewise[{{val,cond},...}, default]`):

```
n == m && m == ell     # triple coincidence
n == m                 # m identified with n, ell generic
n == ell               # ell identified with n, m generic
m == ell               # ell identified with m, n generic
<default>              # all three indices distinct
```

That is exactly the exclusive partition lattice of three dummy
indices. There is **no** extra source branch (no `n == ell && m == ell`
beside the And; transitivity makes it the same triple). There is
**no** missing pairwise. Sums 1–2 are the 2-index analogue (`n == m`
vs generic), related by the vertex permutation `b ↔ c` in `h1/h2`,
not by a degeneracy.

Frozen families split along those parent Piecewises. They do **not**
mix 2-index and 3-index sums, and they do not mix the two 3-index
spectator orientations in one family. That is the right cut of the
tensor. Gluing all 14 branches into one “Guo family” would be I-E;
they did not do it.

---

## 2. Frozen conds vs source branches

Six 5-member families (`guo-p2-s0-i3`, `s1-i2`, `s1-i3`, `s2-i2`,
`s2-i3`, `s4-i1`) carry the same five conds (srepr without
`integer=True`):

| member | frozen cond | source cond | role | full ops |
|---|---|---|---|---:|
| G0012 / G0019 | `And(Eq(ell,m), Eq(m,n))` | `n == m && m == ell` | higher-degeneracy | 33 |
| G0013 / G0020 | `Eq(m,n)` | `n == m` | diagonal | 333 |
| G0014 / G0021 | `Eq(ell,n)` | `n == ell` | diagonal | 379 |
| G0015 / G0022 | `Eq(ell,m)` | `m == ell` | diagonal | 379 |
| G0016 / G0023 | `True` | default | generic | 573 |

Argument order (`n == m` vs `Eq(m,n)`; And written `ell=m ∧ m=n`
vs Wolfram `n==m && m==ell`) does not change the partition.
`DEGENERACY_COORDINATES.json` closes `{ell,n}` under transitivity
on the And, so `free_coordinates` of the triple is empty. Correct:
the source never leaves `ell=n` free once `n=m` and `m=ell`.

`guo-p2-s2-i4` is the 2-index pair: G0004/G0005 from sum 1,
G0008/G0009 from sum 2. Coordinates `{m,n}` only.
`b ↔ c` is stored as `substitution_operators`, **not** as a
degeneracy. That matches the source: sums 1 and 2 are a discrete
vertex swap, not an energy coincidence.

Byte hashes of frozen member texts vs current Wolfram translation:

- 10 / 14 branches: identical `str` (and therefore SHA-256).
- 4 / 14 (both `Eq(ell,n)` diagonals and both generic defaults):
  SHA mismatch, ops 379 vs 378 and 573 vs 563.

The four mismatches are **printer / namespace**, not new kernels.
After identifying symbols (`real` vs `real+integer` on `m,n,ell`)
and expanding, `A - B = 0`. Difference is integer factoring in
denominators, e.g.

```
frozen:  (-96*epsilon(m) + 96*epsilon(n))
source:  (96*(-epsilon(m) + epsilon(n)))
```

Same meromorphic function. I-E is not triggered by a `Mul`
association. Frozen `ops` are therefore slightly inflated relative
to the live Wolfram adapter; the local-complexity table (567 / 327)
still describes the same objects.

---

## 3. Do `epsilon(*) -> epsilon(*)` operators match the kernels?

Covering paths (`PATH_CANDIDATES.json`) are cond-derived
one-parameter coarsenings, not operator fan-fiction. For the
G0012–G0016 lattice:

```
generic G0016 --ε(m)→ε(n)--> Eq(m,n) G0013 --ε(ell)→ε(n)--> And G0012
generic G0016 --ε(ell)→ε(n)--> Eq(ell,n) G0014 --ε(m)→ε(n)--> And G0012
generic G0016 --ε(ell)→ε(m)--> Eq(ell,m) G0015 --ε(m)→ε(n)--> And G0012
```

plus the six one-step edges. The two-parameter star
`G0016 → G0012` (`ε(ell),ε(m) → ε(n),ε(n)`) is
`rejected_multi_parameter` / `not_one_parameter`. Incomparable
diagonals (`Eq(m,n)` vs `Eq(ell,n)`) are not joined.

This is the physically correct 1-skeleton: you may coalesce one
remaining pair at a time. Joint coincidence is a source **branch**
(the And formula exists) but it is not a 1-parameter path. Rejecting
the star is the iterated-vs-joint distinction, not an invalid
decomposition.

Kernel support (epsilon atoms actually written in the branch)
agrees with the hop variable, which is stronger than cond parsing:

| branch | epsilons in the formula | hop to triple | remaining pole |
|---|---|---|---|
| G0016 True | `ε(ell), ε(m), ε(n)` | one of the three pairs | generic 3-denom |
| G0013 `m=n` | `ε(ell), ε(n)` | `ε(ell)→ε(n)` | `(-ε(ell)+ε(n))^4` in Wolfram |
| G0014 `ell=n` | `ε(m), ε(n)` | `ε(m)→ε(n)` | `ε(m)-ε(n)` |
| G0015 `ell=m` | `ε(m), ε(n)` | `ε(m)→ε(n)` | same, ell already glued to m |
| G0012 And | `ε(n)` only | — | no energy difference left |

On `Eq(ell,m)`, moving `ε(m)→ε(n)` also moves the already-identified
`ε(ell)`. One modulus, one parameter. The enumerator records a
single coordinate. That is right.

Polygamma orders in the source are **not** a permutation of one
formula:

- triple: `polygamma(4, ·)` only (33 ops)
- `m=n` diagonal: orders 0,1,2 (333 ops)
- `ell=n` / `ell=m`: orders 0,1,2,3 (378–379 ops)
- generic: orders 0,1,2 (563–573 ops)

The three pairwise strata are distinct physical degeneracies of an
asymmetric 3-leg kernel, not one object with relabeled legs. Treating
them as three different diagonals is required by the source, not an
over-split. Higher polygamma on the And is what repeated L'Hôpital
on a pole in several `ε(i)-ε(j)` produces. I am not going to name
the closed form; the written branches already know their coalescence
order.

Two-index analogue: G0005 generic has `ε(m), ε(n)` and
`(ε(m)-ε(n))^3` in the denominator; G0004 coincident has only
`ε(n)` and `polygamma(1,2,3)`. Frozen operator `ε(m)→ε(n)`. That
edge is ZERO (series, local ops 172). So on the 2-index sums, the
energy-limit reading of `n == m` is not an invention — it is a
certified identity of the written formulas. The 5-branch hop is the
same scientific move, unproven (timeout). That is I-D, not I-E.

---

## 4. Attacks that do **not** produce I-E

**Index equality vs energy limit.** Source Piecewise fires on dummy
index coincidence (`n == m`), not on `epsilon[n] == epsilon[m]`. If
`epsilon` is not injective, two distinct bands can be degenerate in
energy while the source still evaluates the generic (singular)
branch. That is a property of the input, not of the lattice. The
confluence claim is a relation **between written branch
expressions**: the coincident polygamma formula equals the
regularized limit of the generic formula in the energy variables.
`h1`/`h2` stay spectators (`AppliedUndef` of indices, not of
`epsilon`). Peel `S*K = E` is the right physics: vertex factors do
not participate in the thermal kernel’s pole.

**Operator spelling is heterogeneous; covering is not.** Frozen
operators say `epsilon(m)→epsilon(n)`, `{m: n}`, `var/to`,
`limits: [...]`, or `constraint: x -> y` (s4-i1, with
reconstruction order `ε(m), ε(n), ε(ell)`). Coordinate tables map
all of those onto the same undirected pairs `{m,n}`, `{ell,n}`,
`{ell,m}`. Path enumeration uses **conds**, provenance `"cond"`.
A bad operator key is ignored (fail closed). I could not find a
covering edge whose variable disagrees with the target cond.

**Free-coordinate overcount on diagonals.**
`DEGENERACY_COORDINATES.json` lists both `{ell,m}` and `{ell,n}` as
free on `Eq(m,n)`. Once `m=n`, those two pairs are the same
modulus. The table overcounts independent coordinates; the path
graph does not (union-find block count, `_n_params == 1`).
Presentation slop, not an extra hop.

**Duplicate P2 families.** The same G0012–G0016 (resp. G0019–G0023)
members appear under `local_confluence` and
`hermite_divided_difference`. Same conds, same texts, same lattice.
`claimed_type` is a proposer label on a frozen P2 JSON, not a
second source object and not an explicit interpolant F. Recurrence
stays UNKNOWN. Relabeling the same Piecewise is not I-E.

**Linear dependence of the three pairs.** `(ell=m)` follows from
`(ell=n) ∧ (m=n)`. Documented, not sold as a new representation.
The source And already omits the third equality. Fine.

**Substitution vs confluence on s2-i4.** Square

```
G0005 --ε(m)→ε(n)--> G0004     (PATH_ZERO)
  | b↔c
G0009 --ε(m)→ε(n)--> G0008     (PATH_ZERO)
```

`G0005 → G0009` substitution is UNKNOWN; family stays
FAMILY_UNKNOWN. They correctly refuse to promote two PATH_ZERO
edges to FAMILY_ZERO. Commutation of `b↔c` with coalescence is a
symmetry question, not a missing degeneracy coordinate.

**No interpolated kernels.** Source G#### members occupy
`{}, {m,n}, {ell,n}, {ell,m}, {ell,m,n}`.
`intermediates_required` is false for the six 5-member families.
Anonymous algebraic filling of a missing node would have been I-E.
It is not in the artifacts.

---

## 5. What would have been I-E (and is not here)

- Inventing a kernel for a cond the source does not write.
- Dropping Piecewise and declaring the generic formula valid on the
  diagonal (0/0).
- Joining `Eq(m,n)` to `Eq(ell,n)` by a one-parameter edge
  (incomparable strata).
- Treating `b↔c` or the PW3/PW4 spectator permutation as
  `epsilon` confluence.
- Calling the two-parameter star a one-parameter certificate.
- Pointing a proposer at a named master or a human ladder and
  asking the verifier to match it.

None of those are in `PATH_CANDIDATES.json` or
`DEGENERACY_COORDINATES.json`. Gold names are banned in PROTOCOL
and in the coordinate / path / intermediate tests; they are not
targets of this track.

---

## 6. Residual scientific gaps (I-D / I-C, not I-E)

The 5-branch hops remain UNKNOWN (`GUO_ITERATED_RESCORE.md`: 0
FAMILY_ZERO, 0 FAMILY_NONZERO, 7 FAMILY_UNKNOWN). Local ops after
an exact `h1` peel stay 327–567; the certified 2-member scale is
172. I believe the **formulas** stand in the confluence relation
the lattice writes — the 2-index ZERO is the same pattern — but
belief is not a certificate.

Path independence of the three covering routes generic → And is
not reached (no PATH_ZERO, consistency UNKNOWN). Iterated limit is
not joint limit until that is certified. That would be I-C if the
local edges had been ZERO. They were not.

Do not open a new representation proposer on this lattice. Do not
aim the next experiment at a named closed form. The missing object
is a generic decision procedure for one-parameter polygamma
confluence at ~300 ops, on kernels the source already wrote.

---

## 7. Answers

| question | answer |
|---|---|
| Do Eq(m,n) / Eq(ell,n) / Eq(ell,m) / And match source Piecewise? | **Yes.** Wolfram 5-branch conds, first-match order, both 3-index sums. |
| Do `epsilon(m)→epsilon(n)` operators match those branches? | **Yes**, as remaining energy moduli of the written kernels. Path graph uses conds; operators only rename the same pairs. |
| Byte-identical to live Wolfram translation? | 10/14 yes; 4/14 algebraically equal (denominator factoring + integer vs real symbols). |
| Invented intermediates? | **No.** |
| I-E? | **No.** Decomposition is valid under source semantics. |
| Case | **I-D** (local 5-branch edges UNKNOWN). Track D2 stays locked. |

I would use this lattice as a physicist’s index of coincidence
strata. I would not publish a 5-branch identity from it. The
source’s Piecewise is already the scientific statement; V3 asked
whether iterated one-parameter limits of those written kernels can
be certified. They cannot, yet, and that is not because the
branches were misread.
