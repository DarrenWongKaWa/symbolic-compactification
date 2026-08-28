# R4 — PL / verification: attack certificate composition soundness

Parent: `d977db457da2cd50b2b2a72968e8db3bd21d9405`
Branch: `work/v3-review-r4`
Role: Reviewer 4 (PL / verification). Isolated worktree. No coordination with other reviewers.

**Question.** Can an attack certificate — majority PATH_ZERO, one-path PATH_ZERO, timeout/size-guard UNKNOWN, missing consistency, or the frozen `guo-p2-s2-i4` shape (2 PATH_ZERO + UNKNOWN substitution) — compose to `FAMILY_ZERO`?

**Verdict. PASS on the five closed-track claims.** Schema composition is an all-quantifier, not a vote. Frozen Guo stays `FAMILY_UNKNOWN` (7/7). Adversarial suite false `FAMILY_ZERO` = 0. Residual holes exist in vacuous quantifiers and in the Guo rescore's `require_path_independence` heuristic; they do **not** fire on frozen artifacts or on the attack suite as written.

Do not reopen Track D2 on the basis of this audit.

---

## 1. Scope and method

Read (and executed against) the composition surface:

| object | path |
|---|---|
| family/path rules | `research/iterated_confluence/schema.py` |
| path packaging | `research/iterated_confluence/compose/path.py` |
| attack suite | `research/iterated_confluence/falsifier/` |
| schema tests | `tests/test_ic_schema.py` |
| falsifier tests | `tests/test_ic_falsifier.py` |
| close claims | `research/iterated_confluence/TRACK_V3_CLOSED.md` |

Production composer required to attack s2-i4 (not listed in the prompt, but it is the only call site that builds frozen family verdicts): `research/iterated_confluence/eval/guo_iterated_rescore.py`. Also checked `consistency/auditor.py`, `edges/certify.py`, `eval/generic_suite.py`, `PROTOCOL.md`, `VERDICT.md`, `GUO_ITERATED_RESCORE.json`.

Python: `.venv/bin/python`.

```
tests/test_ic_schema.py tests/test_ic_compose.py tests/test_ic_falsifier.py
tests/test_ic_consistency.py tests/test_ic_generic_suite.py tests/test_ic_edges.py
→ 85 passed
```

Falsifier live run: `n_false_family_zero = 0` (8 attacks + 2 commuting controls). Frozen rescore artifact: `FAMILY_ZERO=0 FAMILY_NONZERO=0 FAMILY_UNKNOWN=7`.

---

## 2. The rule that is actually implemented

`COMPOSITION_RULE` and the two functions are the only composers. `compose/path.py` packages `compose_path_verdict`; it does not import or name `FAMILY_ZERO` (enforced by `test_source_ban_compose_does_not_decide_family_zero`). The falsifier calls the schema functions by identity (`inspect.getmodule(...) is schema_mod`, no `__wrapped__`).

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

```174:221:research/iterated_confluence/schema.py
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


def compose_family_verdict(
    ...
) -> str:
    ...
    if any(_is_nonzero(v) for v in pool):
        return FAMILY_NONZERO
    if not (paths or edges):
        return FAMILY_UNKNOWN
    paths_ok = all(_is_path_zero(v) for v in paths)
    recs_ok = all(_is_edge_zero(v) for v in recs)
    edges_ok = all(_is_edge_zero(v) for v in edges)
    if require_path_independence:
        if not cons or not all(_is_consistent_zero(v) for v in cons):
            return FAMILY_UNKNOWN
    if paths_ok and recs_ok and edges_ok:
        return FAMILY_ZERO
    return FAMILY_UNKNOWN
```

NONZERO wins over UNKNOWN at both layers. UNKNOWN never becomes ZERO. There is no vote, no `n_zero > n/2`, no timeout special case.

---

## 3. Mandated checks

### 3.1 PATH_ZERO is not FAMILY_ZERO — HOLD (default rule)

`PATH_ZERO` and `FAMILY_ZERO` are distinct strings. A path of all `ZERO` steps is `PATH_ZERO`; that fact alone never yields `FAMILY_ZERO` when `require_path_independence=True` (the dataclass default and the PROTOCOL default).

Probed:

| call | result |
|---|---|
| `path_verdicts=[PATH_ZERO]`, cons missing, `require_path_independence=True` | `FAMILY_UNKNOWN` |
| `path_verdicts=[PATH_ZERO, PATH_ZERO]`, cons missing, `True` | `FAMILY_UNKNOWN` |
| two `PATH_ZERO` + `CONSISTENT_ZERO` + edges `ZERO` | `FAMILY_ZERO` (the intended positive) |
| empty path steps | `PATH_UNKNOWN`, not `PATH_ZERO` |

