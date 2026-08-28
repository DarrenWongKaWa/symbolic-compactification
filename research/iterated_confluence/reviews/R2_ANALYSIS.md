# Track V3 Reviewer 2 — iterated vs joint limits

Parent: `d977db457da2cd50b2b2a72968e8db3bd21d9405`
(`Close Track V3: iterated 5-branch hops remain UNKNOWN (I-D).`).
Branch: `work/v3-review-r2`. Isolated worktree. No method or freeze edits.

Objects read: `schema.py` (`compose_family_verdict`),
`consistency/auditor.py`, `compose/path.py`,
`eval/guo_iterated_rescore.py` (`_endpoint_consistency`),
`PROTOCOL.md`, `VERDICT.md`, plus path enumerator, generic suite,
falsifier, and literature pack as the mathematical contract.

No current `FAMILY_ZERO` on frozen Guo. No false-`FAMILY_ZERO` patch.

---

## Answers

**Does `PATH_ZERO` of two paths to the same source member illegally
assume commuting joint limits?**

- **As a path verdict: no.** `compose_path_verdict` / `compose_path`
  never mention a second path, a product neighborhood, or a simultaneous
  coalescence. One `PATH_ZERO` is one iterated chain of one-parameter
  source-member equalities.
- **As family glue on Guo: yes, latently.**
  `_endpoint_consistency` infers `CONSISTENT_ZERO` from two `PATH_ZERO`
  labels that share `(start_member, end_member)`, without evaluating
  either iterated limit of a single expression and without touching the
  rejected two-parameter edge. `compose_family_verdict` then treats that
  `CONSISTENT_ZERO` as the gate whose last sentence is “iterated limit
  is not joint limit unless consistency is certified.” That is the
  false converse of Moore–Osgood, encoded as a label rewrite.
- **Live on this close: no promotion.** All six 5-branch covering
  edges are `UNKNOWN` (timeout). The illegal rewrite has no `PATH_ZERO`
  pair to fire on. `FAMILY_ZERO = 0` remains true of the frozen rescore.

**Is I-D correctly distinguished from I-C?**

- **On the frozen run: yes.** Protocol I-C needs local edges `ZERO` and
  consistency `UNKNOWN`. Every 5-branch covering hop is `UNKNOWN`.
  `VERDICT.md` §8 (“Local symbolic complexity (I-D). Not I-C.”) matches
  the data.
- **As a decision procedure: no.** Three incompatible I-C predicates
  are in circulation; the Guo classifier uses the weakest; and
  `_endpoint_consistency` makes *protocol* I-C unreachable on a discrete
  source lattice. If any 5-branch edge later became `ZERO` while others
  stayed `UNKNOWN`, the report would flip to I-C while the bottleneck
  would still be I-D.

---

## 1. Three different limits

Let \(K\) be a generic 5-branch source member (e.g. `G0016`) with
degeneracy coordinates \(\varepsilon(\ell),\varepsilon(m),\varepsilon(n)\).
Write \(D\) for a diagonal member and \(T\) for the triple
(`G0012`). The enumerator emits three covering paths
generic → diagonal → triple, and *rejects* the joint hop:

```312:321:research/iterated_confluence/paths/PATH_CANDIDATES.json
      "rejected_multi_parameter": [
        {
          "source": "G0016",
          "target": "G0012",
          "relation": "repeated_node_confluence",
          "variable": "epsilon(ell),epsilon(m)",
          "target_value": "epsilon(n),epsilon(n)",
          "reason": "not_one_parameter",
          "n_parameters": 2
        }
```

Same pattern on all six 5-member families. The three objects are:

| object | formula | who certifies it |
|---|---|---|
| one-parameter edge | \(\lim_{\varepsilon(a)\to\varepsilon(b)} K_{\mathrm{src}} = K_{\mathrm{tgt}}\) | V3-D `certify_one_parameter` |
| iterated path | \(\lim_{\varepsilon(\ell)\to\varepsilon(n)}\bigl(\lim_{\varepsilon(m)\to\varepsilon(n)} K\bigr)\) | V3-E `compose_path` of those edges |
| joint / simultaneous | \(\lim_{(\varepsilon(\ell),\varepsilon(m))\to(\varepsilon(n),\varepsilon(n))} K\) | **nobody**; rejected as `not_one_parameter` |

Standard analysis (`literature/METHODS.md` §2, Apostol / Rudin /
Moore–Osgood), not a V3 theorem:

