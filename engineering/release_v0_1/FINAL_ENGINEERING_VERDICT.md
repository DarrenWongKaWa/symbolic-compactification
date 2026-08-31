# Final Engineering Verdict — symbolic-compactification v0.1

Decision: **`RESEARCH_PREVIEW_ALPHA`**

## 1. What can the tool reliably do?

A theoretical physicist can create a small workspace, declare expressions and
a tiny assumption surface, register an equivalence hypothesis, and obtain an
exact `ZERO` / `NONZERO` / `UNKNOWN` result with hashes, versions, and a
human report. The verifier is the only judge. The workflow is useful even
when no AI proposer is present.

## 2. What can it not claim?

It cannot claim that AI discovers physics, that it is an autonomous
theoretical physicist, that it reliably invents representations, that it
always finds hidden structure, that it is a general formal proof system, or
that `ZERO` is a theorem beyond the declared engine semantics. Context-
conditioned representation invention remains unestablished.

## 3. Canonical researcher workflow

```text
init workspace → edit expressions/assumptions/hypothesis
  → inspect → verify → report under runs/<run_id>/
```

Mode A is release-critical. Mode B is experimental and not shipped as
`symbolic-compactification propose`.

## 4. Workspace format

Plain directory: `project.yaml`, `expressions/`, `notes/`, `assumptions/`,
`references/`, `hypotheses/hypothesis.json`, tool-owned `runs/`. No database
and no internal benchmark schema. A simple equivalence hypothesis may omit
`proof_obligations`; the loader then constructs one `equivalent` pair without
inventing scientific meaning. Parse failures return `PARSE_FAILURE`.

## 5. CLI surface

Required: `init`, `inspect`, `verify`, `report`. Default errors are stable
codes; `--debug` shows tracebacks. File-oriented inspect/verify and session
commands remain compatibility surfaces.

Exit codes: `ZERO` 0, `NONZERO` 2, `UNKNOWN` 3, parse/compile/assumption 4.

## 6. Python API

```python
from symbolic_compactification import (
    generate_report, load_workspace, verify_hypothesis,
)

workspace = load_workspace("my-symbolic-project")
run = verify_hypothesis(workspace)
report = generate_report(workspace, run)
```

`run.result` is one of `ZERO`, `NONZERO`, `UNKNOWN`, `PARSE_FAILURE`,
`COMPILE_FAILURE`, `ASSUMPTION_REQUIRED`. Fail-closed statuses are structured
results, not success-like exceptions. `propose_hypotheses(...)` is not part
of the v0.1 stable façade.

## 7. ZERO / NONZERO / UNKNOWN semantics

- `ZERO`: exact certification under declared engine semantics and assumptions.
- `NONZERO`: exact refutation of the submitted universal identity on that
  route.
- `UNKNOWN`: cannot decide; not likely true/false, not partial success, not
  promotion.
- Composite hypotheses certify only if every obligation is `ZERO`.

## 8. Provenance guarantees

Every run records timestamp, package/engine/protocol versions, git commit,
Python version, PyYAML/SymPy versions, input/expression/hypothesis/assumption
hashes, verifier route `python_sympy_exact_v1`, result, runtime, and
warnings. Metadata is hashed from the same immutable byte snapshot that was
parsed. Installed builds embed the source checkout SHA.

## 9. Security / secret handling

No `.env` load, no environment inventory, no auth-header capture. Credential-
shaped values are redacted. Reports are regenerated from bounded
`result.json`/`provenance.json`; symlink and forged reports fail closed
without emitting attacker content.

## 10. Source-file immutability

`init` never overwrites an existing path. `inspect`/`verify`/`report` do not
rewrite researcher sources. Generated files live only under `runs/<run_id>/`.

## 11. Demo A result

Exact factorization `x**2 + 2*x + 1` vs `(x + 1)**2`: **`ZERO`**, verify
exit 0. Clean-room inspect/verify/report: 0.14 s / 0.56 s / 0.14 s.

## 12. Demo B result

