# Final Release Review C — Safety and Claim Boundary

Verdict: `INTERNAL_ONLY`

Reviewer scope: independent safety/claim-boundary review of integration HEAD
`aca18646617c151d0914e739105ee1acf46d8d78`, whose production release code is
unchanged from clean-room-tested commit
`eb02da4ee06f9d8d523b82a526dbdb317050588c`.

This is an engineering release decision, not a scientific verdict. The
scientific lines remain closed.

## Blocking findings

### 1. Existing report symlinks bypass the bounded run-artifact boundary

`generate_report()` proves that the selected run directory is real and inside
`runs/`, but it does not apply the same final-component rule to `REPORT.md`.
When that path exists, it calls `read_text()` directly and returns the bytes as
the authoritative human report. It also trusts an existing report instead of
deriving it again from the persisted result and provenance records.

An adversarial replay used a genuine Demo C run whose persisted result was
`UNKNOWN`, replaced only its generated `REPORT.md` with a symlink to a file
outside the workspace, and invoked both the Python API and public CLI. The
observed facts were:

```text
authentic run result:       UNKNOWN
generate_report result:     UNKNOWN
returned report says:       Result: **ZERO**
external private canary:    returned by API and printed by CLI
report CLI exit:            0
```

The generic output redactor did not remove the arbitrary canary, as expected:
it is defence in depth for recognizable credential shapes, not a filesystem
confinement mechanism. This path can therefore disclose an arbitrary readable
local file and, independently, show a success-like report for an authentic
`UNKNOWN` run. That violates both `SECURITY` and `FAIL_CLOSED` release gates.

Required acceptance evidence before alpha:

- reject symlinks and non-regular files for `provenance.json`, `result.json`,
  and `REPORT.md`;
- never trust pre-existing report prose as the source of truth—regenerate it
  from fully validated bounded records, or verify an integrity binding before
  returning it;
- add a regression that creates a genuine `UNKNOWN` run, substitutes an
  out-of-workspace report symlink containing a false `ZERO` and a generic
  canary, and proves a safe failure with no canary output;
- add the equivalent plain-file forged-report regression so stale or edited
  prose cannot contradict the persisted result.

### 2. Parsed metadata and recorded hashes can refer to different bytes

The workspace loader reads `project.yaml`, the assumptions YAML, and the
hypothesis JSON once for parsing and then reads each again through `_source()`
to compute its provenance hash. There is no same-buffer binding or equality
check between those reads.

A controlled editor-race replay changed `assumptions.yaml` immediately after
the parser read and before `_source()` reread it. Verification completed with
`ZERO`; the bounded workspace summary showed `nonzero: false` (the assumptions
actually used), while the source file and recorded `assumptions_hash`
identified `nonzero: true`. The recorded hash matched the new bytes and did
not match the parsed bytes.

This allows a run to certify under one assumption snapshot while its mandatory
provenance names another. It is a reproducibility defect and an assumption-
laundering risk, even though the tool itself did not mutate the source. The
same double-read structure exists for project and hypothesis metadata. This
violates the `PROVENANCE` gate.

Required acceptance evidence before alpha:

- read each metadata source once into an immutable byte snapshot;
- parse, decode, size-check, summarize, and hash that exact snapshot;
- preserve the existing fail-closed behavior if a source cannot be captured
  consistently;
- add deterministic regressions that mutate assumptions and hypothesis files
  at the old read boundary and prove that no run can pair old semantics with a
  new hash.

## Checks that passed

- The fast release-critical gate passed: `12 passed`.
- The focused workspace/API/CLI/security suites passed: `56 passed`.
- Declared input paths reject absolute paths, `..`, and symlink escapes.
  `runs/` and selected run-directory symlinks are rejected. The blocker above
  is the unguarded artifact inside an otherwise accepted run directory.
- Normal clean-room and external-user replays found no source mutation and no
  environment-secret canary in generated artifacts.
- `ZERO`, `NONZERO`, and `UNKNOWN` are distinct in normal generated records;
  normal `UNKNOWN` output explicitly forbids promotion.
- Omission of an already-declared symbol produces the narrow operational
  `ASSUMPTION_REQUIRED` gate without silently adding it. Documentation also
  states that v0.1 cannot infer other missing physical/domain predicates.
- Installed builds record an exact source revision, versions, direct
  dependencies, hashes, verifier route, result, runtime, and warnings in the
  tested clean-room path.
- The public positioning does not affirm any forbidden discovery claim.
  Forbidden phrases occur only as explicit denials/limitations. The proposer
  is optional and experimental, and proposer text cannot certify or promote.
- `SCIENTIFIC_EXPERIMENTS_CLOSED.md` was not reopened by the engineering
  change set.

## Full-suite interpretation

The recorded integration run is not fully green: `2049 passed, 24 failed`.
The committed triage attributes the failures to frozen research hash/source
authority drift, one absent research-only optional LLM client, and historical
package-enumeration behavior involving `__pycache__`. None is evidence of a
failure in the bounded workspace release path, so these 24 failures are not an
additional blocker in this review. They must remain disclosed; they cannot be
reported as a green full repository suite.

The release is rejected on the two independently reproduced safety defects
above, not on scientific capability, proposer performance, or the historical
full-suite count.

## Gate assessment

| Gate | Review result | Basis |
|---|---|---|
| `SECURITY` | `FAIL` | report symlink reads and emits out-of-workspace content |
| `FAIL_CLOSED` | `FAIL` | authentic `UNKNOWN` can be presented as forged `ZERO` report prose |
| `PROVENANCE` | `FAIL` | assumptions/hypothesis/project parse bytes are not bound to recorded hashes |
| claim boundary | `PASS` | public claims remain within the approved evidence boundary |
| scientific-line lock | `PASS` | no research experiment was reopened |

Final reviewer verdict: `INTERNAL_ONLY`.