1. Joint existence + inner one-parameter limits ⇒ both iterated
   limits exist and equal the joint value.
2. The converse is false. Textbook:
   \(f(x,y)=xy/(x^2+y^2)\) at the origin has both iterated limits \(0\),
   while along \(y=mx\) the value is \(m/(1+m^2)\), so the joint limit
   does not exist.
3. Iterated limits may exist and *disagree* (\(x/(x+y)\)).
4. Uniformity of one inner limit restores the joint limit
   (Moore–Osgood). Uniformity is an extra hypothesis.

`PROTOCOL.md` safety rule is (2): do not assume iterated = joint unless
that equality is itself certified. `AGENTS.md` rule 14 is the same
scientific choice.

`PATH_ZERO` is (iterated). `FAMILY_ZERO` under
`require_path_independence=True` is sold as (joint). The glue between
them is `CONSISTENT_ZERO`. That glue is where the audit sits.

---

## 2. What one `PATH_ZERO` actually is

```174:185:research/iterated_confluence/schema.py
def compose_path_verdict(step_verdicts: list[str]) -> str:
    """Compose one path from local step verdicts.

    Empty path is PATH_UNKNOWN, not PATH_ZERO.
    """
    if not step_verdicts:
        return PATH_UNKNOWN
    if any(_is_nonzero(v) for v in step_verdicts):
        return PATH_NONZERO
    if all(_is_edge_zero(v) for v in step_verdicts):
        return PATH_ZERO
    return PATH_UNKNOWN
```

`compose/path.py` only packages this rule. Empty path is
`PATH_UNKNOWN`. Majority `ZERO` plus one `UNKNOWN` is
`PATH_UNKNOWN`. The package never calls `compose_family_verdict`
(enforced by `tests/test_ic_compose.py`).

On a two-step covering path `G0016 → G0013 → G0012`,
`PATH_ZERO` means:

\[
\lim_{\varepsilon(m)\to\varepsilon(n)} K_{G0016}=K_{G0013},
\qquad
\lim_{\varepsilon(\ell)\to\varepsilon(n)} K_{G0013}=K_{G0012}.
\]

If both edges are genuine one-parameter identities of those source
expressions, transitivity gives the *iterated* limit of \(K_{G0016}\)
along that coordinate order, equal to the source member \(K_{G0012}\).
That is not a joint limit, and the path composer does not claim it is.

This part is sound.

---

## 3. Two `PATH_ZERO` paths to the same source member

### 3.1 Transitivity (legal, iterated vs iterated)

Suppose two covering paths share source endpoints:

- Path A: \(K \xrightarrow{\varepsilon(m)\to\varepsilon(n)} D_A
  \xrightarrow{\varepsilon(\ell)\to\varepsilon(n)} T\)
- Path B: \(K \xrightarrow{\varepsilon(\ell)\to\varepsilon(n)} D_B
  \xrightarrow{\varepsilon(m)\to\varepsilon(n)} T\)

If both are `PATH_ZERO`, then

\[
(\text{iterated along A})\,K = T_{\text{source}}
= (\text{iterated along B})\,K.
\]

That is equality of two iterated limits of the *starting source
member*, both identified with the same frozen end member. It is
ordinary transitivity of `ZERO` edges. It is **not** Moore–Osgood,
not uniformity, and not
\(\lim_{(\varepsilon(\ell),\varepsilon(m))\to(\varepsilon(n),\varepsilon(n))}K=T\).

The Guo 5-branch lattice has exactly this shape: three two-step
covering paths, one multi-end pair `(G0016, G0012)` (or
`(G0023, G0019)`), and a rejected two-parameter star on that same pair.

### 3.2 Textbook block (illegal if sold as joint)

Replay of the literature counter-example through the *actual* auditor:

```text
check_two_paths( xy/(x**2+y**2),  (y→0 then x→0),  (x→0 then y→0) )
  → CONSISTENT_ZERO   provenance agree:substitution+substitution|…

along y = m x:  m/(m**2+1)  (joint limit does not exist)
```

`CONSISTENT_ZERO` here is “two iterated orders of one expression
agree.” It is the hypothesis of the false converse, not a joint
certificate. The auditor README nevertheless says: never treat
iterated limits as a joint limit *unless this auditor returns
`CONSISTENT_ZERO`*. That sentence is false as analysis: the auditor
returning `CONSISTENT_ZERO` is exactly the situation in which the
joint limit may still fail.

