---
name: symbolic-compactification
description: >
  Audit scientific papers and derivations. Inventory numbered equations,
  reconstruct load-bearing claims and derivation edges, separate assumptions
  from algebra, emit audit.json plus a reviewer HTML evidence ledger and
  matching Markdown. Use when asked to audit a paper, check equations,
  reconstruct a claim/evidence chain, review a derivation, produce an
  evidence ledger, or given an arXiv URL or TeX manuscript. Triggers:
  "audit this paper", "audit https://arxiv.org/abs/...", equation inventory,
  reviewer HTML, derivation audit. LLM judgment is never proof. Not a CAS.
license: MIT
compatibility: Requires Python 3.10+; network access to fetch arXiv sources.
metadata:
  version: "0.3.3"
  product: scientific-derivation-audit
---

# symbolic-compactification

Scientific paper audit. One method. Portable: this folder is the skill.

You are not a CAS, not a theorem prover, and not an autonomous physicist.
A model may propose. Only exact local algebra `A − B = 0` is machine Exact.
Human Accept never stamps Exact.

Resolve `SKILL_ROOT` as the directory that contains this `SKILL.md`.
Run scripts as `python3 "$SKILL_ROOT/scripts/<name>.py" ...`.
Do not require the development repository to be the working directory.

## When to use

Any request to audit a paper, check numbered equations, reconstruct how a
result is derived, or emit a reviewer-facing evidence ledger.

## Output contract

Write into the user's working directory (create `audit/` if needed):

```text
audit/
├── manuscript/          # fetched or copied source
├── inventory.json       # numbered equations
├── audit.json           # canonical evidence
├── audit.html           # reviewer HTML (V3.1 five layers)
└── audit.md             # Markdown twin
```

HTML and Markdown must be generated from the same `audit.json`.
Never author statuses in HTML by hand.

## Status vocabulary (do not invent colours)

| Status | HTML colour | Meaning |
|---|---|---|
| `EXACT` | dark green | Compiled local residual is 0 |
| `EXACT_IF_ASSUMPTIONS` | hatched green | 0 after an explicit substitution; does not prove the substitution |
| `STRUCTURAL` / `CITED_RULE` | blue | Definition, bookkeeping, or named cited rule |
| `GAP` / `HUMAN_REVIEW` / `ASYMPTOTIC_UNCERTIFIED` / `NUMERICAL_SUPPORT` / `UNCERTIFIED` | orange | Reviewer must look |
| `NONZERO_RESIDUAL` | dark red | Compiled residual is not 0 |

Numerical support is orange, not a third colour.
`0*` / workspace overlay is not Exact. Never write it.

## Workflow

### 1. Acquire source

If the user gave an arXiv URL or id:

```bash
python3 "$SKILL_ROOT/scripts/fetch_arxiv.py" --id ARXIV_ID --out audit/manuscript
```

Find the main `.tex` (skip `.bbl`, figures). If the user dropped a TeX file,
copy it to `audit/manuscript/`.

### 2. Inventory numbered equations

```bash
python3 "$SKILL_ROOT/scripts/inventory.py" \
  --tex audit/manuscript/PAPER.tex \
  --out audit/inventory.json \
  --arxiv ARXIV_ID
```

Count only printed numbered rows. Nested `array` / `tikzpicture` breaks are
not equation numbers. Unnumbered displays are not inventory. Adjacent numbers
are not a derivation.

### 3. Extract claims, edges, obligations

Read the source. Write `audit/audit.json` following
[references/AUDIT_SCHEMA.md](references/AUDIT_SCHEMA.md).

Required scientific work:

1. **Major claims** (typically 4–7). What the paper argues.
2. **Load-bearing derivation** for the central result, as reconstructed
   edges (`from_eq`, `to_eq`, `transformation`, `assumptions`, `status`).
   Split distinct transformations into separate edges. Do not collapse a
   whole appendix into one step.
3. **Assumptions / domain** separate from transformation type.
4. **Reviewer obligations** for steps the engine cannot certify.
5. Mark `central: true` on edges that form the load-bearing chain.
6. Optional `presentation` block for compact HTML copy. Presentation never
   changes a status.

Do **not** invent Eq. (i) → Eq. (i+1) because numbers are consecutive.
Do **not** stamp Exact on remainders, limits, special functions, or numerics.
Do **not** copy another paper's claims (Guo is a golden *reference*, not an
answer key).

If the `symbolic-compactification` CLI is installed, you may compile a local
residual for a purely algebraic edge. Promote to `EXACT` only on engine
`ZERO`. If the CLI is absent, leave algebra that was not compiled as `GAP`.

### 4. Check then render

```bash
python3 "$SKILL_ROOT/scripts/check_audit.py" --audit audit/audit.json
python3 "$SKILL_ROOT/scripts/render.py" \
  --audit audit/audit.json \
  --out audit \
  --check
```

Open `audit/audit.html`. Markdown twin is `audit/audit.md`.

## HTML: five visible layers (less is more)

The page answers: **what does the physicist still need to judge?**

1. **Summary** — title, source, `AUDIT_INCOMPLETE`, colour bar.
   One sentence: *Local certification is not a paper-level certificate.*
   First-screen jump strip: *Need your judgment* → reviewer queue.
2. **Coloured equation map** — chips, `→` = reconstructed edge, `⋯` =
   consecutive numbering only. First screen, never a closed `<details>`.
3. **Major claims** — compact cards (path, assumptions, blocks).
4. **Central derivation** — inspect/gap edges visible;
   `✓ N machine-discharged steps` collapsed behind Show.
5. **Reviewer queue** — strongest visual weight. Source on each card.
   One warning: *Human acceptance records reviewer judgment; it does not
   change a machine status to Exact.*

Full equation records and the relation ledger stay in `audit.json` and in
click-to-open drawers. Do not dump a giant always-visible equation table.
MathJax uses only `\(` `\)`. If typesetting fails, show escaped `<pre>`
LaTeX. Never drop an equation.

## Invariants

- Presentation is not a certificate.
- Silence from a non-submitted step is not a pass.
- Finite Laurent/Taylor coefficients do not prove an `O(·)` remainder.
- Numerical agreement with a model is not an analytic proof.
- Do not rewrite statuses to make the page greener.

## Red flags

- Treating a candidate as a result before engine `ZERO`
- Inventing adjacency edges
- Putting `0*` in reviewer HTML
- Copying Guo-specific equation numbers into another paper's audit
- Requiring the user to name this skill or a script path

Further method: [references/METHOD.md](references/METHOD.md).
Statuses: [references/STATUSES.md](references/STATUSES.md).
Schema: [references/AUDIT_SCHEMA.md](references/AUDIT_SCHEMA.md).
HTML: [references/HTML_CONTRACT.md](references/HTML_CONTRACT.md).
