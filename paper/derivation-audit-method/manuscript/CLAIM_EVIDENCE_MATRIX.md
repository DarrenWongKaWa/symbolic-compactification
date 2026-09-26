# Claim–Evidence Matrix

Parent constitution: `PAPER_AUTHORITY_LOCK.md`.
Source prose scanned: `draft-v3.md` (abstract, contributions, §§2–7, 9–10).
This matrix is the permitted-wording layer. Humanizer may change style.
It may not change a row's **Strength** or **Allowed wording**.

Rule:

```text
Claim → Frozen evidence → Permitted wording
```

A sentence that cannot be placed in a row is not a load-bearing claim and
must not be written as one.

---

## Strength vocabulary

| Strength | Means | Typical verbs |
|---|---|---|
| demonstrated | public product + frozen evidence, no extra caveat required for the claim as stated | is, does, returns |
| demonstrated with caveats | true on the frozen campaign; caveats must travel in the same paragraph | shows, under these conditions |
| implemented | true of the frozen software/schema; not an empirical coverage claim | records, excludes, promotes only on |
| sampled | true of the sampled set; not a population claim | on a sample of, in this set |
| formative | the case shaped the adapter; not held-out generalisation | formative field case |
| candidate | research observation, not a product claim | a further extension would |
| unsupported | no frozen evidence, or contradicts the lock | **do not write** |

---

## Load-bearing claims

