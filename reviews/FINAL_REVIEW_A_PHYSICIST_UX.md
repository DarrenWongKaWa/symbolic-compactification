# Final Re-review A — Theoretical-Physicist UX

Reviewed head: `495600883a392b5882f020b6e8a5eb016bd78a7b`

This was an independent release rejection audit of the bounded Mode A
researcher workflow. I inspected the final clean-room replay, installed the
exact reviewed head into a fresh Python 3.12 environment, ran the
`release_critical` group, replayed Demo B through the installed CLI, inspected
its generated report and provenance, exercised a freshly initialized Mode A
workspace, and checked user-source hashes before and after the workflow. No
production or scientific file was edited by this review.

## Verdict

`INTERNAL_ONLY`

## Release blocker

### The public workspace does not fail closed on the documented `real: false` namespace defect

The final documentation accurately names the defect: `real: false` can become
SymPy's **provably non-real** assumption instead of the historical contract's
unconstrained-complex/probe-selection meaning. `LIMITATIONS.md` says affected
claims must fail closed, and `WORKSPACE_FORMAT.md` repeats that they do.

The public workspace nevertheless accepts `real: false`, passes it directly
to `sympy.Symbol(..., real=False)`, runs verification, and can return `ZERO`
with no warning. I reproduced this from a fresh initialized workspace using:

```yaml
symbols:
  - name: x
    real: false
    nonzero: false
functions: []
```

with the obligation

```text
current   = Piecewise((1, Eq(x, 0)), (0, True))
candidate = 0
```

The installed CLI returned `ZERO`; the generated report recorded
`"real": false`, printed `Warnings: None`, and stated that the declared
`real` flag had been machine-applied. Under the encoded provably-non-real
domain, `Eq(x, 0)` collapses to false. Under the intended unconstrained complex
domain, however, `x = 0` is admitted and the two expressions differ. Thus the
verdict is driven by exactly the unresolved interpretation defect the public
docs say must fail closed.

This is not merely incomplete assumption discovery. It is a supported
workspace field whose accepted value silently narrows the domain and can
change the verdict. A theoretical physicist should not have to rely on having
read a warning to prevent a configuration that the tool itself accepts and
certifies without a run warning. That conflicts with the alpha's core
fail-closed and no-hidden-assumption promises.

Required engineering resolution: at the v0.1 researcher-workspace boundary,
reject `real: false` with a stable non-success status until its semantics are
repaired, or introduce an unambiguous machine representation for an
unconstrained complex symbol. Add a `release_critical` regression using a
domain-sensitive expression such as the one above, and ensure the generated
report cannot show warning-free `ZERO` through the defective path. This can be
fixed in the workspace facade without reopening scientific research or
changing frozen evidence.

## Checks that passed

| Area | Result | Evidence |
|---|---|---|
| Fixed Demo B | PASS | Installed `inspect`/`verify`/`report` returned one exact `ZERO` for the fixed nodes `10/9` and `25/9`; the report exposes the rational substitution, single obligation, fixed member paths, and source hashes. The submitted expression has no variable node-coincidence path. |
| Demo B claim boundary | PASS | Project objective, hypothesis, notes, references, demo guide, and final clean-room report consistently call it one fixed specialization, not the full C9H4 family, search success, or AI discovery. |
| Mode A usability | PASS | A fresh `init` workspace supported `inspect`, `verify`, and `report` without a proposer or API key and produced a readable exact-equivalence report. |
| Source grounding | PASS within advertised scope | Obligations are bound to exact expression members; notes/references are hashed context and are explicitly not treated as proof or as operational assumptions. |
| Source immutability | PASS | Byte-hash manifests of every non-`runs/` Demo B input were identical before and after installed-CLI inspection, verification, and report generation. |
| Verdict semantics | PASS except for the blocker above | ZERO/NONZERO/UNKNOWN and parse/compile/declaration failures are distinct; UNKNOWN is documented as neither likely true nor likely false and never promotable. |
| Assumption-surface disclosure | PASS as prose | Workflow entry points and reports now say that only `real`/`nonzero` flags and function declarations are machine-applied and that `ASSUMPTION_REQUIRED` is not assumption discovery. |
| Release-critical tests | PASS | Independent exact-head replay: `16 passed in 14.85s`. The group lacks a regression that enforces fail-closed behavior for `real: false`. |
| Final clean-room evidence | PASS as reproducibility evidence | The final replay documents fresh ordinary and wheel installs, three demos, artifact/hash integrity, source immutability, and secret scans. It does not exercise the unresolved `real: false` path. |

## Conclusion

The Demo B and assumption-documentation blockers from the first physicist
review are otherwise resolved. The remaining defect sits on the release's
central trust boundary: a documented-invalid domain encoding is accepted and
can produce a warning-free certification. Until the public workspace enforces
the stated fail-closed policy, the theoretical-physicist UX is not safe enough
for `RESEARCH_PREVIEW_ALPHA`.

`INTERNAL_ONLY`