Tests: `test_path_zero_is_not_family_zero` in both `test_ic_schema.py` and `test_ic_compose.py`; falsifier `V3J_01_one_path_zero_other_nonzero` (one `PATH_ZERO` + one `PATH_NONZERO` → `FAMILY_NONZERO`). Forbidden leap composer `forbidden_pairwise_leap` would return `FAMILY_ZERO` on “any PATH_ZERO and no PATH_NONZERO”; the real rule does not.

`compose_path` / `compose_paths` never call `compose_family_verdict` (`test_compose_path_does_not_call_family_rule`).

### 3.2 Majority ban — HOLD

There is no majority operator in schema, compose, falsifier checkers, or rescore. Family zero requires **every** required path `PATH_ZERO` (and every required edge `ZERO`). A single `PATH_UNKNOWN` or `UNKNOWN` edge falsifies `paths_ok` / `edges_ok`.

| attack | result |
|---|---|
| `[PATH_ZERO, PATH_ZERO, PATH_UNKNOWN]` + `CONSISTENT_ZERO` | `FAMILY_UNKNOWN` |
| same, `require_path_independence=False` | `FAMILY_UNKNOWN` (majority still cannot win) |
| `[PATH_ZERO]×4 + [PATH_UNKNOWN]` + `CONSISTENT_ZERO` | `FAMILY_UNKNOWN` (4/5 is not a certificate) |
| path steps `ZERO, ZERO, UNKNOWN` | `PATH_UNKNOWN` |

Tests: `test_majority_paths_not_family_zero`; `test_majority_zero_plus_unknown_is_not_path_zero`; generic suite `neg-majority-unknown`; falsifier `V3J_08_majority_path_unknown` (2 Newton `PATH_ZERO` + size-guard `PATH_UNKNOWN` → `FAMILY_UNKNOWN`). The trap `forbidden_majority_paths` returns `FAMILY_ZERO` on that case; `test_majority_unknown_case_is_not_family_zero` asserts the real composer does not.

`PROTOCOL.md` forbids “majority FAMILY_ZERO”. `TRACK_V3_CLOSED.md` claim “Majority PATH_ZERO + UNKNOWN is FAMILY_UNKNOWN” matches the live rule.

### 3.3 Timeout never ZERO — HOLD

Timeout is a **provenance**, not a verdict. The verdict is `UNKNOWN` / `PATH_UNKNOWN` / `FAMILY_UNKNOWN` / `CONSISTENCY_UNKNOWN`. No layer maps timeout onto `ZERO`.

| layer | fail-closed path |
|---|---|
| one-parameter edge | `BudgetExceeded` → `UNKNOWN` + provenance `timeout`; `_sanitize` rewrites any `ZERO` whose provenance contains `timeout` / is in `_BLOCKED_ZERO` |
| Guo rescore | `_budgeted`: `BudgetExceeded` and any exception → `UNKNOWN` |
| path consistency | `BudgetExceeded` / size-guard / CAS failure → `CONSISTENCY_UNKNOWN`, never `CONSISTENT_ZERO` |
| path compose | `ZERO` + `UNKNOWN` → `PATH_UNKNOWN`; empty path → `PATH_UNKNOWN` |
| family compose | any required `UNKNOWN` blocks `FAMILY_ZERO` (unless some sibling is NONZERO, which yields `FAMILY_NONZERO`) |
| falsifier steps | `opaque` / `unknown_reason` (size_guard) short-circuits to `UNKNOWN` without a residual check |

Tests: `test_timeout_is_unknown_never_zero` (edges); `test_timeout_is_unknown_never_consistent_zero` (auditor); `test_timeout_unknown_never_becomes_family_zero` (falsifier/schema); `test_huge_kernel_is_unknown_not_consistent_zero`. Frozen 5-branch hops are provenance `timeout` with verdict `UNKNOWN` in `GUO_ITERATED_RESCORE.json`.

`_CONFIRM_SKIP` in `consistency/auditor.py` includes `"timeout"` and `"size_guard"`. That skip only treats an already-computed candidate as confirmed; `_limit_value` itself returns `("unknown", None, "timeout")` and does not call `_confirm_limit` with those `how` values. Latent, not currently live.

### 3.4 `require_path_independence` — HOLD on default; bypass is explicit