| ID | Claim | Manuscript location (draft-v3) | Evidence | Strength | Allowed wording | Forbidden wording |
|---|---|---|---|---|---|---|
| L1 | One typed framework supports Forward + Audit | Abstract; §1 C1; §§2–3 | `v0.3.0-alpha` @ `f1d225e`; product Forward and Audit workflows; demos `examples/forward/*`, `examples/audit/minimal`, `examples/flagship/guo/` | demonstrated | one typed evidence graph; two workflows; shared object \(\gamma\) | first system ever; unique in all of CS |
| L2 | Proposal / extraction is untrusted | Abstract; §2; §4.1; §6.1 | product contract; `verify`/`step`; session tests force `HYPOTHESIS` | implemented | candidates are untrusted; proposal authority is not verification authority | AI is untrusted but humans are not; models cannot propose |
| L3 | Candidates cannot self-promote | Abstract; §4.3; §7 RQ1 | Forward demos on `v0.3.0-alpha`; session CASE B; `archive/forward-proposer-replay-v1` (0/36 false promotion) | demonstrated with caveats | uncertified candidates are not installed as accepted state; promote only on engine `ZERO` | the proposer finds the next formula; autonomous discovery; shipped `propose` |
| L4 | Engine `ZERO` is exact residual zero, not a rule certificate | Abstract; §3.2–3.3; §5.3 | `schema.py` on `v0.3.0-alpha`; Guo IBP rows `CERTIFIED_BY_RULE`; tests `test_audit_bz_ibp.py` | implemented | `ZERO` ≠ `CERTIFIED_BY_RULE`; BZ IBP is local Leibniz `ZERO` plus a declared torus rule | the integral was evaluated; rule certificates are weaker/stronger truths |
| L5 | `UNKNOWN` never promotes | §3.3; §4.3; audit demo remainder | product semantics; `examples/audit/minimal` remainder `UNKNOWN`; replay `UNKNOWN` refusals | implemented | `UNKNOWN` is not permission to advance | `UNKNOWN` means likely true / near-miss |
| L6 | Claim type \(\tau\) and certificate provenance \(c\) are independent axes | Abstract; §3; Fig 2 spec | schema edge types vs certificate/status fields; Guo table splits algebra / substitution / rule / remainder | implemented | algebraic equivalence is a type of move; `DIRECT_EXACT` is a kind of support | one axis; pass/fail bit |
| L7 | Substitution-conditioned zero is not unconditional equality | §3.2; §7 RQ1; Guo (D-66)→(D-67) | flagship `ZERO_UNDER_SUBSTITUTION` 21; replay FR-06/FR-08 remain `NONZERO` vs current | demonstrated | zero after a declared identity is written in; the identity itself is not proved | (D-66) equals (D-67) unconditionally |
| L8 | Verified tables are generated, not authored | §5.4; §6.3; §7 RQ2 | `schema.may_appear_in_verified_table`; `test_audit_adversarial.py` | implemented | Markdown `ZERO` is ignored; LLM text cannot fill `TABLE_VERIFIED` | all forgery is impossible |
| L9 | Tested narrative/record attacks cannot populate the verified table | Abstract; §7 RQ2 | `test_audit_adversarial.py`, `test_audit_bz_ibp.py` on the product tree | demonstrated with caveats | under the implemented threat model, tested manipulations cannot populate the table | the evidence layer is unforgeable; all conceivable forgery is impossible |
| L10 | Core verification needs no API key | §6.4 | `v0.3.0-alpha` release notes; clean-room replay | demonstrated | core verification needs no model service and no API key | the method does not use AI |
| L11 | Forward public demos: exact `ZERO`, refused `NONZERO` | §7 RQ1 | `examples/forward/exact-step`, `examples/forward/refused-step` on `v0.3.0-alpha` | demonstrated | exact-step returns `ZERO`; refused-step returns `NONZERO` and does not rewrite current | Demo B Newton DD is a product headline (it is not on the v0.3 public example surface) |
| L12 | Heterogeneous proposers share one frozen verifier | §7 RQ1 | `archive/forward-proposer-replay-v1`; verdict `FORWARD_WORKFLOW_DEMONSTRATED_WITH_CAVEATS` | demonstrated with caveats | existing proposers can share one typed evidence layer; no admissible evidence still means no promotion | LLM recovered Guo; gplearn is a derivation proposer; TargetRecovery is the result |
| L13 | Injected invalids are not promoted (forward replay) | §7 RQ1; Table 7 | 0/36 false promotion on injected invalids | demonstrated with caveats | observed false-promotion rate 0/36 on injected invalids in this replay | never false-promotes any invalid candidate |
| L14 | Complete numbered-equation inventory of one public paper | Abstract; §1 C4; §7 RQ3 | Guo flagship 189/189; TeX=HTML match | demonstrated | 189 of 189 numbered equations were inventoried | 189 equations verified / proved / certified |
| L15 | Only source-grounded relations are checked | Abstract; §7 RQ3 | 146 source-grounded relations; adjacency is not a derivation | demonstrated | 146 source-grounded relations; adjacent numbering is not a derivation | every neighbouring pair was tested |
| L16 | Executable subset and typed statuses on Guo | §7 RQ3; App A; Table 2 | `EXACT_ZERO` 32; substitution 21; `CERTIFIED_BY_RULE` 11; remainder 17; structural 47; unsupported 18; `NONZERO` 0; false promotion 0/155 | demonstrated | report the frozen counts; remainders and IBP are informative non-green statuses | 53/53 passed; 189 passed; greenness ranking |
| L17 | Printed examples: exact / substitution / rule / remainder | §7 RQ3; Fig 4 spec | RESULTS.md rows (D-59)→(D-60), (D-66)→(D-67), (D-114)→(D-119), (D-57) | demonstrated | those four printed steps have those statuses | the whole supplement is exact |
| L18 | Guo is formative, not held-out generalisation | §7 RQ3; §9 | BZ IBP adapter added because this paper needed it | formative | formative field validation; not independent generalisation to unseen manuscripts | general method for all PRL papers |
| L19 | Same status vocabulary on a sampled multi-paper set | Abstract; §1 C4; §7 RQ3 last paragraph | `archive/prd-cross-paper-stress-v1`: 5 papers, 41 edges, false promotion 0/30 | sampled | sampled stress test on five public theory papers; 41 source-grounded edges | five full-paper audits; general cross-paper applicability |
| L20 | The system does not prove a paper or physical conclusions | Abstract; §7 RQ3; §9 | method contract; flagship report | implemented | equation-level audit; does not prove the paper or confirm physical conclusions | the paper is correct; physics is confirmed |
| L21 | Finite coefficient `ZERO` is not a remainder proof | §3.1; audit demo; (D-57) | schema `ASYMPTOTIC_CLAIM`; Demo C / minimal audit; flagship (D-57) `UNKNOWN_REMAINDER` | demonstrated | coefficient `ZERO` is not a remainder certificate | the \(\Gamma\) expansion is certified |
| L22 | Inventory is not algebra | §3.1; §5.1 | inventory extracts labels/ranges; residuals are transcribed | implemented | inventory counts are not scientific evidence; transcription is a limitation | the tool reads PDFs / understands LaTeX as algebra |
| L23 | One named global rule, field-driven growth | §3.3 | catalogue `BZ_TORUS_PERIODICITY` only on `v0.3.0-alpha` | implemented | present catalogue contains one named global rule | a theorem-prover library; Stokes/Hermiticity are supported |
| L24 | Engine identity is 0.3.0, package is 0.3.0-alpha | §6.4 | tag `v0.3.0-alpha` peel `f1d225e` | demonstrated | package `0.3.0-alpha`; engine `0.3.0` unchanged | engine was bumped for the repository cleanup |
| L25 | Approximation-aware certification | §9 one sentence | `archive/approximation-authority-v1` | candidate | a further extension would distinguish declared approximation authority from downstream exact algebra | product capability; contribution; shipped overlay |
| L26 | Representation invention | §4.4; §9 | `SCIENTIFIC_EXPERIMENTS_CLOSED.md` (historical) | unsupported as a positive claim | unestablished; campaign closed with insufficient adjudicable tasks; not a measured zero success rate | AI failed to invent representations; AI discovered representations |

