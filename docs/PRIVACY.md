# Privacy (derivation audit)

Local private sources are **not exportable**. They must not appear in git
history, commits, branches, tags, issues, README, examples, tests, snapshots,
fixtures, docs, package data, release artifacts, CI logs, agent summaries,
reviewer reports, telemetry, or external API prompts.

This page is the user-facing privacy contract. Engineering constants live in
`src/symbolic_compactification/audit/privacy.py` and
[engineering/derivation_audit_v0_2/PRIVACY.md](../engineering/derivation_audit_v0_2/PRIVACY.md).

## Rules

1. Public demos are synthetic or clearly public. No near-clones of private
   work.
2. Public engineering decisions are justified by public or synthetic
   fixtures.
3. Optional local acceptance uses `SSC_PRIVATE_OFFLINE=1`.
4. Outputs of private acceptance stay under `.private_validation/`
   (gitignored).
5. A denylist file may exist at `.private_validation/private_denylist.txt`.
   Public CI runs with a missing or empty denylist.
6. Any denylist hit in a public artifact is a release blocker.

Private acceptance is never release evidence.

## Private-offline mode

```bash
export SSC_PRIVATE_OFFLINE=1
```

While set:

- network-shaped targets (`http://`, `https://`, `ftp://`) are refused
- the proposer is disabled
- verification is local and deterministic only

Do not point `manuscript_source` or member paths outside the workspace.
Workspace paths must be relative, use `/`, and must not contain `..` or
symlinks.

## Denylist

If `.private_validation/private_denylist.txt` exists, each non-comment line
is a case-sensitive substring. Hits are release blockers. The denylist file
itself is gitignored; never commit it or log the matched strings.

## Researcher obligations

- Keep private sources out of this repository and out of reviewer packages.
- Do not paste private kernels, equation numbers, or nicknames into public
  issues, tests, or docs.
- Do not put credentials in expressions, notes, or YAML; redaction is
  defence in depth, not DLP.

See [THREAT_MODEL.md](THREAT_MODEL.md) and [PUBLIC_DEMOS.md](PUBLIC_DEMOS.md).
