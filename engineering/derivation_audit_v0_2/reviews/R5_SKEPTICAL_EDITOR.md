# R5 — Skeptical editor (derivation-audit v0.2)

## Verdict

**ALPHA_READY**

I would accept this as an **honest research-preview product** for
machine-auditable derivation verification. I would not accept it as a
paper-prover, a formal proof assistant, a “every step certified” checker,
or an autonomous theorist — and the public contract does not ask me to.

This is an editorial/engineering decision. No scientific line was reopened.
No unpublished manuscript was read or used.

## Reviewed SHA

Integration HEAD: `ff40d0ec6a8655c32d84ae7b3d901fe76e1c9935`
(`engineering/derivation-audit-v0.2`, also `work/da-r5-review`).

Package identity at this commit: `symbolic-compactification 0.1.0-alpha`
(PEP 440 `0.1.0a0`; engine `0.3.0`; agent protocol `0.3.0`; derivation-audit
protocol `0.2.0`). The README states this layer is **not** a stable v1.0
and is **not** merged to `main`. That preview posture is honest.

Independent install: ordinary non-editable `pip install` of this worktree
into a new CPython 3.12 venv at `/tmp/ssc-da-r5-replay/venv`. Demos were
copied to `/tmp/ssc-da-r5-replay/demo{A,C}` before `audit verify` /
`table` / `report`. Committed demo inputs were not overwritten.

No production code, tests, frozen research, or demo source was edited by
this review. This file is the only deliverable.

## Question

Would a skeptical editor ship this as a research preview without inflating
the claim?

**Yes**, provided the public claim surface remains the generated tables
and `REPORT.md`, not the `audit verify` command-status token (see
non-blocking finding N1).

## Must-not-claim check

Required denials (must not be product claims):

| Forbidden claim | User-facing v0.2 surface |
|---|---|
| AI proves your paper | Absent. Present only as a `FORBIDDEN_PUBLIC_CLAIMS` guard in `audit/schema.py`. |
| formal proof assistant | Absent from README / `docs/DERIVATION_AUDIT.md` / limitations / demos. README denies “universal theorem prover”. |
| every step certified / every manuscript step can be certified | Absent. Docs state the opposite: inventory is not mathematics; `NOT_LOWERED` / `UNKNOWN` are normal; a package is not a manuscript proof. |
| autonomous theorist / autonomous theoretical physicist | Absent from the v0.2 lede. Capability boundary still denies “substitute for a scientist”. |

`tests/test_audit_docs_claims.py` (release-critical) forbids
`FORBIDDEN_PUBLIC_CLAIMS` in `README.md` and `docs/DERIVATION_AUDIT.md`.
Generated tables/report refuse those phrases at write time
(`FORBIDDEN_PUBLIC_CLAIM`).

Positive denials that *are* present and should stay:

- “This tool does not write papers.”
- “This layer does not write papers and does not replace a human derivation.”
- “not a claim that a paper is proved.”
- “This report does not certify a manuscript as a whole.”

## Must-claim check

Required positioning:

| Required claim | Where it actually lives |
|---|---|
| machine-auditable derivation verification | CLI help: “machine-auditable derivation audit (additive v0.2 layer)”. README lede is the equivalent “Typed derivation audit with fail-closed exact verification.” Exact four-word slogan is not in the README headline (N2). |
| only executable ZERO is machine-verified | `APPROVED_MACHINE_CLAIM` is verbatim in README, `docs/DERIVATION_AUDIT.md`, `docs/DERIVATION_AUDIT_LIMITATIONS.md`, generated `REPORT.md`, and HTML banner. Schema inclusion is `status == result == ZERO` **and** `executable` **and** not `SPLIT_PARENT` / `ASYMPTOTIC_CLAIM`. |
| definitions / integrals / asymptotics tracked separately | `APPROVED_CAVEAT` is verbatim in the same user docs and in generated `REPORT.md` / HTML. `DEFINITION` → `TABLE_STRUCTURAL`; `INTEGRAL_ARGUMENT` / `ASYMPTOTIC_CLAIM` → `TABLE_UNCERTIFIED`. |

