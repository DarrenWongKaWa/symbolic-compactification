# Two-skill architecture audit

Inspection only. No product rename, no merge, no tag.

Trees read:

| Tree | Commit | Note |
|---|---|---|
| `origin/main` | `6d02a0f` | current GitHub `main` |
| `release/portable-skill` (this worktree) | `7dd73ce` | portable paper-audit skill + V3.1 HTML |
| local checkout `engineering/research-preview-alpha-v0.1` | `307c51a` | older; extra uncommitted `.grok` role files |
| `experiment/forward-proposer-replay-v1` | history | pluggable proposer adapters, **not on main** |

Do not treat a historical Markdown file as an implemented skill.

---

## 1. Current state

```text
Proposer skill: PARTIAL   (engine + role contract exist; no installable proposer skill)
Reviewer skill: PARTIAL   (installable on the portable branch; fused/Grok-only on main)
```

They are **not** two independent harness-discoverable skills today.

What exists instead:

- **One Python engine** (`src/symbolic_compactification/`) that can verify a
  human/CAS/file candidate (`ZERO` / `NONZERO` / `UNKNOWN`) and record a
  session loop (`init-session` / `step`).
- **One installable Agent Skill** on `release/portable-skill`:
  `skills/symbolic-compactification/` — **paper audit only**.
- **One Grok skill** on `origin/main`:
  `.grok/skills/symbolic-compactification/SKILL.md` — **both workflows in
  one file**, not `gh skill install`-portable (`skills/` is absent on main).

There is no `skills/symbolic-proposer/` and no `skills/derivation-auditor/`.

---

## 2. Current canonical paths

### Reviewer / paper audit

| Item | `origin/main` | `release/portable-skill` |
|---|---|---|
| Canonical `SKILL.md` | `.grok/skills/symbolic-compactification/SKILL.md` (Grok; two workflows) | `skills/symbolic-compactification/SKILL.md` (paper audit only) |
| Entrypoint | CLI `symbolic-compactification audit …` plus Grok skill | Skill scripts: `fetch_arxiv.py`, `inventory.py`, `check_audit.py`, `render.py` |
| Shared library | `src/symbolic_compactification/audit/` + verifier | Same engine in the repo; **not shipped inside the installed skill** |
| Tests | `tests/test_audit_*.py`, `test_v3_2604_audit.py`, `test_flagship_html.py` | plus `tests/test_portable_skill.py` |
| Examples | `examples/guo-evidence-ledger/`, `examples/2604.04520/`, `examples/audit/` | same |
| Docs | `docs/paper-audit.md`, `AGENTS.md` (two workflows) | README + skill METHOD; `AGENTS.md` is a thin Codex pointer to the audit skill |
| Outputs | `REPORT.md` / `report.html` (CLI audit) or `v3/audit.html` | `audit/audit.json`, `audit.html`, `audit.md` |

Harness install (`gh skill install … --agent {codex,claude-code}`) only
works from a tree that contains `skills/*/SKILL.md`. That is the portable
branch, not `main`.

### Proposer / discovery loop

| Item | Where it actually lives |
|---|---|
| Canonical `SKILL.md` | **Missing as a separate skill.** Forward derivation is a *section* of the Grok skill on `main`. The portable skill **omits** it. |
| Role contract | `.grok/skills/symbolic-compactification/STRUCTURAL_PROPOSER.md` (moved from `roles/STRUCTURAL_PROPOSER.md` in `3171e76`). Code comments still say `roles/STRUCTURAL_PROPOSER.md` — stale path, file was relocated not deleted. |
| Entrypoint | CLI `inspect` / `verify` / `init-session` / `step` / `finalize`; Python `verify_equivalent()`, `adjudicate_candidate()` |
| Scripts in installable skill | **None.** Installed skill folder has only audit scripts. |
| Shared library | `verifier.py`, `session.py`, `conjecture.py`, `pipeline.py`, `structure.py` |
| Configuration | `--proposer-mode main\|subagent\|auto` on `init-session`. No API-provider config. |
| Tests | `tests/test_verifier.py`, `test_session.py`, `test_conjecture.py`, `test_proposer_protocol.py`, `test_requested_proposer_mode.py` |
| Examples | `examples/forward/exact-step` (`ZERO`), `examples/forward/refused-step` (`NONZERO`) |
| Docs | `docs/forward-derivation.md`, `docs/architecture.md` |
| Expected outputs | `workspace/runs/<id>/steps/`, `final/FINAL_CERTIFIED_FORM.md` |

---

## 3. Shared engine

Still one kernel. Both workflows are supposed to call it; only the CLI
audit path and the Python verifier actually do.

```text
human / harness / file candidate
        │
        ▼
parser.py  →  ExpressionRecord
        │
        ▼
verifier.py   ZERO | NONZERO | UNKNOWN
        │
        ▼
session.py / pipeline.py   record, promote only on ZERO
        ▲
paper edge (optional) ── audit/edges.py, audit/evidence.py
```

