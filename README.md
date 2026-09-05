# symbolic-compactification

**Verified symbolic reasoning for theoretical physics.**

An installable scientific **paper audit** / derivation-audit skill. Give
Codex or Claude Code a paper. It inventories numbered equations,
reconstructs claims and load-bearing edges, and emits reviewer **HTML** +
**Markdown**. A model may propose. Only exact `ZERO` is machine Exact.

This is not a CAS, not a theorem prover, and not an autonomous physicist.
Core verification needs **no API key**.

Package `0.3.2-alpha`. Research preview.

## 1. Install the skill

From any machine with [GitHub CLI](https://cli.github.com/) `gh skill`:

**Codex**

```bash
gh skill install DarrenWongKaWa/symbolic-compactification symbolic-compactification --agent codex --scope user
```

**Claude Code**

```bash
gh skill install DarrenWongKaWa/symbolic-compactification symbolic-compactification --agent claude-code --scope user
```

Restart the harness so it reloads skills.

## 2. Start Codex or Claude Code

Open a **new, unrelated directory**. Do not open this development repository.

## 3. Ask only

```text
Audit https://arxiv.org/abs/2604.04520.
```

The installed skill supplies inventory, claim/derivation reconstruction,
statuses, and the renderer.

## 4. Open the ledger

```text
audit/audit.html
audit/audit.md
audit/audit.json
```

## What green / blue / orange / red mean

| Colour | Meaning |
|---|---|
| Dark green | Local residual is exact `ZERO` |
| Hatched green | `ZERO` after an explicit substitution (`EXACT_IF_ASSUMPTIONS`) |
| Blue | Definition / cited rule |
| Orange | Reviewer looks (gap, assumption, remainder, numerics) |
| Dark red | Compiled residual is `NONZERO` |

Green is a local residual, not a paper pass. Human Accept does not stamp Exact.

## Flagship (golden reference)

Guo et al., Phys. Rev. Lett. 136, 206303.

[`examples/guo-evidence-ledger/output/index.html`](examples/guo-evidence-ledger/output/index.html)

Do not copy Guo claims into another paper.

## Independent benchmark

Anan, Kitamura, Morimoto, arXiv:2604.04520 (V3.1 five-layer page):

[`examples/2604.04520/v3/audit.html`](examples/2604.04520/v3/audit.html)

Status semantics: [`skills/symbolic-compactification/references/STATUSES.md`](skills/symbolic-compactification/references/STATUSES.md).
Portability tests: [`validation/PORTABILITY_REPORT.md`](validation/PORTABILITY_REPORT.md).
UI comparison: [`examples/2604.04520/comparison/UI_COMPARISON.md`](examples/2604.04520/comparison/UI_COMPARISON.md).

## Forward derivation (engine CLI)

Candidate must be exact `ZERO`. Promote only on `ZERO`. `NONZERO` /
`UNKNOWN` never promote.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/symbolic-compactification --version
```

Paper-audit **skill** path does not require that install. Scripts ship
inside the skill folder (Python 3.10 stdlib).

## Canonical skill

[`skills/symbolic-compactification/SKILL.md`](skills/symbolic-compactification/SKILL.md)

`AGENTS.md` / `CLAUDE.md` only tell the harness where the skill is.
