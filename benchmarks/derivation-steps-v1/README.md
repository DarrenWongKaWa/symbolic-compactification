# Derivation-step benchmark v1: agents with and without the tool

Can agents catch planted errors in long, real derivations, and what does
this tool add at three model sizes?

## Items

There are 32 steps in six chains taken from two research papers. Each step
is a claimed equality with the author's justification.

| Part | Source | Steps | Planted errors | Public here |
|---|---|---:|---:|---|
| K (chains K1–K4) | an unpublished finite-dissipation transport manuscript: thermal kernels, confluent divided differences, Γ poles | 23 | 4 | step ids, error types, results only |
| G (chains G1–G2) | Guo *et al.*, *Dissipation-shaped quantum geometry in nonlinear transport*, arXiv:2511.16422: bath integrals versus residue forms, kernel ω² coefficients and their Γ expansions | 9 | 2 | everything (`sheet_part_G.md`, `chains_guo.py`) |

The planted errors are of the kind that survives proofreading:

| Step | Planted error |
|---|---|
| K1.5 | `2Γ − iε` → `2Γ + iε` in a denominator |
| K2.4 | `2iΓ` → `iΓ` |
| K3.5 | pole coefficient halved |
| K4.4 | `(x − y)` → `(y − x)` |
| G1.3 | `f₊(ε_m − ω)` → `f₊(ε_m + ω)` |
| G2.2 | `1/384` → `1/192` |

The ground truth is numerical and does not use the tool or the papers'
derivations:
- derivatives by `mp.diff`;
- ω-coefficients by a Cauchy contour integral;
- bath integrals by quadrature;
- O(·) claims by remainder scaling.

For every planted step, the unplanted original is confirmed valid. Every
formula tested from Guo *et al.* is numerically correct.

## Arms

Each model size was run in three setups, once each, from the same blinded
sheet:

| Setup | What the agent may use |
|---|---|
| whiteboard | the sheet only, no tools |
| python | SymPy, mpmath, numpy |
| python_tool | Python plus `symbolic-compactification` |

**Tool versions differ.** The Opus tool arm used the tool before PR #16.
The Sonnet and Haiku tool arms used it after PR #16, which adds divided
differences, series coefficients, digamma reflection and the Γ-limit series
route.

## Results

`python3 score.py`:

| Arm | Correct | Planted errors caught | False alarms | Steps computed | Steps decided by the tool |
|---|---:|---:|---:|---:|---:|
| opus_whiteboard | 32/32 | 6/6 | 0/26 | 0/32 | – |
| opus_python | 32/32 | 6/6 | 0/26 | 31/32 | – |
| opus_python_tool | 32/32 | 6/6 | 0/26 | 28/32 | 12 |
| sonnet_whiteboard | did not finish: exceeded the 64k output-token limit twice | | | | |
| sonnet_python | 30/32 | 6/6 | 2/26 | 32/32 | – |
| sonnet_python_tool | 31/32 | 6/6 | 1/26 | 32/32 | 13 |
| haiku_whiteboard | 25/32 | 0/6 | 1/26 | 0/32 | – |
| haiku_python | 26/32 | 0/6 | 0/26 | 14/32 | – |
| haiku_python_tool | 19/32 | 3/6 | 10/26 | 19/32 | 0 |

**Tool verdicts were never wrong.** Across the tool arms the tool returned
25 decisive verdicts (`ZERO`, `NONZERO` or `CERTIFIED_BY_RULE`), and all 25
were correct. Every `NONZERO` fell on a planted error and every
`ZERO`/certificate on a valid step.

## What the results say

1. **Frontier model.** Every arm is perfect, so the tool adds no accuracy.
   The model rederives each step from the definitions.
2. **Mid-size model.** Both computing arms catch all six errors. The tool
   arm has one false alarm fewer, and four of its six catches are the tool's
   own `NONZERO` with a counterexample (K1.5, K2.4, K4.4, G2.2). The
   remaining false alarm (G2.3) came from the agent's own Python: it
   expanded ρ̃₁_mn instead of ρ̃₁_nm. That is a convention slip the tool
   cannot catch, because it happened in encoding. Reasoning alone did not
   finish within the output budget.
3. **Small model.** Neither reasoning nor Python finds any error: Python was
   used only on easy steps, and everything was approved. With the tool
   available, the agent never managed to call it. It then rejected every
   step it could not check, which "caught" three errors at the cost of ten
   false alarms. **A small model plus this tool does not reach
   frontier-level reliability.** The bottleneck is encoding a step into a
   checkable form, not the checker.

## Round 2: step cards and the encoding cookbook (PR #17)

The tool gained three things in PR #17:
- **Step cards:** one YAML file per step, with named definitions.
- **An encoding cookbook** with a decision rule for agents: VALID only on
  `ZERO` or a certificate, INVALID only on `NONZERO`, otherwise "not
  decided".
- **Exact Fermi-weighted integrals.**

The Sonnet and Haiku arms were then rerun on the same sheet:

| Arm | Correct | Planted errors caught | False alarms | Abstained | Steps decided by the tool |
|---|---:|---:|---:|---:|---:|
| sonnet_cards | 31/32 | 6/6 | 1/26 | 0 | 13 |
| haiku_cards_run1 | 13/32 | 2/6 | 1/26 | 17 | 11 |
| haiku_cards_run2 | 25/32 | 1/6 | 2/26 | 0 | 8 |

- **Sonnet.** It catches all six errors again. Its only false alarm (G1.4,
  confidence 0.55) came from its own numerics. The index-order slip of round
  1 (G2.3) did not recur. Its catch of G1.3 is **not independent**: the
  first version of the cookbook used Guo's ρ₁ integral as its worked
  example and described the planted `f₊(ε_m + ω)` error.
- **Haiku.** The cookbook changed its behaviour but not its detection.
  - It now calls the tool: 8–11 decided steps, versus none before.
  - False alarms fell from 10 to 1–2, because it abstains instead of
    rejecting.
  - It still catches only 1–2 of the six errors.
- **Every wrong Haiku result traces to encoding, not to the checker.** We
  read the cards Haiku wrote:
  - K2.2 and K2.3: where a step took the second derivative of a divided
    difference, it encoded the second derivative of the underlying
    function. The card language had no way to write the latter, so
    `Diff(expr, x, k)` was added.
  - K1.4: it divided the divided differences by the gap a second time, and
    it transcribed only the first term of the claim.
  - G1.3: it copied the cookbook's example card, which holds Guo's
    **correct** formula, instead of transcribing the planted claim.

  For each of these the tool's verdict was correct for the card it was
  given, but it was wrong about the step.

**Fixes after round 2.**
- `Diff(expr, x, k)` for derivatives of any expression.
- Every worked example in the cookbook and `examples/cards/` is replaced by
  one that is not a benchmark item.
- The cookbook now states "transcribe, do not reconstruct".

These arms were run before the fixes, so they measure the version with the
contaminated examples.

**Conclusion.** The checker is sound, and every decisive verdict was
correct for its encoded input. Its value depends on whether the agent
transcribes the step faithfully. A mid-size model with the tool matches a
frontier model on this benchmark, and 4 of its 6 catches are machine
`NONZERO` verdicts with counterexamples. A small model with the tool does
not, because transcription fails.

## Round 3: source-tied cards, drafts from the document (PR #18)

After round 2 showed that every wrong answer from Haiku came from a
mis-transcribed card, the tool was changed so that a card can be checked
against the text:
- **Verbatim quotes.** A card quotes the source verbatim. The tool checks
  that each quote occurs in the document, translates it by fixed rules and
  compares it with the card. `--require-source` makes every expression
  and every card-level definition a checked quote.
- **Drafts.** `manybody draft` writes the cards from the document itself,
  so no formula is retyped. The agent only fills in one conventions file
  and picks the checks.

| Arm | Correct | Caught | False alarms | Tool decided the reported verdict |
|---|---:|---:|---:|---|
| haiku_source_run1 (quotes optional) | 20/32 | 2/6 | 8/26 | no card carried a quote |
| haiku_source_run2 (quotes optional) | 26/32 | 1/6 | 1/26 | 7 of 10 tool-checked steps (it overrode the tool on 3) |
| haiku_draft_run1 | 26/32 | 0/6 | 0/26 | none |
| haiku_draft_run2 | 26/32 | 0/6 | 0/26 | none |
| sonnet_draft | 32/32 | 6/6 | 0/26 | none (see below) |

- **Optional quotes do not help a small model.** In run 1, Haiku wrote no
  `source:` block at all. Its unfaithful cards got decisive verdicts on
  valid steps, which gave 8 false alarms. Replayed with
  `--require-source`, every one of its cards is `NOT_DECIDED`: the strict
  replay turns those false alarms into abstentions.
- **Drafting removes transcription but moves the work into conventions.**
  Haiku filled `conventions.yaml` with identity maps (`rho0_n: rho0_n`) and
  declared `e_nm` as an independent symbol. That silently drops the
  convention `e_nm = e_n − e_m`. The tool then decided nothing, and Haiku
  approved every step. Writing the notation table and definitions is the
  one step a small model cannot do here.
- **Sonnet caught 6/6 with no false alarm, by its own numerics.** Midway
  through its run, every tool call stalled. The cause was the environment:
  the repository sat in an iCloud-synced folder and file reads blocked.
  It was not a defect of the tool, and Sonnet reported it. Its verdicts
  therefore count as the "Python" setup, not as tool-decided.

**Conclusion.** The strict pipeline is now safe for small models: a wrong
card is never decided. It still needs the conventions to come from the
author, the reviewer or a strong model. Once they do, the cards are
mechanical, and the reviewer package shows exactly those conventions
for a one-time check. [`../../docs/case-study-jwm.md`](../../docs/case-study-jwm.md)
applies this to a published paper.

## Caveats

- **Single runs.** There is one run per arm.
- **Same model family.** The same model family wrote the errors and judged
  them.
- **Local errors only.** Non-local errors (conventions across sections, a
  missing term in a long sum, the order of limits) are not tested.
- **Tool versions differ.** The tool version differs between the Opus arm
  and the Sonnet/Haiku arms, and between rounds.
- **Environment stalls.** Some round-3 runs were slowed or stalled by an
  iCloud-synced working directory.