One fixed Newton-DD specialization of frozen C9H4/M9H1 at nodes `10/9` and
`25/9`: **`ZERO`**, verify exit 0. Not a discovery claim and not the full
family. Clean-room verify 0.62 s.

## 13. Demo C result

Order-two polygamma recurrence vs `2/z**3`: **`UNKNOWN`**, verify exit 3.
Report states it is neither likely true nor likely false and does not permit
promotion. Clean-room verify 2.65 s.

## 14. Clean install result

PASS. Fresh CPython 3.12 ordinary `pip install .[dev]` and wheel install;
import origin site-packages; `0.1.0-alpha` / `0.1.0a0`; engine/protocol
`0.3.0`; PyYAML 6.0.3; SymPy 1.14.0; `pip check` clean; both entry points
work. Wheel SHA-256 (build instance):
`0d4842d0ab4b4342e65aeddf0aa73c7e4eb8708f8c2e7b97448559ccc21d578c`.

## 15. Release-critical test result

`python -m pytest -q -m release_critical` → **17 passed** (clean-room 9.36 s;
coordinator 9.63 s; Reviewer B 9.69 s).

## 16. Full-suite result

Authorized one-run result: **2049 passed, 24 failed**. Failures are frozen
RPS/SOL authority drift, one optional LLM client, and historical `__pycache__`
enumeration. Not green. Not repaired. Disclosed in `FULL_SUITE_RESULT.md`.

## 17. Clean-room replay result

`ALPHA_READY` at `bd6f0a1`. Demos ZERO/ZERO/UNKNOWN, provenance match,
immutability PASS, secret scan 0 hits, symlink/forged-report attacks PASS,
wheel outside-checkout PASS. Evidence:
`engineering/release_v0_1/CLEAN_ROOM_HEAD_REPLAY.md`.

## 18. External-user simulation

Final E11 retest at an earlier HEAD was `ALPHA_READY`. Final physicist UX
review at this product SHA independently completed install → init → inspect
→ verify → report from README/QUICKSTART without internals. Remaining
non-blocking friction: legacy `symbols.json` still accepts `real: false`;
CLI prints unsimplified residual next to `ZERO`; `report` process exit is 0
even when the named result is `UNKNOWN`/`PARSE_FAILURE` (named status is
authoritative).

## 19. Known limitations

Incomplete verification coverage; `UNKNOWN` common; unestablished
representation invention; tiny assumption schema; exactness is
engine-relative; hard special-function limits often undecidable; proposer
outputs speculative; remainder control required for exact limits; lightweight
references; tested platform is CPython 3.12 / macOS arm64.

## 20. Capability boundary

See `CAPABILITY_BOUNDARY.md`. Supported: exact adjudication in covered
domains, grounding, provenance, structured observations, reproducible runs.
Experimental: AI proposal. Unsupported: robust invention, universal
simplification, general exact limits.

## 21. Reviewer verdicts

| reviewer | verdict |
|---|---|
| A theoretical-physicist UX | `ALPHA_READY` |
| B software/reproducibility | `ALPHA_READY` |
| C safety/claim-boundary | `ALPHA_READY` |

## 22. Final engineering decision

**`RESEARCH_PREVIEW_ALPHA`**

Readiness: INSTALL, CLI, PYTHON_API, WORKSPACE, PROVENANCE, FAIL_CLOSED,
SECURITY, DEMOS, DOCS, REPRODUCIBILITY all `PASS`. No critical `FAIL`.

## 23. Exact commits / tag

- Product SHA: `bd6f0a1ecb766526be3eb5cc596eeb337e4b69d0`
- Branch: `engineering/research-preview-alpha-v0.1`
- Tag: `research-preview-v0.1.0-alpha` (local; not published unless policy
  allows)

## 24. Next engineering action

Do not reopen scientific experiments. Optional later engineering: apply the
workspace `real: false` rejection to the legacy `symbols.json` / session CLI
so compatibility mode cannot warning-free-certify the documented namespace
defect.