I treat the **substance** of the required claims as satisfied. I would
still prefer the README headline to say “machine-auditable” out loud
(N2). That is not a blocker: the approved paragraphs are already on the
first screen.

## TABLE generation (authoritative surface)

Read `src/symbolic_compactification/audit/tables.py`, `schema.py`,
`report.py`, and `tests/test_audit_tables.py`.

Inclusion is generated, not authored:

- `schema.may_appear_in_verified_table` and `schema.table_bucket` are the
  only inclusion functions.
- Markdown `ZERO` is ignored. Regenerating tables after a forged
  `LLM_FORGED` / `FORGED_ZERO` row restores the machine set
  (`test_forged_markdown_zero_is_restored_from_machine_records`,
  `test_forged_markdown_zero_is_ignored_on_regeneration`).
- Integrity-fail records cannot enter `TABLE_VERIFIED` even if labels
  say `ZERO`.
- `ASYMPTOTIC_CLAIM` is excluded from `TABLE_VERIFIED` even if a
  remainder hash were later attached. Finite coefficient `ZERO` is not a
  remainder proof.
- `SPLIT_PARENT` cannot be engine `ZERO`. `CERTIFIED_BY_CHILDREN`
  displays as `SPLIT — all children certified`.
- `TABLE_NONZERO` is titled “POTENTIAL DERIVATION MISMATCHES” and tells
  the reviewer to check transcription/assumptions/conventions — it does
  not say “the paper is wrong.”

Independent Demo A replay (install CLI): two `ALGEBRAIC_EQUIVALENCE`
rows in `TABLE_VERIFIED`; counts
`TABLE_VERIFIED=2`, others 0.

## Demo C — coefficient ZERO, remainder UNKNOWN

This is the soundness demo. If it had promoted `F(g)=a/g+O(g)` to
`TABLE_VERIFIED`, this review would be **BLOCKED**.

Copied workspace: `/tmp/ssc-da-r5-replay/demoC`.
Installed CLI `audit verify` then `audit table` then `audit report`.

| Edge | Type | `status`/`result` | Table | `executable` | `may_appear_in_verified_table` |
|---|---|---|---|---|---|
| `C.coeff-g-inv` | `LAURENT_COEFFICIENT` | `ZERO` | `TABLE_VERIFIED` | true | true |
| `C.coeff-g0` | `LAURENT_COEFFICIENT` | `ZERO` | `TABLE_VERIFIED` | true | true |
| `C.asymptotic-O` | `ASYMPTOTIC_CLAIM` | `UNKNOWN` | `TABLE_UNCERTIFIED` | false | false |

`C.asymptotic-O` is **absent** from `TABLE_VERIFIED.md` and **present**
in `TABLE_UNCERTIFIED.md`. `remainder_certificate_hash` is null. Residual
cell is empty. The parent is not rewritten as `F-a/g=0`.

Lowering never executes `ASYMPTOTIC_CLAIM` (`_NEVER_EXECUTABLE_TYPES`).
Evidence additionally refuses engine `ZERO` on that type without a
remainder certificate. Table inclusion excludes the type unconditionally.

`REPORT.md` repeats the approved machine claim and caveat, lists the two
coefficient identities under “Machine-verified identities”, and lists
the remainder under “Uncertified / asymptotic / integral”:
“Finite coefficient identities do not certify an enclosing asymptotic
remainder.”

That is the honest product.

## Blocking findings

None.

## Non-blocking editorial / engineering notes

These do **not** withhold `ALPHA_READY`. Fix them before a noisy public
announcement if cheap; do not expand scientific scope to “close” them.

### N1 — `audit verify` status token `AUDIT_VERIFIED` (leading nit)