---

## Prohibited claims (do not place in abstract, contributions, or results)

| ID | Claim | Why | Evidence status |
|---|---|---|---|
| P1 | 189 Guo equations verified | inventory ≠ verification | unsupported |
| P2 | Five papers fully audited | sampled 41 edges | unsupported |
| P3 | Approximation overlays are productized | not in `v0.3.0-alpha` schema | unsupported |
| P4 | LLM certifies mathematics / discovers the next formula | proposal ≠ verification | unsupported |
| P5 | The tool is a Lean/Coq/Isabelle replacement | different object | unsupported |
| P6 | The tool is a CAS that proves identities by simplification policy | simplify ≠ promotion policy | unsupported |
| P7 | All conceivable record forgery is impossible | threat-model tests only | unsupported |
| P8 | Held-out generalisation to unseen manuscripts | Guo shaped the IBP adapter | unsupported |
| P9 | Physical conclusions of Guo et al. are confirmed | out of scope | unsupported |
| P10 | Selected-edge 25/26 is the flagship public result | superseded by 189/189 inventory | unsupported as headline |
| P11 | `main` / `a10e4b5` is the software authority | tag freeze | unsupported |
| P12 | Shipped workspace `propose` command | not in `v0.3.0-alpha` | unsupported |
| P13 | Unpublished local manuscripts | privacy lock | prohibited |
| P14 | “No prior work has …” (exhaustive novelty) | Related Work not yet re-audited | **do not write until RW freeze**; prefer “we are not aware of prior work that combines …” after that audit |

---

## Contribution rows (must each hit a load-bearing claim)

| Contribution (draft-v3 §1) | Maps to | Strength cap |
|---|---|---|
| C1 one typed graph, two workflows | L1, L2 | demonstrated |
| C2 \(\tau\) vs \(c\); `ZERO` ≠ `CERTIFIED_BY_RULE` | L4, L6, L7 | implemented / demonstrated |
| C3 gated Forward; experimental proposer | L3, L11, L12, L13 | demonstrated with caveats |
| C4 audit + Guo inventory + five-paper sample | L14–L20 | depth demonstrated; breadth sampled; not a paper proof |

