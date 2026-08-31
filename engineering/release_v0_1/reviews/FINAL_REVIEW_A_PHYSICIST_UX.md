# Final Review A — Theoretical Physicist UX

## Verdict

`ALPHA_READY`

## Reviewed SHA

Integration HEAD: `416867289f372f469be5ee8b72c948e48bf31821`
(`engineering/research-preview-alpha-v0.1`)

Product (production code) commit: `bd6f0a1ecb766526be3eb5cc596eeb337e4b69d0`
(ancestor of HEAD). Clean-room evidence commit is this HEAD.

Independent install: ordinary `pip install .` from this worktree into a fresh
CPython 3.12.13 venv at `/tmp/ssc-final-review-a-physicist-ux/venv` (not
editable). Installed identity: `symbolic-compactification 0.1.0-alpha`
(PEP 440 `0.1.0a0`; engine `0.3.0`, protocol `0.3.0`); SymPy `1.14.0`;
PyYAML `6.0.3`. Run provenance recorded
`416867289f372f469be5ee8b72c948e48bf31821-dirty` because this worktree had
unrelated local `STATUS.md` dirt and untracked files at build time. That
suffix is an install-hygiene note, not a scientific-domain defect.

No production code, frozen evidence, or demo source was edited by this
review. The older root file `reviews/FINAL_REVIEW_A_PHYSICIST_UX.md` was
left untouched.

## Blocking findings

None.

The two historical physicist-UX blockers are independently re-tested and
closed on the advertised Mode A workspace. I also hunted for new ways a
theoretical physicist could over-read `ZERO`, treat `UNKNOWN` as success,
or mistake notes/references for proof. Those hunts did not yield a Mode A
alpha blocker.

## Checks that passed

### 1. Demo B outside the checkout — one fixed-node `ZERO`

Copied `engineering/release_v0_1/demos/demo_b_grounded_newton_dd` to
`/tmp/ssc-final-review-a-physicist-ux/demo_b_grounded_newton_dd` and ran
the installed CLI:

```text
symbolic-compactification inspect <copy>
symbolic-compactification verify  <copy>   # exit 0
symbolic-compactification report  <copy>
```

Observed:

- exactly one obligation, `Q9H1_FIXED_NONSINGULAR` → `ZERO`;
- inspect/report source text and hypothesis `instance_maps`/`reconstruction_rule`
  name the fixed nodes `10/9` and `25/9` (difference `5/3`);
- project objective: "one fixed, source-grounded, nonsingular rational
  instance";
- notes state it is **not** a discovery result and **does not** certify the
  full symbolic `C9H4` family;
- report semantics: `ZERO` certifies declared obligations under declared
  engine semantics and assumptions; notes/references are hashed metadata
  only; machine-applied assumptions are `real: true` / optional `nonzero` /
  declared functions;
- report warnings: none; simplified residual: `0`;
- no "AI discovers", search-success, or full-family certification language
  in inspect, CLI verify, or `REPORT.md`.

### 2. Demo B source immutability

SHA-256 of every non-`runs/` Demo B file, committed tree vs copy before CLI
vs copy after inspect/verify/report:

| path | sha256 |
|---|---|
| `assumptions/assumptions.yaml` | `dae7a70c1becc57bbd43e5279588e22c4a74f057da4462c6293f926dc11683b1` |
| `expressions/m9h1_fixed_newton_dd.txt` | `4c2f2874d5ddf38927f7d1ba8e53c345c8e6565f5ad1aab664ff5869af0a3c45` |
| `expressions/m9h1_fixed_source.txt` | `163682b4a066c0b8564773608b3d172820b00f5f3e9b10e313494629de07091a` |
| `hypotheses/hypothesis.json` | `ca46f99ed6cdda6665df5231705f582bb5d657144d20536cd2c50def32abb43b` |
| `notes/research_notes.md` | `b75349041c6c86d2573b48d6a4d461917c2c2002425b2d58e688a17baefe3672` |
| `project.yaml` | `59fae2e4b60865d274d0c5a5e4d4d322ef7a2d67979e131f4a49164594db730d` |
| `references/README.md` | `0fc66d1f259e5ad3c48d19f97a02c56fe9f5570aa720a7ae4228a4ea66dd2e29` |

Byte-identical in all three snapshots. Generated files existed only under
`runs/<run_id>/`.

The submitted members are constant-node identities in the single real
bookkeeping symbol `scale`. There is no remaining variable
node-coincidence path of the kind that previously certified a formal
cancellation off the declared scientific domain.

### 3. `real: false` piecewise attack — fail closed, no obligation

Workspace (Mode A) with:

```yaml
symbols:
  - name: x
    real: false
    nonzero: false
functions: []
```

```text
current   = Piecewise((1, Eq(x, 0)), (0, True))
candidate = 0
```

Installed workflow:

- `inspect`: exit 4; `error: UNSUPPORTED_COMPLEX_SYMBOL_SEMANTICS`; source
  `assumptions/assumptions.yaml`; no scientific verdict.
- `verify`: exit 4; `result: PARSE_FAILURE`;
  `error_code: UNSUPPORTED_COMPLEX_SYMBOL_SEMANTICS`;
  semantics: no scientific relation was checked; `obligations: []` in
  `result.json`; warning
  `workspace_parse_failure:UNSUPPORTED_COMPLEX_SYMBOL_SEMANTICS`.
