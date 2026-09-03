# Clean-room test — arXiv:2604.04520

Canonical regenerate for V3 (this release):

```bash
python examples/2604.04520/tools/render.py --check
```

That writes `v3/audit.html` and `v3/audit.md`. It does not overwrite `v1/`
or `v2/`. A fresh-agent Codex/Claude PASS is **not** claimed for V3 in
this file.

---

# Historical V2 record

Date: 2026-09-03. Branch: `audit/v2-2604.04520`.

Date: 2026-09-03. Branch: `audit/v2-2604.04520`.

Prompt given to a fresh agent (no development conversation):

> Audit arXiv:2604.04520 using this repository. Produce the reviewer-facing HTML and Markdown evidence reports.

Isolated clones: `/tmp/ssc-cleanroom-v2-codex`, `/tmp/ssc-cleanroom-v2-claude`.

## Codex

**PASS (after a first-turn misroute).**

On the first utterance Codex loaded a global `academic-paper-reviewer` skill (journal referee panel) instead of `AGENTS.md`. That is a harness-routing defect, not a missing repo instruction.

A continuation that restricted the agent to this repository’s paper-audit workflow then:

- ran `examples/2604.04520/tools/{inventory,build_audit,render}.py --check`;
- wrote `v2/audit.html` and `v2/audit.md` from `evidence/audit.json`;
- left `v1/` untouched;
- stated that **Eq. (4) → Eq. (5) is load-bearing** (claim C2, Appendix C then D) and is **not** machine-certified (`GAP` / `HUMAN_REVIEW` / `STRUCTURAL` on the constituent edges).

Paper-specific tests: 5/5. Renderer: `CHECK_OK`.

## Claude Code

**BLOCKED.** `claude` is installed and OAuth-logged-in, but `claude -p --model sonnet` exited immediately in this environment (same print-mode/default-model failure as the v0.3.1-alpha productize run). Not reported as PASS.

## Substitute

The documented regenerate commands were executed independently in the worktree and match committed V2 bytes (`tests/test_v2_2604_audit.py`).
