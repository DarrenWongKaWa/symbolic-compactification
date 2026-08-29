# AI_UNIQUE mini-audit (DEV resolvent)

Candidate: operational Newton first-difference of `F(t)=1/(t-a)` on
CORE_COMPARABLE resolvent tasks. Frozen B9 is TYPE_ONLY.

| auditor | question | verdict |
|---|---|---|
| A symbolic-baseline | same operational H already from B1–B5? | **PASS** (TYPE_ONLY / LGG templates ≠ F+maps+reconstruction) |
| B leakage | gold type in proposer-visible text? | **FAIL** — `prompts/SYSTEM_V1.txt` uses “divided difference” as the TYPE_ONLY negative example and lists `Hermite-on-Guo` among forbidden strings. Task packs and SOL do not name Newton/DD/Hermite. |
| C verification | obligations exact ZERO? | **PASS** (rational identity; numerator identically 0) |

AI_UNIQUE_CANDIDATE: yes (R2 resolvent cluster).
AI_UNIQUE_CONFIRMED: **no** (requires 3/3; B fails).

The system-prompt mention is a frozen V1 instruction, not a post-hoc
pack leak. It is still proposer-visible target vocabulary. Do not
retune SYSTEM_V1 after seeing DEV outcomes.

Do not count two successes on mp-resolvent and ac-r01 as two
independent confirmed results (NEAR_DUPLICATE cluster).
