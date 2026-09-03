# Cleanup manifest — 0.3.2-alpha / Anan V3

Classifications used: KEEP_PRODUCT, KEEP_TEST, KEEP_EXAMPLE, KEEP_MANUSCRIPT,
KEEP_HISTORY, GENERATED_REPRODUCIBLE, REDUNDANT_DUPLICATE, TEMPORARY,
OBSOLETE, UNKNOWN.

Nothing classified UNKNOWN was deleted.

## In-repository

| path | classification | reason | replacement | delete? |
|---|---|---|---|---|
| examples/guo-evidence-ledger/ | KEEP_PRODUCT | Flagship | — | no |
| examples/2604.04520/evidence/audit.json | KEEP_EXAMPLE | Canonical Anan evidence | — | no |
| examples/2604.04520/v3/ | KEEP_EXAMPLE | Canonical Anan product | — | no |
| examples/2604.04520/index.html | KEEP_EXAMPLE | Pointer to V3 | v3/audit.html | no |
| examples/2604.04520/v1/ | KEEP_HISTORY | Visual-ledger baseline | v3/ | no |
| examples/2604.04520/v2/ | KEEP_HISTORY | Claim-ledger baseline | v3/ | no |
| examples/2604.04520/tools/render.py | KEEP_EXAMPLE | V3 renderer | — | no |
| examples/2604.04520/tools/render_v2.py | KEEP_HISTORY | Frozen V2 renderer | render.py | no |
| examples/2604.04520/comparison/ | KEEP_HISTORY | V1/V2/V3 notes | — | no |
| examples/audit/minimal/ | KEEP_EXAMPLE | CI toy workspace | — | no |
| examples/audit/2604.04520/ | KEEP_EXAMPLE | Formative V1-style demo (HTML bytes match v1/, but INVENTORY/RESULTS/RELATIONS are the formative workspace) | examples/2604.04520/v1/ for HTML only | no |
| examples/audit/1508.00571/ | KEEP_EXAMPLE | Formative Sodemann ledger | — | no |
| examples/flagship/README.md | KEEP_PRODUCT | Compatibility pointer to Guo | examples/guo-evidence-ledger/ | no |
| examples/forward/ | KEEP_EXAMPLE | Exact / refused demos | — | no |
| docs/history/ | KEEP_HISTORY | Closed campaigns, 0* archive | — | no |
| manuscripts/ | KEEP_MANUSCRIPT | — | — | no |
| tests/ | KEEP_TEST | — | — | no |
| src/ | KEEP_PRODUCT | — | — | no |
| .grok/skills/symbolic-compactification/ | KEEP_PRODUCT | Agent skill; Guo HTML contract unchanged | — | no |

No in-repo path met the deletion bar (exact duplicate with no compatibility
purpose, generated-only, superseded temporary, or obsolete with no
references). The Anan formative HTML under `examples/audit/2604.04520/`
is byte-identical to `examples/2604.04520/v1/audit.html` but lives with
distinct RESULTS/INVENTORY files; deleting it would break the formative
demo tree.

## Local (not in Git)

| path | classification | reason | delete? |
|---|---|---|---|
| /Users/kawawong/Projects/symbolic-compactification (engineering/research-preview-alpha-v0.1, dirty) | KEEP_HISTORY | Operator checkout; unique uncommitted skill/paper HTML | no |
| /private/tmp/ssc-v3-anan | KEEP_PRODUCT | This release worktree | no (until merge) |
| /private/tmp/ssc-v2-anan | KEEP_HISTORY | Merged V2 worktree | no until inspected after merge |
| /private/tmp/ssc-productize | KEEP_HISTORY | Merged 0.3.1 productize | no |
| /private/tmp/ssc-* research/work/paper worktrees | KEEP_HISTORY or UNKNOWN | Unmerged scientific campaigns; unique commits | no |
| /Users/kawawong/Projects/examples/2604.04520 | TEMPORARY | Editor scratch copies of V1/V2 HTML | yes (local only, not a git path) |

Worktrees marked `prunable` by git still hold unique `work/*` and
`research/*` commits. They are not product clutter inside the
repository. This release does **not** force-delete them.

## Local branches

Do not delete: `main`, `release/v3-product-cleanup`, any `paper/*`,
`research/*`, `engineering/*` with unique commits, or branches with
open PRs.

`audit/v2-2604.04520` is merged to `origin/main` (PR #7). Safe
`git branch -d` only after its worktree is removed and the operator
confirms.
