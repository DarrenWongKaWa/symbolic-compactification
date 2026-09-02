# New-visitor review — v0.3.0-alpha

Read as a theoretical physicist arriving at the repository, not as the
author of the historical campaigns.

| # | Question | Answer |
|---|---|---|
| 1 | Can I understand the product in 60 seconds? | **Yes.** README opens with the product name, one sentence, and two workflows. |
| 2 | Do I see exactly two workflows? | **Yes.** Forward derivation and paper audit. Historical Mode A/B names are not the public model. |
| 3 | Can I run something useful within five minutes? | **Yes.** `pip install -e ".[dev]"` then `examples/forward/exact-step` or `examples/audit/minimal`. |
| 4 | Is the flagship demo understandable without reading internal docs? | **Yes.** `examples/flagship/guo/RESULTS.md` uses printed equation numbers and GitHub-rendered mathematics. |
| 5 | Are there giant benchmark directories visible at root? | **No.** Historical corpora are in git history and `docs/history/benchmark-history.md`. |
| 6 | Are there old final-report files everywhere? | **No.** Root is README, license, package files, `src/`, `tests/`, `docs/`, `examples/`. Process notes live under `consolidation/`. |
| 7 | Do branch names expose years of internal experimentation? | **No.** Visible remotes: `main` and temporary `paper/derivation-audit-method`. |
| 8 | Does README spend more space on history than product? | **No.** History is one closing sentence plus `docs/research-evidence.md`. |
| 9 | Does anything imply an LLM certifies mathematics? | **No.** README, AGENTS, and the skill state the opposite: proposal ≠ certification. |
| 10 | Is there an obvious path from paper → RESULTS.md? | **Yes.** README → flagship RESULTS.md; `docs/paper-audit.md` and `examples/flagship/guo/REPRODUCE.md` give the replay. |

Post-release remote branch count is 2. Obsolete experiment/engineering
branches were deleted only after archive tags, `v0.3.0-alpha`, and the
GitHub prerelease were verified.