The schema repeats the same conflation:

```41:48:research/iterated_confluence/schema.py
COMPOSITION_RULE = (
    "PATH_ZERO iff every required step is ZERO; any step NONZERO => PATH_NONZERO; "
    "else PATH_UNKNOWN. FAMILY_ZERO iff every required path is PATH_ZERO, every "
    "required local edge is ZERO, branch reconstruction is ZERO, and — whenever "
    "the claim needs order independence — path consistency is CONSISTENT_ZERO. "
    "Any required NONZERO or INCONSISTENT_NONZERO => FAMILY_NONZERO. Otherwise "
    "FAMILY_UNKNOWN. PATH_ZERO is not FAMILY_ZERO. Majority is forbidden. "
    "Iterated limit is not joint limit unless consistency is certified."
)
```

Last sentence: `CONSISTENT_ZERO` is the joint-limit certificate.
`PathConsistencyObligation` docstring is more honest (“agreement of
two iterated paths”) and contradicts that last sentence.
`literature/CLASSIFICATION.md` §3 is also honest: “agreement of two
iterated orders is not the joint limit.” The composition rule, the
auditor README, and `METHODS.md` §2 (“that is Moore–Osgood honesty”)
are not. Uniformity is never an obligation.

`compose_family_verdict` implements the conflation:

```216:221:research/iterated_confluence/schema.py
    if require_path_independence:
        if not cons or not all(_is_consistent_zero(v) for v in cons):
            return FAMILY_UNKNOWN
    if paths_ok and recs_ok and edges_ok:
        return FAMILY_ZERO
    return FAMILY_UNKNOWN
```

Two `PATH_ZERO` covering paths + `CONSISTENT_ZERO` + reconstruction
`ZERO` ⇒ `FAMILY_ZERO`, with no joint-limit input. `_is_consistent_zero`
even accepts a raw `ZERO` as consistency.

---

## 4. The Guo rescore rewrite (the live mechanism)

The order-of-limits auditor is **not called** on frozen Guo.
`eval/guo_iterated_rescore.py` does not import `check_two_paths`.
Glue is this function:

```120:144:research/iterated_confluence/eval/guo_iterated_rescore.py
def _endpoint_consistency(path_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """PATH_ZERO paths with the same start and end agree at the source end-member."""
    by_ends: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for p in path_rows:
        key = (p["start_member"], p["end_member"])
        by_ends.setdefault(key, []).append(p)
    out = []
    for (start, end), group in sorted(by_ends.items()):
        if len(group) < 2:
            continue
        verdicts = [g["path_verdict"] for g in group]
        if any(v == PATH_NONZERO for v in verdicts):
            v = INCONSISTENT_NONZERO
        elif all(v == PATH_ZERO for v in verdicts):
            v = CONSISTENT_ZERO
        else:
            v = CONSISTENCY_UNKNOWN
        ...
```

This is a label rewrite, not an evaluation:

| inputs | inferred verdict | mathematical content |
|---|---|---|
| all `PATH_ZERO`, same `(start,end)` source ids | `CONSISTENT_ZERO` | transitivity of discrete hops, sold as order independence |
| any `PATH_NONZERO` in the group | `INCONSISTENT_NONZERO` | a failed claimed hop, not an order-of-limits disagreement |
| mixed `PATH_ZERO` / `PATH_UNKNOWN` | `UNKNOWN` | honest |

Then:

```267:282:research/iterated_confluence/eval/guo_iterated_rescore.py
        cons = _endpoint_consistency(path_rows)
        covering = [pr for pr in path_rows if pr["n_steps"] >= 2]
        if not covering:
            covering = path_rows
        require_ind = any(int(c.get("n_paths") or 0) >= 2 for c in cons)
        ...
        fam_v = compose_family_verdict(
            path_verdicts=[pr["path_verdict"] for pr in covering],
            consistency_verdicts=[c["verdict"] for c in cons] if require_ind else [],
            reconstruction_verdicts=["ZERO"],
            required_edge_verdicts=sub_verdicts,
            require_path_independence=require_ind,
        )
```

Four independent holes, of which the first is the assigned attack.

### 4.1 Same-end `PATH_ZERO` pair ⇒ `FAMILY_ZERO` without a joint hop

Replay (not a frozen family; a rule check):

