# AGENTS.md

You are operating **symbolic-compactification**: an agent-assisted
derivation-audit system. LLM judgment is never proof. Core verification
needs no API key.

Two workflows: **Forward derivation** and **Paper audit**. Promote only
on `ZERO`.

Canonical docs: `docs/paper-audit.md`, `docs/architecture.md`,
`docs/semantics.md`. Claude Code: `CLAUDE.md` (same contract).

## Product

Input: a scientist's paper/derivation with numbered equations.
Output: reviewer-facing HTML + Markdown, with provenance
source → numbered equation → relation → frozen status → report.

Flagship: `examples/guo-evidence-ledger/output/index.html`.

## Canonical commands

```bash
python -m pip install -e ".[dev]"
symbolic-compactification --version

# paper audit
symbolic-compactification audit init DIR
symbolic-compactification audit inventory DIR
symbolic-compactification audit verify DIR
symbolic-compactification audit report DIR
# → DIR/reports/REPORT.md and DIR/reports/report.html

# forward derivation
symbolic-compactification verify WORKSPACE
```

Replay the flagship HTML (presentation only):

```bash
python examples/guo-evidence-ledger/presentation/assemble_ledger.py
python examples/guo-evidence-ledger/presentation/verify_presentation.py
```

Anan V3 example (arXiv:2604.04520):

```bash
python examples/2604.04520/tools/inventory.py
python examples/2604.04520/tools/build_audit.py
python examples/2604.04520/tools/render.py --check
```

Canonical outputs: `examples/2604.04520/v3/audit.html` and `v3/audit.md`.
Do not overwrite `v1/` or `v2/` (historical baselines).

Validation: `make test` (release-critical + derivation-audit gates) and
`python scripts/check_clean_room.py`.

## Scientific invariants

- `ZERO` means exact engine `ZERO`. It is not `CERTIFIED_BY_RULE`.
- `UNKNOWN` never promotes.
- Do not invent Eq. (i) → Eq. (i+1) from adjacency.
- Do not weaken residuals to manufacture `ZERO`.
- Do not rewrite frozen `RESULTS.md` statuses.
- Do not treat `0*` / workspace overlay as Exact. That lineage is
  invalid and archived in `docs/history/invalid-0star-lineage/`.
- Presentation is not a certificate. HTML copies frozen statuses.

## Output contract

For a paper audit the reviewer must be able to see:

1. What was inventoried (numbered equations only).
2. Which relations are source-grounded.
3. Which residuals the engine actually ran.
4. Which rows still need human scientific judgment (reviewer queue / remainder / look). Human Accept does not stamp Exact.
5. Matching Markdown and HTML statuses.

Appendix maps are a visible `<section id="map-sec">` on the first screen,
never a closed `<details>`.

## Do not

- Weaken or delete legitimate tests to get green CI.
- Fabricate evidence, citations, or residuals.
- Reopen frozen negatives in `docs/history/negative-results.md` without a
  new predeclared experiment.