C4 must not be shortened to “we verify published papers.”

---

## Abstract sentence check (draft-v3)

| Abstract fragment | Row | Verdict for draft-v4 |
|---|---|---|
| one verified symbolic-reasoning framework / typed evidence graph | L1 | keep |
| claim semantics and certificate provenance are different axes | L6 | keep |
| candidates … only after independent fail-closed evidence | L2, L3 | keep |
| Forward … not autonomous representation invention | L12, L26 | keep |
| BZ IBP as `CERTIFIED_BY_RULE` rather than engine `ZERO` | L4 | keep |
| tested narrative and record manipulations cannot populate the table | L9 | keep **with** “under the implemented threat model” (already in sentence) |
| complete numbered-equation inventory … 189 of 189 | L14 | keep; do not add “verified” |
| then checks only source-grounded relations | L15 | keep |
| sampled five-paper stress test … without claiming five complete-paper proofs | L19 | keep |
| does not prove a paper or confirm physical conclusions | L20 | keep |
| An AI may propose … may not certify itself | L2 | keep (slogan, not a contribution) |

No abstract sentence currently asserts P1–P3. Do not let humanizer introduce them.

---

## draft-v3 wording to fix in draft-v4 (not in this pass)

These are not new experiments. They are lock compliance.

| Location | Issue | Required repair |
|---|---|---|
| §5.1 “Two independent read-only reviewers checked the public Guo transcription” | true of the selected-edge campaign; not restated as a flagship operator fact in `PAPER_AUTHORITY_LOCK.md` | drop, or cite the selected-edge precursor explicitly; do not imply a second independent review of all 189 transcriptions |
| §7 RQ1 still mentions historical Demo B/C in older tables | v0.3 public Forward examples are exact-step / refused-step | Table 6 must match `v0.3.0-alpha` examples; Demo B is not a product headline |
| §4 / §2 “Forward Mode” / “Retrospective Audit” | product names are Forward and Audit | lineage aliases OK once; default to product names |
| Related Work “Those lines of work do not, by themselves, …” | allowed; “no prior work has” is not | freeze after the RW re-audit; no exhaustive-novelty sentence before that |

---

## Number freeze (copy-paste only from the lock)

| Quantity | Value | May appear as |
|---|---|---|
| Guo inventoried equations | 189/189 | inventory coverage |
| Guo source-grounded relations | 146 | relations extracted / checked as typed claims |
| Guo executable numbered relations | 53 | executable residuals |
| Leibniz helper | 1 | not a numbered-equation row |
| `EXACT_ZERO` | 32 | exact local residuals |
| `ZERO_UNDER_SUBSTITUTION` | 21 | exact after declared substitution |
| `CERTIFIED_BY_RULE` | 11 | local `ZERO` + declared BZ rule |
| `UNKNOWN_REMAINDER` | 17 | remainder uncertified |
| `STRUCTURAL` | 47 | definitions / bookkeeping |
| `UNSUPPORTED` | 18 | not lowered |
| Guo false promotion | 0/155 | injected controls on the flagship relation set |
| Sample papers | 5 | sampled |
| Sample edges | 41 | sampled |
| Sample false promotion | 0/30 | injected invalids in that campaign |
| Forward replay false promotion | 0/36 | injected invalids in that campaign |

Do not invent a new count. If a figure needs a count not in this table, stop.

---

## Next allowed step

Related Work re-audit (external literature), organized by:

A. Certified / checked symbolic computation (producer vs checker)
B. Formal proof assistants (why not a kernel substitute)
C. Scientific workflow provenance (where vs what evidence)
D. LLM / agent scientific reasoning (proposal ≠ verification)
E. CAS / simplification (search ≠ promotion policy)

Until that audit is written, novelty language is capped at combination
claims already in L1, without “no prior work has.”