```text
two PATH_ZERO covering paths, same (G, Z)
_endpoint_consistency → CONSISTENT_ZERO
compose_family_verdict(..., reconstruction=["ZERO"], edges=["ZERO",...],
                       require_path_independence=True)
  → FAMILY_ZERO
```

On a 5-branch family this is exactly “three covering paths
generic→triple all `PATH_ZERO`.” The two-parameter obligation
`G0016 → G0012` along
\((\varepsilon(\ell),\varepsilon(m))\to(\varepsilon(n),\varepsilon(n))\)
is in `rejected_multi_parameter` and is **not** in
`required_edge_verdicts` (that list is substitutions only; 5-branch
substitutions are empty). `FAMILY_ZERO` would therefore certify the
family without the joint coalescence the protocol forbids assuming.

That is the illegal commuting-joint-limit assumption.

It does not fire today: covering path verdicts are `PATH_UNKNOWN`.

### 4.2 Different-end `PATH_ZERO` pair ⇒ skip consistency

`_endpoint_consistency` keys on source-member ids, not on the
degeneracy point. Attack `V3J_02` (`x/(x+y)`): both paths are
`PATH_ZERO` against *their own* intermediates, ends `Za=1` vs `Zb=0`.
The falsifier compares iterated *values* and returns
`INCONSISTENT_NONZERO`. The Guo rewrite sees two different
`(start,end)` keys, emits no obligation, sets
`require_path_independence=False`, and the same schema call returns
`FAMILY_ZERO`.

Replay:

```text
PATH_ZERO G→Za and PATH_ZERO G→Zb
_endpoint_consistency → []
require_ind → False
compose_family_verdict(..., cons=[], require_path_independence=False)
  → FAMILY_ZERO
```

So the only noncommuting-limits attack in the falsifier suite would
be a false `FAMILY_ZERO` *if scored by the Guo pipeline*. The
falsifier does not use `_endpoint_consistency`; the Guo rescore does
not use the falsifier’s value comparison. The two composition paths
are not the same function.

Guo 5-branch covering paths do share `(G0016, G0012)`, so this
particular skip is not the 5-branch case. It is a hole in the same
function.

### 4.3 Hardcoded reconstruction `ZERO`

`reconstruction_verdicts=["ZERO"]` is a constant. Spectator
`split_certified` is recorded on edges and ignored by
`compose_family_verdict`. Literature §8: an iterated limit of a
modified kernel that does not rebuild the source is a different
claim. Not live today (paths are not `PATH_ZERO`).

### 4.4 Auditor size-guard would have blocked Guo even after local `ZERO`

`LIMIT_OPS_CAP = 80`. Frozen 5-branch local ops after peel: 327
(diagonal→triple) and 567 (generic→diagonal). `check_two_paths` on
any such kernel returns `UNKNOWN` / `size_guard` without entering
the limit cascade (`tests/test_ic_consistency.py`).

If local covering edges became `ZERO` and the rescore *used* the
auditor, protocol I-C would fire: local edges `ZERO`, consistency
`UNKNOWN`, `FAMILY_UNKNOWN`, D2 locked. That is the fail-closed
outcome Moore–Osgood requires on an untrusted 300-op polygamma
kernel (no \(C^k\), no uniformity proof; Hermite–Genocchi is
explicitly forbidden as a skip).

`_endpoint_consistency` bypasses that size-guard. The same local
`ZERO`s would become `CONSISTENT_ZERO` then `FAMILY_ZERO` (I-A).
That is the latent false-`FAMILY_ZERO` rule. It is not a current
false promotion, so method code was left frozen.

---

## 5. What the auditor *does* get right

`check_two_paths` evaluates two iterated one-parameter chains of a
*single* expression, independently, then residual-compares
(`_expr_equal`). Timeout, size-guard, parse failure, both-nonfinite,
and undecided compare are `UNKNOWN`, never `CONSISTENT_ZERO`.
`x/(x+y)` is `INCONSISTENT_NONZERO`. Cubic Newton second DD is
`CONSISTENT_ZERO`. `family_zero_blocked` refuses `FAMILY_ZERO` on
missing/`UNKNOWN` consistency when independence is required, and
always blocks `INCONSISTENT_NONZERO`.

Schema tests match: `PATH_ZERO+PATH_ZERO` + `UNKNOWN` +
`require_path_independence` → `FAMILY_UNKNOWN`;
`PATH_ZERO+PATH_ZERO` + `INCONSISTENT_NONZERO` → `FAMILY_NONZERO`.

