# Portability report

Replay install: GitHub `release/portable-skill` @ `98f6a5b`
(skill metadata 0.3.3). Clean rooms `/tmp/sc-test-codex2` and
`/tmp/sc-test-claude2`. Minimal prompt only:

```text
Audit https://arxiv.org/abs/2604.04520.
```

| Gate                | Codex | Claude Code |
| ------------------- | ----- | ----------- |
| Acquire             | PASS  | PASS        |
| Discover            | PASS  | PASS        |
| Trigger             | PASS  | PASS        |
| Execute             | PASS  | PASS        |
| Scientific fidelity | PASS  | PARTIAL     |
| Overall             | PASS  | PARTIAL     |

Prior `bcb7863` rooms (`/tmp/sc-test-codex`, `/tmp/sc-test-claude`) were
G5 PARTIAL on both harnesses (Appendix D collapsed). METHOD grain in
`98f6a5b` unblocked Codex; Claude still coarsened D.

## Can a user install `symbolic-compactification`, start either supported harness from an unrelated directory, provide only a scientific paper, and obtain the intended reviewer-facing audit?

PARTIAL

Evidence:

- **Install is the real user command.** From an empty git repo:

  ```bash
  gh skill install DarrenWongKaWa/symbolic-compactification symbolic-compactification --agent codex --scope project --pin release/portable-skill --force
  gh skill install DarrenWongKaWa/symbolic-compactification symbolic-compactification --agent claude-code --scope project --pin release/portable-skill --force
  ```

  Codex lands in `.agents/skills/`; Claude Code in `.claude/skills/`.
  Do not pass `--dir` unless you want a raw folder instead of the
  harness path.

- **Discovery and trigger work** on both. The user does not need to name
  the skill or a script.

- **Execute works** on both: arXiv fetch, inventory 93, `audit.json`,
  five-layer HTML with Need-your-judgment strip, Markdown twin.

- **Codex G5 meets the Anan semantic benchmark:** Eq. (4) → Appendix C →
  Appendix D → TR → antisymmetrization → shift-vector / `H = ξ i A` →
  Eq. (5), with orange remainders and a reviewer queue.

- **Claude G5 is a competent but coarser ledger:** same spine, Appendix D
  still one edge. Skill instructions were enough (Codex split D). That is
  HARNESS_BEHAVIOR, not a remaining skill defect.

- **No Guo answer-key leak.** No `0*`.

## Skill vs harness

| Issue | Class |
|---|---|
| Codex uncompiled `EXACT_IF_ASSUMPTIONS` on E-3 | HARNESS_BEHAVIOR |
| Claude collapsed Appendix D | HARNESS_BEHAVIOR |
| Claude unknown-model warning | HARNESS_BEHAVIOR |
| `--dir` installs outside `.agents` / `.claude` | document; not a skill defect |

## Release gates still open

- No merge to `main`.
- No post-merge install from `main` / tag.
- No tag.

Do not treat this as a PASS release: Claude G5 is PARTIAL.