`IteratedConfluenceCertificate.require_path_independence` defaults to `True`.

When `True`:

- missing consistency list → `FAMILY_UNKNOWN` (the one-path / two-path PATH_ZERO attacks die here);
- any consistency not `_is_consistent_zero` → `FAMILY_UNKNOWN`;
- `INCONSISTENT_NONZERO` is in the NONZERO pool and yields `FAMILY_NONZERO` **before** the independence gate.

When `False`:

- missing or `UNKNOWN` consistency is ignored;
- `INCONSISTENT_NONZERO` still yields `FAMILY_NONZERO` (independence flag is not a license to ignore a computed disagreement);
- a single `PATH_ZERO` path with reconstruction/edges `ZERO` **is** `FAMILY_ZERO`. This is the documented single-path family (`test_single_path_family_without_independence`).

Probed extra (not in `test_ic_schema.py`):

| call | result |
|---|---|
| two `PATH_ZERO`, cons `UNKNOWN`, `require_path_independence=False` | **`FAMILY_ZERO`** |
| two `PATH_ZERO`, cons `INCONSISTENT_NONZERO`, `False` | `FAMILY_NONZERO` |
| two `PATH_ZERO`, no cons, `False`, no required edges | **`FAMILY_ZERO`** |

The last row is the s2-i4 substitution-omission attack (next section). `family_zero_blocked(..., require_path_independence=False)` agrees that UNKNOWN consistency does not block, but still blocks `INCONSISTENT_NONZERO`.

Guo rescore does **not** use the certificate default. It infers the flag from enumerator topology:

```267:282:research/iterated_confluence/eval/guo_iterated_rescore.py
        cons = _endpoint_consistency(path_rows)
        covering = [pr for pr in path_rows if pr["n_steps"] >= 2]
        if not covering:
            covering = path_rows
        require_ind = any(int(c.get("n_paths") or 0) >= 2 for c in cons)
        sub_verdicts = [
            edge_verdicts[(s["source"], s["target"], s.get("variable"), s.get("target_value"))]["verdict"]
            for s in fam_paths.get("substitutions") or []
        ]
        fam_v = compose_family_verdict(
            path_verdicts=[pr["path_verdict"] for pr in covering],
            consistency_verdicts=[c["verdict"] for c in cons] if require_ind else [],
            reconstruction_verdicts=["ZERO"],
            required_edge_verdicts=sub_verdicts,
            require_path_independence=require_ind,
        )
```

So independence is required only when two enumerated paths share `(start_member, end_member)`. Five-branch covering paths (generic → triple via three diagonals) share endpoints → `require_path_independence=true` in the artifact. `guo-p2-s2-i4` paths are disjoint pairs → `false`. That heuristic is weaker than “the representation claim needs order independence” in `COMPOSITION_RULE`. It is safe on the frozen 5-branch lattice (covering paths really do share ends) and is the reason s2-i4’s family verdict depends entirely on the substitution edge.

`_endpoint_consistency` never calls `check_two_paths`. It sets `CONSISTENT_ZERO` if every same-endpoint path is `PATH_ZERO`. That is sound **if** each `PATH_ZERO` step is an honest sequential limit against the named member: two such paths to the same end-member both equal that member. It is **not** an independent evaluation of iterated limits of the start expression. Defense-in-depth gap; it does not fire today because no frozen covering path is `PATH_ZERO`.

### 3.5 s2-i4: 2 PATH_ZERO + UNKNOWN substitution is not FAMILY_ZERO — HOLD on the artifact

Frozen close claim (`TRACK_V3_CLOSED.md`, `VERDICT.md` §5/§9):

> `guo-p2-s2-i4` has 2 ZERO one-parameter edges (G0005→G0004, G0009→G0008, series, local ops 172) and 1 UNKNOWN substitution. Family stays FAMILY_UNKNOWN.

Live artifact `GUO_ITERATED_RESCORE.json`:

| field | value |
|---|---|
| family_id | `guo-p2-s2-i4` |
| n_path_zero | 2 |
| n_zero_edges | 2 (confluences) |
| n_unknown_edges | 1 |
| substitution G0005→G0009 `b→c` | `UNKNOWN` / provenance `UNKNOWN` |
| consistency | `n/a` |
| `require_path_independence` | **false** |
| `family_verdict` | **`FAMILY_UNKNOWN`** |

`PATH_CANDIDATES.json` stores the substitution **outside** `paths` (`substitutions: [{G0005, G0009, substitution}]`). `test_s2_i4_two_confluence_one_step_paths` asserts `(G0005, G0009)` is not a path pair and that the substitution record exists. Rescore threads `sub_verdicts` into `required_edge_verdicts`. Schema then fails `edges_ok` on `UNKNOWN`.