Those tests never insert a joint-limit obligation. They also never
run `_endpoint_consistency`. The fail-closed schema is real; the Guo
glue that feeds it is not the auditor the tests describe.

Generic suite case `A-joint-iterated-agree` hardcodes
`consistency_verdicts=[CONSISTENT_ZERO]` with the comment
“polynomial; orders agree at a point.” It does not call
`check_two_paths` and does not check a product neighborhood. On
\(z^3\) the joint limit happens to exist; the suite does not prove
it. The name of the case is the same conflation.

---

## 6. I-D vs I-C

Protocol (`PROTOCOL.md`):

| class | predicate | D2 |
|---|---|---|
| I-C | local edges `ZERO`, path consistency `UNKNOWN` | locked |
| I-D | local edge `UNKNOWN` | locked |

Literature self-adversarial note (`METHODS.md` §11.3) is a *different*
predicate: “`PATH_ZERO` on one coordinate order, with the other order
`PATH_UNKNOWN`, is outcome I-C.” That is mixed paths, hence still a
local `UNKNOWN` edge — protocol I-D.

The Guo report classifier is a third predicate:

```308:317:research/iterated_confluence/eval/guo_iterated_rescore.py
    if n_five_z:
        case = "I-A"
    elif n_fn:
        case = "I-B"
    elif any(r["n_zero_edges"] and r["consistency"] == CONSISTENCY_UNKNOWN for r in family_rows):
        case = "I-C"
    elif any(r["n_unknown_edges"] for r in family_rows):
        case = "I-D"
    else:
        case = "I-E"
```

`n_zero_edges` is “at least one `ZERO` edge,” not “all required local
edges `ZERO`.” `any(...)` is report-level. `r["consistency"]` is
`cons[0]["verdict"]` only — the first endpoint group.

### 6.1 Frozen run (this close)

| family | n | ZERO edges | UNKNOWN | PATH_ZERO | consistency | `require_ind` | family |
|---|---:|---:|---:|---:|---|---|---|
| six 5-branch | 5 | 0 | 6 | 0 | `UNKNOWN` | true | `FAMILY_UNKNOWN` |
| `guo-p2-s2-i4` | 4 | 2 | 1 | 2 | `n/a` | false | `FAMILY_UNKNOWN` |

5-branch `consistency=UNKNOWN` is `_endpoint_consistency` on three
`PATH_UNKNOWN` covering paths, not an auditor size-guard. I-C’s
`n_zero_edges` conjunct is false (0). I-D’s `n_unknown_edges` conjunct
is true. Report case **I-D**. Correct for protocol I-C vs I-D.

`guo-p2-s2-i4` is two *different* one-step pairs (`G0005→G0004`,
`G0009→G0008`) plus an unknown `b↔c` substitution. Those two
`PATH_ZERO` paths do **not** share `(start,end)`, so they are not the
assigned two-path-to-one-member pattern. `require_path_independence`
is false because `cons` is empty. Family stays `FAMILY_UNKNOWN` on
the substitution, which is still I-D at family grain. Reused Track V
pair `ZERO`s are not a 4-member joint certificate (`METHODS.md`
§11.2). Agreed.

Bottleneck: 327–567-op one-parameter polygamma hops timeout.
Path independence of 5-branch kernels was never reached. `VERDICT.md`
§4 and §8 and `CAPABILITY_BOUNDARY.md` (“not I-C”) are right *for
this evidence*.

### 6.2 Why the distinction is not robust

Replay of the classifier on the frozen JSON with one field flipped:

| mutation | classifier |
|---|---|
| 5-branch all covering edges `ZERO` (endpoint rewrite ⇒ `CONSISTENT_ZERO`, `FAMILY_ZERO`) | **I-A** (protocol I-C skipped) |
| one 5-branch edge `ZERO`, five still `UNKNOWN` | **I-C** (protocol I-D) |
| `s2-i4` consistency field set to `UNKNOWN` | **I-C** (report stolen from 5-branch I-D) |

So:

- Protocol I-C (all local edges `ZERO`, consistency genuinely
  unknown) cannot occur on Guo rescore: two `PATH_ZERO` covering
  paths auto-promote to `CONSISTENT_ZERO`. The scientifically
  correct next stop after local `ZERO` — auditor `size_guard` on
  327-op kernels — is never reached.
