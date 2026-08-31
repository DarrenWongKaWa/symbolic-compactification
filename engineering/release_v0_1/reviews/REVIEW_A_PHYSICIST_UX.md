# Final Release Review A — Theoretical Physicist UX

## Verdict

`INTERNAL_ONLY`

The installed Mode A workflow is compact, reproducible, provenance-rich, and
source-immutable, but the current scientific-domain contract can still give a
physicist a success-like `ZERO` beyond the assumptions represented in the
workspace. That is release-critical for a tool whose defining promise is
fail-closed verification.

## Scope and evidence

This review examined integration head
`aca18646617c151d0914e739105ee1acf46d8d78`, including:

- the root and release quickstarts, workspace format, semantics, limitations,
  installation, and capability-boundary documents;
- the clean-room replay and final external-user retest;
- the full-suite triage and explicit release-critical tests;
- all three committed demo workspaces; and
- the workspace loader, equivalence compiler, verifier facade, report
  renderer, and CLI output.

A fresh ordinary Python 3.12 install from this worktree succeeded. I copied
Demo B outside the checkout and ran the installed `inspect`, `verify`, and
`report` commands. They returned four per-obligation `ZERO` verdicts and an
aggregate `ZERO`. A recursive comparison excluding `runs/` found no source
mutation.

## Release blockers

### 1. Demo B certifies a formal cancellation without preserving the declared scientific domain

Demo B's notes correctly state that the frozen source contract requires
positive and unequal squared-distance radicands and nonzero displayed
denominators. The machine-readable assumptions declare only real symbols, so
those conditions are absent from the operational run.

This is not merely a missing annotation. For obligation `Q9H1`, the declared
workspace permits the exact point

```text
alpha = 1
x1_old = x1_new = 0
x2_hold = 1
```

At that point the source expression evaluates to `-sqrt(2)/4`, while the
Newton divided-difference candidate evaluates to `nan` because its node
difference is zero. Nevertheless, the installed workflow reports `ZERO`.
The verifier has certified the simplified formal relation on a generic/common
domain; it has not certified equality of the submitted expressions' domains
or their removable extensions.

That distinction is not part of the public `ZERO` contract. The human report
says every obligation is certified under the declared assumptions, records
`Warnings: None`, and omits note contents, so the only explicit distinct-node
warning is unavailable to someone reviewing the report alone. The very long
raw residual further obscures the decisive `Simplified residual: 0` line.

This violates the alpha requirements for precise semantics, no hidden
scientific assumptions, and a report that does not mislead a field user.

Required engineering resolution: either use a grounded demo whose two sides
have compatible declared domains, fail closed when the required domain
condition is not representable, or make common-domain/formal-cancellation
semantics and the unverified domain-extension boundary explicit in both the
run record and prominent report warning. Add a release-critical regression
for a coincident-node substitution. This does not require reopening a
scientific experiment.

### 2. The public assumptions workflow promises more than the v0.1 schema can express

The quickstart tells researchers to declare every scientific/domain
assumption, and `SEMANTICS.md` discusses positivity, boundary behavior,
symmetry, integration by parts, and limit order. The actual v0.1 assumptions
schema supports only symbol names, `real`, `nonzero`, and undefined-function
names. It cannot encode positivity, inequalities, relations such as
`alpha + beta = 1`, excluded discrete pole sets, boundary conditions,
symmetry, or limit ordering. `ASSUMPTION_REQUIRED` only detects omission of a
symbol already listed in `assumptions.yaml`; it does not detect a missing
predicate.

The narrower operational trigger is disclosed in `SEMANTICS.md`, and the Demo
B/C notes acknowledge individual gaps, but the external workflow still tells
the researcher to perform an action the schema cannot represent. In the Demo
B case, verification proceeds to `ZERO` rather than making this limitation
visible in the report.

Required engineering resolution: state prominently at the workflow entry
point and in every report that v0.1 operational assumptions are limited to
the supported flags, distinguish machine-applied assumptions from contextual
domain notes, and do not describe unsupported predicates as if the user can
declare them operationally. Any obligation that depends on an unsupported
predicate must remain visibly scoped or fail closed.

## Checks that passed

| Area | Assessment | Evidence |
|---|---|---|
| Mode A workflow | PASS | A first-time user can install, initialize, inspect, verify, and report without an AI backend. |
| Source immutability | PASS | Direct replay changed only `runs/`; clean-room and E11 byte manifests agree. |
| Core verdict separation | PASS | `ZERO`, `NONZERO`, `UNKNOWN`, parse, compile, and assumption-gate statuses are distinct; Demo C correctly remains unpromoted. |
| Provenance | PASS | Reports identify source hashes, hypothesis/assumption hashes, versions, revision, route, runtime, and per-obligation evidence. |
| Reference handling | PASS within stated scope | References are explicitly lightweight, hashed context only, and never treated as proof or silently mined for assumptions. |
| Claim boundary | PASS | The docs reject AI-discovery, autonomous-physicist, universal-simplification, and general-proof claims. |
| Installation/replay | PASS | The clean-room lane reports an ordinary install, wheel install, 12 release-critical tests, and all three demos on Python 3.12. |
| Historical suite disclosure | PASS as disclosure | The 24 frozen-research failures are clearly separated from the release path; this review does not reinterpret them. |

## Non-blocking UX observations

- `inspect` is useful but the compact structural counters do not explain that
  `sums` and `products` mean explicit bound `Sum`/`Product` nodes.
- Large exact residuals can dominate both CLI and report output. A collapsed
  or separately stored raw residual would make the verdict and simplified
  residual easier to audit without discarding evidence.
- The report's reference inventory is adequate provenance for the advertised
  lightweight mode, but it is not a self-contained scientific citation
  record because only paths, hashes, and sizes are rendered. The docs state
  this accurately.

## Conclusion

The product shape is credible, and the basic researcher journey works. The
remaining blockers are narrower than a new evaluator or research campaign:
they concern the exact domain of what `ZERO` certifies and the operational
limits of the assumptions file. Until those are made fail-closed and visible
in the report, a theoretical physicist can reasonably read a certified result
more broadly than the engine has established.

`INTERNAL_ONLY`
