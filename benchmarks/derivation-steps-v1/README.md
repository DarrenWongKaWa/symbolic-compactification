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

## Caveats

- **Single runs.** There is one run per arm.
- **Same model family.** The same model family wrote the errors and judged
  them.
- **Local errors only.** Non-local errors (conventions across sections, a
  missing term in a long sum, the order of limits) are not tested.
- **Tool versions differ.** The tool version differs between the Opus arm
  and the Sonnet/Haiku arms.
