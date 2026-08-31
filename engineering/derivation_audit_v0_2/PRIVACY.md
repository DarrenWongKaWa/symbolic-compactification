# Privacy firewall (frozen)

Unpublished local scientific sources are `PRIVATE_NON_EXPORTABLE`.

They must not appear in git history, commits, branches, tags, issues, README,
examples, tests, snapshots, fixtures, docs, package data, release artifacts,
CI logs, agent summaries, reviewer reports, telemetry, or external API prompts.

## Rules

1. Public demos are synthetic or clearly public. No near-clones of private work.
2. Public engineering decisions are justified by public/synthetic fixtures.
3. Optional local acceptance uses `SSC_PRIVATE_OFFLINE=1`.
4. Outputs of private acceptance stay under `.private_validation/` (gitignored).
5. A denylist file may exist at `.private_validation/private_denylist.txt`.
   Public CI runs with a missing/empty denylist.
6. Any denylist hit in a public artifact is a release blocker.

Private acceptance is never release evidence.