- `report`: Result **PARSE_FAILURE**; action-required section names the
  same code; **not** warning-free `ZERO`.

Control with `real: true` on the same piecewise identity returned
`UNKNOWN` (exit 3), not `ZERO`. YAML `real: "false"` (string) is
`PARSE_FAILURE` / `ASSUMPTIONS_SCHEMA_INVALID`. Omitting `real` on a
declared symbol normalizes to `real: true` and is visible in `inspect`.

### 4. Fresh Mode A workspace from README / QUICKSTART

From a directory outside the checkout, using only the documented commands:

```text
symbolic-compactification init my-symbolic-project
symbolic-compactification inspect my-symbolic-project
symbolic-compactification verify my-symbolic-project
symbolic-compactification report my-symbolic-project
```

`init` refused no existing path and produced the documented tree. Inspect
showed `x**2 + 2*x + 1` vs `(x + 1)**2` with `real: true`. Verify returned
one-obligation `ZERO` (exit 0) with scoped semantics. The QUICKSTART Python
façade (`load_workspace` / `verify_hypothesis` / `generate_report`)
reproduced `ZERO` on the same workspace. No proposer, API key, or source
tree internals were required. `finalize --run <workspace-run-id>` failed
closed (`RUN_ID_INVALID`, exit 4) rather than minting a "FINAL CERTIFIED
FORM" from a workspace run.

### 5. Semantics, limitations, and claim boundary

Read `engineering/release_v0_1/SEMANTICS.md`,
`engineering/release_v0_1/LIMITATIONS.md`, `CAPABILITY_BOUNDARY.md`,
Demo B notes/references, the generated Demo B `ZERO` report, and the
generated Demo C `UNKNOWN` report.

| Attack | Result |
|---|---|
| Hidden operational assumptions | Machine surface is only `real: true`, optional `nonzero`, and declared functions. Reports restate that other predicates are not inferred or certified. Demo B no longer depends on unrepresentable positivity / distinct-node predicates. |
| `ZERO` meaning more than declared engine semantics | CLI and report: "exactly certified under the declared engine semantics and assumptions." Demo B objective/reconstruction_rule/notes bound the claim to one fixed instance, not the C9H4 family. |
| `UNKNOWN` presented as success | Demo C CLI: "this is not success and does not permit scientific promotion" (exit 3). Report: neither likely true nor likely false; no promotion. |
| Notes/references treated as proof | Report copies only path/hash/size; explicit sentence that contents are not copied and are not verifier proof. |
| Overselling representation invention | User docs state context-conditioned invention is unestablished. Forbidden marketing phrases appear only as denials. No workspace-level `propose` command is promised. |

### 6. `UNKNOWN` is first-class (Demo C)

Copied `demo_c_unknown` outside the checkout. Installed `verify` returned
`UNKNOWN`, exit 3, one obligation `polygamma-order-two-recurrence`, residual
unresolved. Report Result is **UNKNOWN** with non-promotion language.
Non-`runs/` source hashes were unchanged by inspect/verify/report.

## Non-blocking residual hazards

These did not meet the bar to keep Mode A alpha `INTERNAL_ONLY`. They are
recorded so they are not mistaken for unexamined paths.

1. **Legacy file-oriented / session Mode A still accepts `real: false`.**
   The same piecewise pair with `symbols.json`
   `{"name": "x", "real": false, "nonzero": false}` yields:
   - `verify --current --candidate --symbols` → `verdict: ZERO`, exit 0,
     no warning;
   - `init-session` + `step` → `verdict: ZERO`, `status: CERTIFIED`,
     `promoted: .../final/current.json`, `zero_promotions: 1`.
   The advertised v0.1 workspace rejects this setting, and README/QUICKSTART
   make the workspace the primary external interface. The historical CLI is
   labeled compatibility and uses JSON, not the workspace YAML gate. A later
   engineering pass could apply the same fail-closed rejection at
   `symbols.json` / session load without new science. It is not a Mode A
   workspace-contract regression.

2. **Workspace `verify` prints the unsimplified residual next to `ZERO`.**
   Demo B CLI residual is a non-obvious exact combination that the report
   then simplifies to `0`. Named result and report remain authoritative.

3. **`report` process exit is 0 even when the named result is
   `PARSE_FAILURE` or `UNKNOWN`.** `verify` exits 4 / 3 as required.
   SEMANTICS.md already ranks named status above report exit codes.

## Conclusion

I tried to reject this head on physicist-UX grounds and could not, on the
release-critical Mode A contract.

The earlier Demo B domain over-certification is gone: the shipped demo is
one denominator-safe specialization at nodes `10/9` and `25/9`, source-immutable
under the installed CLI, and does not claim discovery or the full C9H4
family. Assumption docs and generated reports now state the tiny machine
surface and refuse to treat notes, references, operators, or reconstruction
prose as proof. The documented `real: false` namespace defect no longer
produces warning-free `ZERO` on the public workspace: it is
`PARSE_FAILURE` / `UNSUPPORTED_COMPLEX_SYMBOL_SEMANTICS` with no obligation
executed. A physicist can complete install → `init` → `inspect` → `verify`
→ `report` from README/QUICKSTART. `UNKNOWN` remains a first-class,
non-promotable result (Demo C, exit 3).

The product may be called `RESEARCH_PREVIEW_ALPHA` from this
theoretical-physicist UX gate.

`ALPHA_READY`