On Demo C (remainder `UNKNOWN`), installed CLI printed
`{"status": "AUDIT_VERIFIED", "records": 3, ...}` and exited **0**.

Mode A treated authentic `UNKNOWN` as exit 3 / not success. Multi-edge
audit cannot collapse to a single ZERO/NONZERO/UNKNOWN without losing
information, so pipeline-complete exit 0 is defensible — **if** the
status token does not sound like a scientific verdict.

`AUDIT_VERIFIED` sits in a family of command-complete tokens
(`AUDIT_INITIALIZED`, `AUDIT_TABLES`, `AUDIT_REPORT`) but is the one
word a hurried reader will over-read. JSON also omits ZERO / UNKNOWN /
NONZERO counts.

Recommendation (engineering, not science): rename to
`AUDIT_RUN_RECORDED` (or equivalent), emit per-status counts, and keep
tables/`REPORT.md` as the only claim surface. Do not teach users that
exit 0 means the derivation was proved.

I still accept the preview because the documented workflow is “read
`TABLE_VERIFIED.md`”, and those tables are honest.

### N2 — README headline vs required slogan

README does not use the exact words “machine-auditable derivation
verification”. CLI help does (“machine-auditable derivation audit”).
The approved machine-claim and caveat paragraphs **are** in README.
Optional: put “machine-auditable” in the first sentence.

### N3 — PyPI short description is still Mode A

`pyproject.toml` `description` remains “Context-grounded symbolic
hypotheses with fail-closed verification.” Long description is the
current README. Packaging nit, not a false theorem.

### N4 — Demo C coefficient residuals are toy algebraic identities

`C.coeff-g-inv` residual is `g*(a/g + b*g) - a - b*g**2` (the whole
finite polynomial, not a series-coefficient operator). `C.coeff-g0` is
`F(g)+F(-g)`. Fine for a table-inclusion soundness demo; do not let
marketing describe this as a general Laurent engine.

## Gate assessment (editorial)

| Gate | Result |
|---|---|
| `DOCUMENTATION` | PASS — required claims present; forbidden claims absent |
| `ANTI_HALLUCINATION` | PASS — tables generated from `may_appear_in_verified_table` / `table_bucket`; markdown ZERO ignored |
| `TABLE_GENERATION` | PASS — four buckets, forged rows restored from records |
| `PUBLIC_DEMOS` | PASS — Demo C remainder stays `UNKNOWN` / `TABLE_UNCERTIFIED` |
| `VERIFIER_AUTHORITY` | PASS — only executable engine ZERO is machine-verified |
| `STATUS_SEMANTICS` | PASS — definitions/integrals/asymptotics tracked separately |
| `PRIVACY` | PASS for this review — no unpublished sources used; demos labelled synthetic |
| `CLI` | PASS with N1 — command works; status token is sloppy, not a false ZERO |

Targeted tests on the independent interpreter:
`tests/test_audit_docs_claims.py`,
`tests/test_derivation_audit_release_critical.py`,
`tests/test_audit_tables.py`,
`tests/test_audit_public_demos_static.py`,
`tests/test_audit_schema.py` → **34 passed**.

Recorded clean-room replay at this branch
(`engineering/derivation_audit_v0_2/CLEAN_ROOM_REPLAY.md`, commit
`c85a703`) is consistent with this Demo C observation. This review did
not re-run the full clean room.

## What I would print on the box

Allowed:

> Research preview: machine-auditable derivation verification. Only
> executable residuals that the deterministic verifier returns as exact
> ZERO are listed as machine-verified. Definitions, integral-level
> arguments, asymptotic remainder claims, and unsupported
> transformations are tracked separately.

Not allowed (and currently not claimed):

> AI proves your paper. Formal proof assistant. Every step certified.
> Autonomous theorist.

## Verdict (repeat)

**ALPHA_READY**

I would accept this as an honest research-preview product.