Shared concepts that **exist in code**:

- expression parse + namespace (`parser.py`)
- residual `current - candidate` (`verifier.py`)
- exact equality / probe lattice (no floats)
- `ZERO` / `NONZERO` / `UNKNOWN`
- `HYPOTHESIS` vs `CERTIFIED` (`conjecture.validate_candidate` **rejects**
  any self-declared `CERTIFIED`)
- session provenance (`session.py`)
- budgets / fail-closed UNKNOWN

Not shared today:

- The portable skill’s `check_audit.py` only checks JSON status vocabulary.
  It does not call `verify_equivalent` unless a human/agent separately
  installs the package and compiles an algebraic edge.

---

## 4. Proposer support

```text
LLM proposer:            PARTIAL — harness agent may write candidate.txt;
                         there is NO LLM API client, NO provider list,
                         NO key config in this repo. conjecture.py:
                         “deliberately NO agent runtime, NO LLM API
                         integration”.
Human proposer:          PRESENT at engine level — drop candidate.txt
                         and `verify` / `step`.
External candidate set:  PRESENT at engine level — same files.
                         No batch “here are five candidates” CLI wrapper.
API configuration:       MISSING as a product. Tests redact OPENAI_API_KEY /
                         ANTHROPIC_API_KEY / GOOGLE_API_KEY if they appear
                         in records; the engine does not read them.
                         Core verification needs no key (documented).
Iteration loop:          PARTIAL — `init-session` + `step` is the loop.
                         The proposer is whoever writes the next file
                         (human or harness). No automated search budget
                         skill. Optional `proposer=subagent` is a
                         harness-native subagent, not a pluggable library.
Verifier:                PRESENT — `verify_equivalent` / CLI `verify` /
                         `step`. Promotion only on ZERO.
```

Inspected this session (engine, not skill):

```text
x**2 + 2*x + 1  vs  (x + 1)**2     → ZERO
x**2 + 2*x + 1  vs  -(x + 1)**2    → NONZERO, counterexample x=-2, value 2
```

That is the human/external candidate path. It requires the **Python
package**, not `gh skill install`.

Pluggable adapters (`experiments/forward_replay_v1/proposers/{interface,
cas_sympy,freeze_llm,gplearn_sr,gold_and_negatives}.py`) exist only on
`experiment/forward-proposer-replay-v1`. They were removed from the
product tree in `3171e76` (v0.3.0-alpha unification). They were labeled
“experimental, not a product API”.

---

## 5. Reviewer support

```text
paper ingestion:     PRESENT — skill `fetch_arxiv.py`; CLI `audit init`
equation extraction: PRESENT — skill `inventory.py`; CLI `audit inventory`
verification:        PARTIAL — engine can compile a local residual if
                     the package is installed; the portable skill says
                     leave uncompiled algebra as GAP
audit.json:          PRESENT on the portable path
HTML:                PRESENT — five layers; judgment strip; MathJax
                     `\(`/`\)` with `<pre class="tex-fallback">`
Markdown:            PRESENT — twin of audit.json
```

Portable skill description triggers on paper audit / arXiv URL, not on
“simplify this expression”.

---

## 6. Git-history findings

| Capability | Status |
|---|---|
| Deterministic verifier + session loop | **A. still on main and on the portable branch** |
| Combined Grok skill (forward + audit) | **A. still on `origin/main`** at `.grok/skills/…/SKILL.md` |
| `STRUCTURAL_PROPOSER` role | **B. moved** `roles/` → `.grok/skills/…/STRUCTURAL_PROPOSER.md` (`3171e76`) |
| Installable `skills/` paper-audit skill | **B. added** on `release/portable-skill` (`bcb7863`); **not on main** |
| Forward derivation inside the *installable* skill | **C. dropped** during portable-skill productization. Engine kept; skill method is audit-only. `AGENTS.md` no longer describes the propose→verify loop. |
| `research/grounded_proposer/` | **D. history only** (deleted `3171e76`) |
| `experiments/forward_replay_v1/proposers/` | **D. history / experiment branch only** |
| `.grok/skills/audit-reviewer/` | **D. history only** — a *ledger adversary* role (`MISSING_EDGE`, …), **not** the paper-auditor product |
| Root `CAPABILITIES.json` / `REPERTOIRE_V2.md` | **D. removed** from the product tree; summaries in `docs/history/` |

Do not restore `grounded_proposer` or the gplearn adapters blindly: they
are frozen research, task-mismatched (symbolic regression vs rewrite), and
predate the current skill layout.

---

## 7. Missing pieces (concrete)

1. **No second skill directory** under `skills/` for proposer/discovery.
2. **Portable skill does not teach** `inspect` / `verify` / `step`, and
   does not ship the engine.
3. **`origin/main` is not `gh skill install`-able** (no `skills/*/SKILL.md`,
   no `.claude-plugin/marketplace.json`).
