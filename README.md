# symbolic-compactification

**Verified symbolic reasoning for theoretical physics.**

An installable skill with two tasks over one engine. **Compactify** a
given expression: the agent proposes a candidate, the program checks the
residual, and improvement is scored separately. **Paper audit** /
derivation-audit still inventories numbered equations, reconstructs
claims and load-bearing edges, and emits reviewer **HTML** +
**Markdown**. A model may propose. Only exact `ZERO` is machine Exact.
The model cannot write that status.

This is not a CAS, not a theorem prover, and not an autonomous physicist.
Core verification needs **no API key**.

Package `0.3.2-alpha` (PEP 440: `0.3.2a0`). Engine `0.3.0`.
Skill metadata `skill_version` `0.3.4` (portable workflow), compatible
with engine `>=0.3.2a0,<0.4`. Research preview.

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
Compactify this formula. Keep the declared symbols and domain.
Do not introduce a new name for the whole expression.
```

The installed skill proposes a candidate, runs `compact_verify.py`, and
writes a bound receipt. Machine Exact is issued only by `certify.py` /
`compact_verify.py`.

## 4. Open the result

```text
compact/result.tex
compact/report.md
compact/verification.json
compact/unresolved.md
```

Paper audit is a secondary path. It starts only when the user asks to
audit a derivation, not because an arXiv link appears in a translation.

## What green / blue / orange / red mean

| Colour | Meaning |
|---|---|
| Dark green | Local residual is exact `ZERO` |
| Hatched green | `ZERO` after an explicit substitution (`EXACT_IF_ASSUMPTIONS`) |
| Blue | Definition / cited rule |
| Orange | Reviewer looks (gap, assumption, remainder, numerics) |
| Dark red | Compiled residual is `NONZERO` |

Green is a local residual, not a paper pass. Human Accept does not stamp Exact.

## Optional case library (not loaded by the skill)

`examples/` holds historical paper audits and synthetic toys. They are
**not** default knowledge. A new task must not copy their claims,
equation numbers, or conclusions.

- Synthetic compactification: `examples/forward/`
- Synthetic audit workspace: `examples/audit/minimal/`

Status semantics: [`skills/symbolic-compactification/references/STATUSES.md`](skills/symbolic-compactification/references/STATUSES.md).

## Forward derivation (engine CLI)

Candidate must be exact `ZERO`. Promote only on `ZERO`. `NONZERO` /
`UNKNOWN` never promote.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/symbolic-compactification --version
```

Reconstruction scripts ship inside the skill folder (Python 3.10 stdlib).
Machine Exact still requires this engine install; without it, algebra stays a gap.

## Canonical skill

[`skills/symbolic-compactification/SKILL.md`](skills/symbolic-compactification/SKILL.md)

`AGENTS.md` / `CLAUDE.md` only tell the harness where the skill is.