Reconstructed schema calls:

| call (s2-i4 shape) | result |
|---|---|
| 2×`PATH_ZERO`, cons `[]`, rec `ZERO`, edges `[UNKNOWN]`, `require_path_independence=False` | `FAMILY_UNKNOWN` — **actual frozen call** |
| 2×`PATH_ZERO`, cons `[]`, rec `ZERO`, **no** required edges, `False` | **`FAMILY_ZERO`** — substitution-omission attack |
| 2×`PATH_ZERO`, cons `[]`, rec `ZERO`, edges `[ZERO]`, `False` | `FAMILY_ZERO` — would be correct only if the substitution were actually certified |

`test_ic_schema.py` has **no** case of this shape. Majority tests keep `require_path_independence=True`. The s2-i4 guard is therefore a **caller** property of `guo_iterated_rescore.py` (and of the enumerator putting the substitution in `substitutions`), not a schema invariant that “two PATH_ZERO disjoint pairs are never a family.”

That is the sharpest composition residual on this track. It does not refute the close claim: the frozen composer **does** pass the UNKNOWN substitution in, and the family is `FAMILY_UNKNOWN`.

---

## 4. Attack reconstructions (what would be a false FAMILY_ZERO)

Executed against schema + falsifier. None of these succeed on the code as merged.

| id | attack | blocked by |
|---|---|---|
| A1 | one PATH_ZERO, ignore the other path | missing cons + `require_path_independence=True`; V3J_01 also has PATH_NONZERO → FAMILY_NONZERO |
| A2 | both iterated orders PATH_ZERO for `x/(x+y)`, skip consistency | V3J_02 computes `INCONSISTENT_NONZERO`; schema → FAMILY_NONZERO. Lying `CONSISTENT_ZERO` **does** yield FAMILY_ZERO — that is the documented attack, not a pass (`test_order_dependent_case_is_not_family_zero`) |
| A3 | 2/3 or 4/5 PATH_ZERO | all-quantifier; V3J_08; generic `neg-majority-unknown` |
| A4 | timeout / size-guard as ZERO | edge `_sanitize`, rescore `_budgeted`, auditor, opaque falsifier steps |
| A5 | empty path as PATH_ZERO | `compose_path_verdict([]) == PATH_UNKNOWN` |
| A6 | polar sibling ignored | V3J_03 PATH_NONZERO on the pole (directional / infinite) |
| A7 | skip corrupted intermediate | V3J_04 reconstruction NONZERO + path PATH_NONZERO |
| A8 | residual 0 only on `y=x` | V3J_05 identity PATH_NONZERO; surface-restricted residual is recorded as the trap, not the certificate |
| A9 | one repeated-node coalescence | V3J_06 PATH_NONZERO companion |
| A10 | local kernel PATH_ZERO, wrong spectator | V3J_07 reconstruction NONZERO |
| A11 | **s2-i4 omit substitution** | **would succeed** if rescore dropped `required_edge_verdicts`; does not succeed on the frozen call |
| A12 | vacuous empty `path_verdicts` + edge ZERO + `CONSISTENT_ZERO` | **schema returns FAMILY_ZERO** (see §5). Not used by rescore, falsifier, or tests |

Positive controls `V3J_POS_commuting_iterated_linear` and `V3J_POS_commuting_cubic_nodes` remain `FAMILY_ZERO` with `CONSISTENT_ZERO`. The suite is not an always-NONZERO gate.

---

## 5. Residual holes (do not currently promote frozen Guo)

Ranked by how easily a later composer could mint a false `FAMILY_ZERO`.

**R1. `require_path_independence=False` + omitted required edges (s2-i4-shaped).** Schema will certify two disjoint `PATH_ZERO` paths as `FAMILY_ZERO` with no consistency and no substitution. Frozen rescore avoids this only by passing `sub_verdicts`. Add a schema unit test:

```python
compose_family_verdict(
    path_verdicts=[PATH_ZERO, PATH_ZERO],
    consistency_verdicts=[],
    reconstruction_verdicts=["ZERO"],
    required_edge_verdicts=["UNKNOWN"],   # substitution
    require_path_independence=False,
) == FAMILY_UNKNOWN
```

and the omission twin (`required_edge_verdicts=[]` → `FAMILY_ZERO`) as a documented trap, analogous to V3J_02’s lying-consistency test.