- Methods-note I-C (one order `PATH_ZERO`, the other
  `PATH_UNKNOWN`) *is* what the classifier calls I-C, and that
  contradicts protocol I-D.
- 5-branch table column `consistency=UNKNOWN` looks like I-C to a
  reader of `GUO_ITERATED_RESCORE.md`; the `n_zero_edges=0` column
  is the only thing preventing that misread.

I-D vs I-C is correctly *reported* on `d977db4`. It is not correctly
*mechanized*.

---

## 7. Claims that survive

- `PATH_ZERO` of one path is not `FAMILY_ZERO`
  (`compose/path.py`, schema tests, generic majority case). Sound.
- Empty path is not `PATH_ZERO`. Sound.
- Order-dependent toy \(x/(x+y)\) is `INCONSISTENT_NONZERO` in the
  *auditor* and `FAMILY_NONZERO` in the *falsifier*. Sound, and
  **not** the Guo composition path.
- Two-parameter stars are not enumerated as one-parameter paths.
  Sound graph hygiene; the scientific cost is that the joint
  obligation is then dropped rather than scored `UNKNOWN`.
- Frozen Guo: 0 `FAMILY_ZERO`, 0 `FAMILY_NONZERO`, 7
  `FAMILY_UNKNOWN`, case I-D. Sound as a snapshot.
- D2 remains locked. Sound.

---

## 8. Claims that do not survive as analysis

- “Iterated limit is not joint limit unless consistency is
  certified,” when `CONSISTENT_ZERO` is either (i) agreement of two
  iterated orders or (ii) two `PATH_ZERO` labels on the same source
  endpoints. That sentence is the false converse of Moore–Osgood.
- “Never treat iterated limits as a joint limit unless
  `check_two_paths` returns `CONSISTENT_ZERO`.” Replay:
  \(xy/(x^2+y^2)\) returns `CONSISTENT_ZERO`; joint limit does not
  exist.
- Treating `_endpoint_consistency` as an order-of-limits auditor.
  It never takes an expression.
- Invoking Moore–Osgood / Hermite–Genocchi / “the lattice already
  landed on the same `G####`” to skip uniformity on Piecewise
  polygamma (`CLASSIFICATION.md` forbidden upgrade; `AGENTS.md`
  rule 14).
- Report class I-C as implemented in
  `guo_iterated_rescore.py`. It is not protocol I-C.

---

## 9. False-`FAMILY_ZERO` status

| channel | false `FAMILY_ZERO` |
|---|---|
| frozen Guo rescore, this parent | 0 (7× `FAMILY_UNKNOWN`) |
| generic suite | 0 (recorded) |
| falsifier 8 attacks + 2 controls | 0 (falsifier uses value comparison, not `_endpoint_consistency`) |
| Guo rule if covering edges become `ZERO` | **would be 6× `FAMILY_ZERO` without a joint hop** |
| Guo rule on `V3J_02`-shaped different ends | **would be `FAMILY_ZERO`** |

No live false promotion on `d977db4`. The promotion rule is wrong.
Method code was not edited.

If a later increment closes 5-branch one-parameter hops, the correct
family verdict is `FAMILY_UNKNOWN` (protocol I-C): call
`check_two_paths` (it will `size_guard`), keep the two-parameter
rejected edge as an `UNKNOWN` required obligation, and do not infer
`CONSISTENT_ZERO` from source-member ids. Unlocking D2 on that
`FAMILY_ZERO` would be a joint-limit assumption, not a certificate.

---

## 10. Direct answers restated

**Two `PATH_ZERO` paths to the same source member do not, by
themselves, assume commuting joint limits.** They assume transitivity
of one-parameter source-member equalities. That is iterated vs
iterated.

**The Track V3 Guo composition *does* illegally treat that pair as
commuting joint limits**, by rewriting it to `CONSISTENT_ZERO` and
feeding it to a family rule whose documentation calls that rewrite
the iterated=joint certificate, while the actual joint hop is sitting
in `rejected_multi_parameter` and is never scored.

**I-D is correctly distinguished from I-C on the closed frozen
run.** Local 5-branch edges are `UNKNOWN`. Path consistency was not
the bottleneck. **I-C is not a correctly implemented alternative
class** in the Guo rescore: it is unreachable after local `ZERO`
because of the same rewrite, and it is over-triggered on mixed
`ZERO`+`UNKNOWN` families.