4. **No proposer provider / API-key workflow.** By design the repo is not
   an LLM client. A physicist cannot “configure OpenAI/xAI and run
   proposer”. The intended plug is: *any process writes `candidate.txt`*.
   That interface is the CLI/files, not a skill + env file.
5. **No batch external-candidate command** (“here are five files, verify
   each”). You can loop `verify` yourself.
6. **Stale path** `roles/STRUCTURAL_PROPOSER.md` in `conjecture.py`.
7. **Harness discovery collision:** with only the paper-audit skill
   installed, Codex still *named* `symbolic-compactification` for
   “find a simpler certified form…” because of the skill **name**, not
   because the skill implements that loop. Installed tree contains no
   proposer strings.

### Test A — Proposer skill (clean room `/tmp/sc-test-proposer-discover`)

Installed `release/portable-skill` via `gh skill install` (Codex, project
scope). Prompt: find a simpler certified form of `expr.txt`.

```text
Acquire:  FAIL     no proposer skill to acquire; only paper-audit skill
Discover: PARTIAL  Codex named `symbolic-compactification` (name collision)
Trigger:  FAIL     installed SKILL.md has no proposer method
Execute:  FAIL     via skill (no engine scripts in the skill folder)
Verify:   PASS     engine-only, from this repo with PYTHONPATH=src
Iterate:  PARTIAL  CLI `step` exists in the package, not in the skill
```

### Test B — Reviewer skill

Already run outside the repo (`/tmp/sc-test-codex2`, `/tmp/sc-test-claude2`)
on `98f6a5b`. See `validation/PORTABILITY_REPORT.md`.

```text
Acquire:              PASS
Discover:             PASS
Trigger:              PASS
Execute:              PASS
Scientific fidelity:  PASS Codex / PARTIAL Claude Code
Reviewer output:      PASS (audit.json + HTML + Markdown)
```

---

## 8. Recommended final architecture (minimal)

Keep one engine. Split **two** Agent Skills that both call it. Do not
reintroduce an LLM SDK.

```text
skills/
├── symbolic-compactification/     # keep current name if desired
│   └── SKILL.md                   # paper → audit.json → HTML/MD
│
└── symbolic-proposer/             # new, thin
    └── SKILL.md                   # expression → candidates → verify/step
        scripts/                   # wrappers around the installed package
                                   # or document: pip install -e . then CLI

src/symbolic_compactification/     # shared verifier (unchanged)

candidate source (pluggable, files only):
  human .txt | harness LLM | CAS script | other project
        → verify / step
        → ZERO promote | NONZERO residual | UNKNOWN
```

Skill 1 must say: the verifier certifies; proposers never stamp
`CERTIFIED`; no API key is required; optional keys belong to the *outer
harness*, not this repo.

Skill 2 stays the five-layer reviewer. HTML must not enter `verifier.py`.

`gh skill install` should list **both** `skills/*/SKILL.md`. `main` needs
that layout before a user on Codex/Claude can acquire either skill from
GitHub `main`.

---

## Central questions

### Scenario A

Can a physicist install the skill, configure a proposer if desired, ask
for candidate symbolic compactifications, and let the system repeatedly
propose → verify → reject/accept until useful certified candidates are
found?

```text
PARTIAL
```

Evidence:

- The **engine** already does human/external candidates and a recorded
  `step` loop. `validate_candidate` forbids self-certification. No API
  key is used or required.
- There is **no installable proposer skill**. `gh skill install` delivers
  paper-audit scripts only. There is no provider/API-key configuration
  because this repo is not an LLM client. “Configure proposer provider”
  is **missing by architecture**, not a hidden env var.
- Automated “LLM API proposes until budget” is **not implemented**.
  The loop is: something (human, harness, other project) writes a
  candidate; the engine verifies.

### Scenario B

Can a physicist install the reviewer skill, give it a paper, and receive
only the machine-unresolved derivation obligations in a human-friendly
audit?

```text
PARTIAL
```

Evidence:

- On `release/portable-skill`, yes enough to use: install, ask only
  `Audit https://arxiv.org/abs/2604.04520.`, get `audit.html` / `audit.md`
  / `audit.json` with a reviewer queue. Codex reconstructed the
  (4)→C→D→TR→antisym→shift→(5) chain. Claude coarsened Appendix D.
- On **`origin/main`**, that install path does not exist (`skills/`
  missing). The Grok skill + CLI audit workflow exists but is not the
  portable Codex/Claude skill.
- Machine-check of paper edges still depends on a separate package
  install; the skill alone leaves algebra as `GAP`.

---

**The two-skill product you intended does not fully exist as two
discoverable skills.** The shared verifier and the reviewer skill are
real. The proposer/discovery **skill** was never split out; on the
portable branch the installable method is reviewer-only, while the
propose→verify engine remains in `src/` and in the Grok skill on `main`.