**R2. Vacuous path list.** `all(_is_path_zero(v) for v in [])` is true. With `required_edge_verdicts=["ZERO"]`, `reconstruction_verdicts=["ZERO"]`, `consistency_verdicts=[CONSISTENT_ZERO]`, `require_path_independence=True`, schema returns `FAMILY_ZERO` with **no paths**. Empty *steps* are `PATH_UNKNOWN`; empty *path list* is not. Fail-closed fix: if `require_path_independence` or the V3 claim is path-shaped, empty `path_verdicts` should be `FAMILY_UNKNOWN` even when edges are ZERO.

**R3. Verdict aliasing.** `_is_path_zero` accepts `ZERO` as well as `PATH_ZERO`. `_is_consistent_zero` accepts `ZERO` as well as `CONSISTENT_ZERO`. Passing leftover edge `ZERO` strings as consistency yields `FAMILY_ZERO`. `family_zero_blocked(["ZERO"], True)` is **True** (blocks), so the helper and the schema disagree. Callers today pass the named consistency constants; still a confused-deputy hole.

**R4. Rescore hardcodes `reconstruction_verdicts=["ZERO"]`.** Family-level branch reconstruction is never checked in the Guo composer. Acceptable for existing-members-only lattices (no invented intermediates; I-E does not hold). Poisonous if a later enumerator inserts reconstructed mids and the rescore is reused unchanged.

**R5. Covering-path filter.** Family path verdicts use `n_steps >= 2` when any such path exists, else all paths. On the frozen 5-branch graphs every one-step edge appears inside a two-step covering path, so a NONZERO/UNKNOWN one-step still poisons a covering path. A later enumerator that added a one-step edge *not* on a covering path could drop it from composition. s2-i4 has only one-step paths, so the fallback keeps both PATH_ZERO paths.

**R6. Generic suite hardcodes consistency.** Case A stamps `CONSISTENT_ZERO` with the comment “polynomial; orders agree at a point.” Case B stamps `INCONSISTENT_NONZERO` rather than calling `check_two_paths`. Fine as a fixture for the composer; it is not evidence that production Guo composition uses the auditor. It does not.

None of R1–R6 produce `FAMILY_ZERO` on `GUO_ITERATED_RESCORE.json` or on `run_cases()`.

---

## 6. Closed-track claims vs this audit

`TRACK_V3_CLOSED.md`:

- false FAMILY_ZERO = 0 (generic suite) — **confirmed** (`GENERIC_SUITE.json`, `test_generic_suite_false_family_zero_is_zero`).
- order-dependent `x/(x+y)` is FAMILY_NONZERO — **confirmed** (suite B, V3J_02, auditor).
- majority PATH_ZERO + UNKNOWN is FAMILY_UNKNOWN — **confirmed**.
- spectator `h1` cubic kernel FAMILY_ZERO — **confirmed** (suite G).
- adversarial falsifier false FAMILY_ZERO = 0 — **confirmed** (10 rows).
- frozen Guo 7× FAMILY_UNKNOWN, case I-D — **confirmed**.
- s2-i4 2 PATH_ZERO + UNKNOWN substitution stays FAMILY_UNKNOWN — **confirmed** on the artifact; **not** schema-enforced without `required_edge_verdicts`.
- Track D2 locked — **no FAMILY_ZERO / FAMILY_NONZERO on a frozen family**; this audit does not unlock it.

---

## 7. Recommendation

- Accept the composition close: PATH_ZERO is not FAMILY_ZERO; majority cannot certify; timeout/size-guard cannot become ZERO; `require_path_independence=True` fail-closes missing consistency; s2-i4 as actually composed is FAMILY_UNKNOWN.
- Do not treat `require_path_independence=False` as a safe default. The certificate default is True; the Guo rescore’s topology heuristic is the only production `False`.
- Optional tightenings if this composer is reused (not required to keep D2 locked): reject empty `path_verdicts` as `FAMILY_UNKNOWN`; stop aliasing `ZERO` as `CONSISTENT_ZERO`; unit-test the s2-i4 substitution shape; stop hardcoding reconstruction ZERO in the rescore; run `check_two_paths` when two covering paths share endpoints instead of inferring `CONSISTENT_ZERO` from PATH_ZERO labels.

**R4 sign-off.** Composition soundness holds for the frozen track and the attack suite. The remaining false-FAMILY_ZERO surface is caller error (`False` independence + dropped required edges, or vacuous empty path lists), not a live promotion of Guo 5-branch or s2-i4.
