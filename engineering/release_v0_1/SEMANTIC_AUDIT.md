# Fail-Closed Semantic Audit

This audit covers the external researcher-workspace API and CLI at the v0.1
engineering integration head. It changes no verifier mathematics and does not
reopen any frozen scientific experiment.

## Public result matrix

| Result | Exact user meaning | CLI exit | Proof obligations executed | Can certify or promote? |
|---|---|---:|---:|---:|
| `ZERO` | Every declared equivalence obligation was certified exactly under the declared engine namespace and assumptions. | 0 | yes | yes, for the submitted relation only |
| `NONZERO` | At least one obligation was exactly refuted by the verification route. | 2 | yes | no |
| `UNKNOWN` | The verifier could not decide at least one non-refuted obligation. This is neither likely true nor likely false. | 3 | yes | no |
| `PARSE_FAILURE` | Workspace metadata or a declared source could not be safely parsed. | 4 | no | no |
| `COMPILE_FAILURE` | The readable hypothesis is outside the supported v0.1 equivalence-obligation language. | 4 | no | no |
| `ASSUMPTION_REQUIRED` | The hypothesis omitted a symbol already declared by the researcher in the assumptions source. The tool does not add it silently. | 4 | no | no |

The result value is persisted identically in `result.json` and
`provenance.json`. Reports repeat the result and its non-marketing semantic
meaning. Only `ZERO` receives process exit 0 from `verify`.

## Findings and disposition

1. `ZERO`, `NONZERO`, and `UNKNOWN` were already distinct exact verifier
   outcomes. Composite hypotheses remain `ZERO` only when every obligation is
   `ZERO`; a proven `NONZERO` refutes the composite, and otherwise any
   non-`ZERO` obligation yields `UNKNOWN`.
2. `UNKNOWN` already used exit 3 and the report explicitly prohibited
   scientific promotion. The release gate now checks both CLI JSON and report
   text for accidental success language.
3. Unsupported hypothesis types and relations already stopped at
   `COMPILE_FAILURE` without running an obligation. This behavior is pinned in
   the release gate.
4. A public-schema mismatch existed for `ASSUMPTION_REQUIRED`: provenance and
   documentation named it, but researcher-workspace verification could not
   emit it. Omission of a declared symbol from `assumptions_used` was reported
   as generic hypothesis schema failure. It now returns the public
   `ASSUMPTION_REQUIRED` result with stable error code
   `DECLARED_ASSUMPTIONS_OMITTED`, records a run, executes no obligation, and
   exits 4.
5. The tool still does not infer that a new positivity, nonzero, boundary,
   symmetry, or limit-order assumption is mathematically needed. An
   undeclared expression name remains `PARSE_FAILURE`; an undecidable relation
   under the available declarations remains `UNKNOWN`. This is intentional:
   inference would require new scientific semantics.
6. Parse, compile, and assumption gates persist bounded codes and hashes, not
   raw exception details. Credential-shaped malformed input is absent from run
   artifacts.
7. Workspace verification writes only under `runs/<run_id>/`; source-byte,
   modification-time, and mode snapshots are unchanged by inspect, verify, and
   report flows.

## Permanent retraction boundary

The release-critical group directly replays the historical safety invariant:

```text
negative Laurent coefficients ZERO
+ constant coefficient ZERO
+ remainder UNKNOWN
= final UNKNOWN at LEVEL_B, never ZERO
```

Finite Laurent coefficients therefore cannot certify an exact limit without
remainder control. The existing broader remainder regressions also pass.

## Release-critical test group

The registered `release_critical` marker is owned by
`tests/test_release_critical.py` and covers:

- workspace initialization and clean parsing;
- CLI inspection smoke behavior;
- `ZERO`, `NONZERO`, and intentional `UNKNOWN`;
- `PARSE_FAILURE`, `COMPILE_FAILURE`, and `ASSUMPTION_REQUIRED`;
- provenance persistence and deterministic SHA-256 evidence;
- researcher-source immutability;
- secret redaction from failed-input artifacts;
- report regeneration; and
- the finite-Laurent remainder retraction boundary.

The exact release command avoids importing unrelated optional-extra test
modules before marker selection, so it remains a fast core-install gate:

```bash
python -m pytest -q -m release_critical
```

Result on Python 3.12.13: **11 passed in 5.88s**.

Affected safety/API/CLI/workspace/demo/session/remainder suites:
**103 passed in 27.90s**.

## Blockers

None within the E7 error-semantics and fail-closed scope.
