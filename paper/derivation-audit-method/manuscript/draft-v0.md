# Machine-Auditable Derivation Verification for Theoretical Physics

*Working title. Alternative: Fail-Closed Verification of AI-Assisted Symbolic Derivations. Do not use “Autonomous Theoretical Physicist” or “AI Discovers Physics.”*

*Draft v0 — methods first draft from frozen public product `derivation-audit-v0.2.1-alpha` (SHA `783ec64`) and public evidence branch `engineering/real-paper-validation-arxiv-2511-16422` (SHA `69ad474`). This draft does not modify product semantics. Unpublished local manuscripts are excluded.*

---

## Abstract

Modern scientific workflows increasingly use AI systems and computer-algebra engines for long symbolic derivations. The generated explanation and the mathematical authority of a step are often conflated: a fluent identity, a model’s confidence, or a green-looking table can be mistaken for a certificate. We ask a narrower question: *how can AI-assisted symbolic derivations be made machine-auditable without granting the AI authority to certify its own claims?*

We present **Derivation Audit**, a fail-closed method that separates *proposal* from *authority*. A manuscript is inventoried into labelled equations, recorded as a typed derivation graph, and lowered to source-grounded executable obligations only where the encoding is honest. A deterministic exact verifier returns `ZERO`, `NONZERO`, or `UNKNOWN`. Certificates bind source, expression, assumptions, obligation, verifier, and result. Reviewer tables are generated from integrity-valid machine records and cannot be authored. Some global steps combine a local engine certificate with a declared theorem and domain; they receive `CERTIFIED_BY_RULE` and are never a fake engine `ZERO`.

We evaluate the method with public synthetic demonstrations, adversarial integrity tests, and an end-to-end field validation on a published theoretical-physics derivation (Guo et al., *Phys. Rev. Lett.* **136**, 206303 (2026), arXiv:2511.16422v2). Of 25 selected paper steps we report 19 machine `ZERO` rows (13 `DIRECT_EXACT`, 6 `SUBSTITUTION_EXACT`), 2 Brillouin-zone periodic integration-by-parts rule certificates, 1 asymptotic `UNKNOWN`, and 0 `NONZERO`. Certificate classes describe provenance, not a hierarchy of truth. This is an equation-level audit; it does not prove the paper or confirm its physical conclusions.

---

## 1. Introduction

The motivation for this work is not that large language models are “smart enough to do physics.” It is that they, and computer-algebra systems more broadly, are already inside the derivation loop.

A contemporary theoretical-physics calculation often mixes (i) handwritten algebra, (ii) a CAS rewrite, (iii) an AI-proposed rearrangement or substitution, and (iv) a prose argument that a remainder is small, a boundary term vanishes, or two expressions are “the same after relabeling.” Reviewers and later readers then face a practical problem that is not solved by another fluent paragraph:

- exactly which step was checked;
- what assumptions were used;
- whether the step was an exact identity, a substitution, a global theorem, or an asymptotic claim;
- what machine evidence supports it;
- how to reproduce it.

When those distinctions are missing, two failure modes appear. The first is **false certification**: an AI or a human writes “verified” into a table, a coefficient match is treated as a remainder proof, or an integral identity is faked by asking a CAS to simplify a symbol that it never integrated. The second is **false refutation**: a tool returns “cannot prove” and the user hears “wrong,” or a `NOT_LOWERED` encoding gap is reported as a scientific dead end.

Derivation Audit is an *audit layer* for that workflow. An AI or a researcher may propose a derivation. Only explicit, source-grounded machine evidence may certify a step. The verified table is generated, not authored. `UNKNOWN` is a first-class result and is never promoted for narrative convenience.

The method is intentionally weaker than a general-purpose proof assistant and intentionally stronger than a notebook that prints `True`. It does not claim to prove papers, discover physics, or certify physical conclusions. It claims that selected equation-level steps can be recorded, typed, checked, and reproduced with an explicit epistemic label.

**Contributions.**

- **C1.** A theoretical derivation is a typed graph, not a list of neighboring equation pairs treated as lhs–rhs equalities.
- **C2.** Exact obligations fail closed: `ZERO`, `NONZERO`, `UNKNOWN`.
- **C3.** Certificates bind source, expression, assumptions, obligation, verifier, and result.
- **C4.** Reviewer tables are generated from integrity-valid records; an LLM cannot author a verified row.
- **C5.** Theorem-mediated steps receive `CERTIFIED_BY_RULE`, not fake engine `ZERO`.
- **C6.** Certificate classes (`DIRECT_EXACT`, `SUBSTITUTION_EXACT`, `RULE_CERTIFICATE`, `STRUCTURAL`, `ASYMPTOTIC`/`UNKNOWN`) describe provenance, not truth ranking.
- **C7.** The frozen pipeline is exercised on a published theoretical-physics derivation without modifying the verifier core.

---

## 2. Problem Formulation

Let a manuscript \(M\) contain a finite set of labelled displayed equations \(E = \{e_i\}\) together with surrounding prose. A *derivation claim* is not “\(e_i\) equals \(e_{i+1}\) because they are printed next to each other.” It is a typed edge

\[
\gamma = (e_{\mathrm{from}}, e_{\mathrm{to}}, \tau, \rho, A)
\]

where \(\tau\) is an edge type (algebraic equivalence, index relabeling, definition insertion, asymptotic claim, Brillouin-zone integration by parts, …), \(\rho\) is an optional residual encoding, and \(A\) is a declared assumption set.

The audit problem is: produce, for each admitted \(\gamma\), a machine record \(R(\gamma)\) such that

1. a reviewer can re-run the same obligation on the same bytes;
2. the status cannot be upgraded by editing Markdown or by model prose;
3. the status is honest about what was actually checked.

We distinguish four kinds of claim (Figure 2):

| Kind | Typical encoding | Authority |
|---|---|---|
| Engine certificate | executable residual \(r\) | deterministic verifier |
| Rule certificate | local child certificate + declared theorem/domain | typed parent `CERTIFIED_BY_RULE` |
| Structural record | definition, split, bookkeeping | tracking, not proof |
| Uncertified claim | remainder, unsupported integral, parse/compile gap | `UNKNOWN` / `NOT_LOWERED` / failure statuses |

The object of verification is the *encoded residual under declared assumptions*, not the physical meaning of \(M\).

**Non-goals.** Full formalization of a manuscript in a proof assistant; verification that a conductivity formula describes a material; autonomous invention of a representation; a catalogue of every useful theorem in mathematical physics.

---

## 3. Threat Model: Why LLM Reasoning Cannot Certify Itself

Large language models can propose residuals, invent edge types, write “ZERO” in a table, and generate a convincing story about why an asymptotic remainder is negligible. None of those acts is a certificate.

We treat the following as in-scope adversaries or misuse (public threat model):

- an author or model writes `ZERO` / `VERIFIED` / `CERTIFIED` into Markdown or YAML;
- a `ZERO` record is forged without residual, obligation, and assumption hashes;
- source, residual, or assumption bytes are mutated after a claimed `ZERO`;
- an `UNKNOWN` row is relabelled `ZERO` without an engine `ZERO`;
- a `NONZERO` row is deleted from Markdown in the hope that it stays gone;
- a split parent is labelled certified while a child is uncertified;
- an asymptotic truncation is encoded as an exact identity to force a green row;
- a global integral is submitted as if a CAS had evaluated it.

The corresponding controls are mechanical. Tables are generated from inclusion predicates on integrity-valid records. Markdown `ZERO` is ignored. Status `ZERO` requires engine result `ZERO`. Split parents cannot be engine `ZERO`. Asymptotic claims cannot be engine `ZERO` without a remainder certificate. Rule-mediated parents cannot occupy the verified table. Regeneration from the bound run is the authority.

The threat model is not “the model might be wrong about physics.” It is “the model must not be able to *act as its own notary*.” Proposal authority and verification authority are different objects.

A second, independent threat is leakage of unpublished local scientific material into public artifacts. Public demos and public field validation must be synthetic or clearly public. Private acceptance is never release evidence.

---

## 4. Typed Derivation Representation

A derivation graph whose every edge is silently “lhs minus rhs” cannot describe theoretical physics. Neighboring equations may be a definition, a dummy-index relabeling, a projector identity, a pairwise cancellation inside a sum, a completeness insertion, a limit, an integral identity, or an asymptotic expansion. Forcing all of those into one residual type produces either fake `ZERO` or unreadable `UNKNOWN`.

Derivation Audit therefore uses a frozen catalogue of edge types. Lowering applicability is `SUPPORTED`, `PARTIAL`, or `NOT_APPLICABLE`. Default statuses are typed non-proof starting points (`NOT_LOWERED`, `DEFINITION`, `RECORDED`, `SPLIT`, `UNKNOWN`).

Examples:

- `ALGEBRAIC_EQUIVALENCE` — local residual `lhs - rhs`.
- `INDEX_RELABELING` — dummy-index rewrite of an identity.
- `PAIRWISE_REDUCTION` — local pair identity; a global sum is not swallowed.
- `DEFINITION_INSERTION` — name introduction; not a proof claim.
- `SPLIT_PARENT` — parent delegated to children; never itself `ZERO`.
- `ASYMPTOTIC_CLAIM` — global remainder; coefficient children may be `ZERO`.
- `INTEGRAL_ARGUMENT` — generic integral-level argument; not a local residual.
- `BZ_PERIODIC_INTEGRATION_BY_PARTS` — Brillouin-zone IBP with an explicit local Leibniz child and a declared torus-periodicity rule.

Selection rule: use the most specific type that matches the scientific claim. If the engine has no residual, the honest status is `NOT_LOWERED` or `UNKNOWN`, not a nearby algebraic encoding.

Equation inventory extracts labels, environments, order, and source ranges. It does not interpret LaTeX as algebra. Native-text members in `expressions/` are researcher-authored transcriptions. That transcription step is a stated limitation, not a hidden intelligence.

---

## 5. Source-Grounded Obligation Compilation

An executable edge is compiled into a proof obligation only after grounding:

1. **Workspace containment.** Paths are workspace-relative, use `/`, and must not contain `..` or symlinks.
2. **Source snapshot.** Manuscript bytes, equation and edge manifests, expression files, and assumptions are hashed.
3. **Grounding.** Each edge must bind to declared equation/expression sources. Failure is `GROUNDING_FAILURE`, not a guess.
4. **Assumption gate.** Declared symbols live in a small machine-enforced namespace (`real: true`, optional `nonzero`, named functions). Undeclared names are `ASSUMPTION_REQUIRED`. The gate does not discover which physical assumptions a paper “really needs.”
5. **Lowering.** Supported types produce a residual. Unsupported types remain typed and non-executable.
6. **Parse / compile.** Parser whitelist, token/depth/size limits, and the exact SymPy route bound what can be certified. Failure is `PARSE_FAILURE` or `COMPILE_FAILURE`.

The obligation is the residual bytes plus the assumption bytes plus the verifier route (`python_sympy_exact_v1`) plus the engine version (`0.3.0`). Changing any of those produces a new snapshot. Prior `ZERO` rows do not transfer silently.

Parameter identities that the assumption language cannot encode (for example \(\varepsilon_{21}=-\varepsilon_{12}\)) must be *substituted into the residual* and labelled as substitution provenance. They are not silently treated as engine-enforced laws.

---

## 6. Exact and Rule-Based Certificates

### 6.1 Engine certificates

The deterministic verifier returns:

- `ZERO` — exact symbolic simplification of the encoded residual to zero under the recorded route, namespace, and assumptions;
- `NONZERO` — an exact probe proved the residual nonzero;
- `UNKNOWN` — no proof either way.

`ZERO` certifies only the submitted residual. It does not certify novelty, physical usefulness, the rest of a manuscript, or a broader domain. `UNKNOWN` is not “likely true,” “likely false,” “partial success,” or permission to advance.

### 6.2 `ZERO ≠ CERTIFIED_BY_RULE`

Some scientifically real steps are not local residuals. Integration by parts on a Brillouin-zone torus is the motivating example: the local Leibniz product rule *is* a residual; the vanishing of the integral of a total \(k\)-derivative is a *theorem about a domain*.

Asking SymPy to return `ZERO` for \(\int_{\mathrm{BZ}} \partial_k(\cdots)\,d^dk\) would be a fake engine certificate. The honest parent status is `CERTIFIED_BY_RULE` when, and only when,

- a local child is integrity-ok engine `ZERO` (Leibniz);
- the researcher declares `BZ_TORUS_PERIODICITY` on domain `BRILLOUIN_ZONE_TORUS`;
- the declared rule applies to the IBP *integrand combination* (gauge-invariant / globally periodic). A gauge-dependent Berry connection is not automatically allowed because the BZ is a torus.

Missing periodicity is `ASSUMPTION_REQUIRED`. Missing local child is `NOT_LOWERED`. The parent never enters `TABLE_VERIFIED`.

The recorded certificate is structured:

```text
status: CERTIFIED_BY_RULE
rule_id: BZ_TORUS_PERIODICITY
local_children: [{edge_id, status: ZERO}]
requirements: {domain: BRILLOUIN_ZONE_TORUS, integrand_periodic: declared}
conclusion: integral_of_total_derivative = 0
```

### 6.3 Field-driven rule growth

Rule growth is field-driven. A named rule is added only when a real public derivation uses the step, the existing taxonomy cannot express it without a fake residual `ZERO`, and the mathematical conditions are explicit and fail-closed. Completeness, Stokes, Hermiticity, trace cyclicity, and similar operations stay untyped until field use exposes them. This paper does not propose a theorem-prover library.

### 6.4 Epistemic overlay

On top of machine statuses, a reviewer-facing overlay distinguishes:

- `DIRECT_EXACT` — unsubstituted engine `ZERO`;
- `SUBSTITUTION_EXACT` — engine `ZERO` after a declared upstream identity is written into the residual;
- `RULE_CERTIFICATE`;
- `STRUCTURAL`;
- `ASYMPTOTIC` / `UNKNOWN`.

The overlay cannot add a `ZERO` row. It tells the reviewer what the conclusion *depends on*. `SUBSTITUTION_EXACT` is not “less true” than `DIRECT_EXACT`; it is more explicit about an upstream identity the assumption language could not enforce.

---

## 7. Evidence Integrity and Generated Reviewer Tables

**Invariant.** `VERIFIED TABLE IS GENERATED, NOT AUTHORED.`

Inclusion is a function of a machine record:

1. `integrity_ok(record)`
2. `record.result == ZERO` and `record.status == ZERO`
3. `record.executable`
4. edge type is not `SPLIT_PARENT`
5. edge type is not `ASYMPTOTIC_CLAIM`

Markdown `ZERO` is ignored. Forged records without residual, obligation, assumptions hashes and a verifier route fail integrity and cannot enter `TABLE_VERIFIED`. Integrity failure always buckets as `TABLE_UNCERTIFIED`, even if labels say `ZERO`.

Buckets:

| Bucket | Contents |
|---|---|
| `TABLE_VERIFIED` | integrity-ok executable engine `ZERO` |
| `TABLE_NONZERO` | `NONZERO` |
| `TABLE_STRUCTURAL` | `DEFINITION`, `RECORDED`, `SPLIT`, `CERTIFIED_BY_CHILDREN`, `CERTIFIED_BY_RULE` |
| `TABLE_UNCERTIFIED` | `UNKNOWN`, `NOT_LOWERED`, parse/compile/grounding failures, asymptotic parents, integrity failures |

A reviewer package exports the bound run, generated tables, assumptions, obligations, `MANIFEST.json`, and `reproduce.sh`. Regenerating tables from that run is the authority. Deleting a `NONZERO` row from Markdown does not hide it.

Finite Laurent/series/coefficient `ZERO` is not a remainder proof. Coefficient children may occupy `TABLE_VERIFIED` on their own; the enclosing `ASYMPTOTIC_CLAIM` stays uncertified without a remainder certificate.

---

## 8. Implementation

The public product is `symbolic-compactification` **Derivation Audit** `0.2.1-alpha` (PEP 440 `0.2.1a0`), engine `0.3.0`, protocol `0.2.1`, immutable tag `derivation-audit-v0.2.1-alpha` at commit `783ec64`. Historical tag `derivation-audit-v0.2.0-alpha` remains at `aaf1199` and is not moved.

Command surface:

```text
ssc audit init | inventory | inspect | verify | table | report | package
```

v0.1 Mode A (`init` → `inspect` → `verify` → `report`) remains supported. Optional AI proposal is experimental, disabled under `SSC_PRIVATE_OFFLINE=1`, and cannot create `ZERO`.

Public synthetic demonstrations ship with the product:

- **Demo A.** Algebraic equation-to-equation identities → multiple `ZERO`.
- **Demo B.** Typed steps (index relabeling, projector, pairwise) plus `DEFINITION` / `RECORDED`.
- **Demo C.** Laurent coefficient `ZERO`, enclosing asymptotic remainder `UNKNOWN`.

Demo C is the intended soundness demo: the tool will not rewrite a remainder claim as an exact identity to force a green row.

The v0.2.1 patch is taxonomy-additive: it exposes `BZ_PERIODIC_INTEGRATION_BY_PARTS` and structured `CERTIFIED_BY_RULE` records. The exact-engine semantics of `ZERO` / `NONZERO` / `UNKNOWN` are unchanged. Public real-paper evidence lives on a separate branch and is not the product release.

---

## 9. Evaluation

No new experiment is introduced in this draft. Results below are existing public artifacts.

### 9.1 Synthetic / public demonstrations

Demos A/B/C exercise the public CLI (`inspect`, `verify`, `table`) on synthetic workspaces. A produces multiple algebraic `ZERO` rows. B shows that typed non-equality steps remain structural. C shows coefficient-level `ZERO` with parent `UNKNOWN`. These are documentation of the user contract, not a claim that a scientific paper has been proved.

### 9.2 Adversarial soundness tests

The following attacks are implemented as public tests (Table 3). They are central to the claim that an AI cannot certify itself.

| Attack | Outcome |
|---|---|
| LLM-authored `ZERO` in Markdown | ignored |
| Forged `ZERO` JSON without hashes | rejected |
| Source mutation | certificate identity changes |
| Assumption mutation | certificate identity changes |
| Residual mutation | certificate identity changes |
| Relabel `UNKNOWN` as `ZERO` | rejected |
| Hide `NONZERO` by editing Markdown | regeneration restores it |
| Split parent with uncertified child | cannot certify; never `ZERO` |
| Asymptotic truncation as exact equality | parent stays uncertified |
| BZ IBP parent as engine `ZERO` | `CERTIFIED_BY_RULE` or `ASSUMPTION_REQUIRED`, never `ZERO` |

These tests do not prove the absence of every possible encoding cheat (a human can still transcribe the wrong identity on both sides). They prove that the *table machinery* does not accept narrative, forgery, or remainder promotion as certification.

### 9.3 Published theoretical-physics field validation

**Statement.** The Derivation Audit pipeline has been exercised end-to-end on a published theoretical-physics derivation.

**Source.** Zhichao Guo, Xing-Yuan Liu, Hua Wang, Li-kun Shi, and Kai Chang, “Dissipation-Shaped Quantum Geometry in Nonlinear Transport,” *Phys. Rev. Lett.* **136**, 206303 (2026), arXiv:2511.16422v2. Public authority is the arXiv v2 source. The PDF and source tarball are not committed; they are reconstructed from bibliographic `SOURCE.yaml`.

**Evidence object.** Git branch `engineering/real-paper-validation-arxiv-2511-16422` at `69ad474`, workspace `examples/real_papers/arxiv_2511_16422/`. This is evidence, not product source. The product tag does not contain that workspace.

**Scope.** Selected supplement edges, primarily Appendix D algebraic chain, plus Appendix B split/bookkeeping, Appendix E a stated identity recorded as definition, one \(\Gamma\) asymptotic remainder, and two Brillouin-zone IBP parents. Printed HTML/PDF equation numbers do not reset per appendix; local `D-1` is printed `(D-57)`. Reviewer tables cite printed numbers.

**Approved public metrics** (25 selected paper steps):

| Quantity | Count |
|---|---|
| Selected paper steps | 25 |
| Machine `ZERO` | 19 |
|  `DIRECT_EXACT` | 13 |
|  `SUBSTITUTION_EXACT` | 6 |
| `RULE_CERTIFICATE` (BZ periodic IBP) | 2 |
| Asymptotic `UNKNOWN` | 1 |
| `NONZERO` | 0 |

A shared local Leibniz product-rule child is a machine helper for both IBP parents. It is one of the 13 `DIRECT_EXACT` rows and is not an additional paper step.

**What the classes mean here.**

- *Direct residual equality.* Example: (D-59)→(D-60) regroup of \(K_{1A}\) is an unsubstituted local identity and returns engine `ZERO`.
- *Explicit substitution equality.* Example: (D-66)→(D-67) is `ZERO` *given* \(\varepsilon_{21}=-\varepsilon_{12}\) written into the residual. The tool does not independently prove that Levi-Civita identity; it certifies the remaining algebra. Other substitutions: metric-velocity pair, \(\Omega_{ab}^{1}\) definition, \(\Omega^{2}=-\Omega^{1}\), \(f_n'=2f_{0,n}'\).
- *BZ periodic IBP rule certificate.* (D-114)→(D-119) and (D-123)→(D-124) are `CERTIFIED_BY_RULE` with local Leibniz `ZERO` and declared `BZ_TORUS_PERIODICITY` on `BRILLOUIN_ZONE_TORUS`. SymPy did not evaluate \(\int_{\mathrm{BZ}}\). Without the declaration the parents would be `ASSUMPTION_REQUIRED`.
- *Asymptotic remainder deliberately remaining `UNKNOWN`.* (D-57) is typed `ASYMPTOTIC_CLAIM`. It is not rewritten as “truncated series equals the object.” The remainder stays `UNKNOWN`.

**Honesty about lineage.** The field validation began on frozen `v0.2.0-alpha`. The two IBP parents were originally an encoding gap (`NOT_LOWERED`), not a mathematical dead end. The generic adapter (`CERTIFIED_BY_RULE` + `BZ_PERIODIC_INTEGRATION_BY_PARTS`) is the `v0.2.1-alpha` product patch. The verifier core (`ZERO`/`NONZERO`/`UNKNOWN`, engine `0.3.0`) was not redesigned. Historical tag `v0.2.0-alpha` was not moved.

**Boundary sentence, repeated on purpose.** This is an equation-level audit and does not prove the paper or confirm its physical conclusions.

---

## 10. Limitations

The method is an alpha audit layer. The following are in-scope boundaries, not punch-list bugs:

- Inventory does not understand PDFs. Native-text transcription is manual.
- Many scientifically real steps have no supported residual (`NOT_LOWERED`).
- Generic integrals, exact limits, and asymptotic remainders are not certified.
- The machine-enforced assumption namespace is small. Positivity, excluded poles, parameter identities, symmetries, and limit order are not operational assumptions.
- `ASSUMPTION_REQUIRED` detects undeclared names / missing declared rules. It does not invent the physically necessary hypotheses.
- Abstract band sums are not auto-cancelled; the public Guo audit used two-band scalars where that was the paper’s reduction.
- Parser whitelist and size limits bound the certificate surface.
- Manual transcription can encode the wrong identity (detected as `NONZERO`, or missed if both sides are wrong the same way).
- `UNKNOWN` can still be misread as support by a human. The software cannot stop that misreading; it can refuse to emit a verified row.

We do not treat these limitations as an invitation to grow a twenty-rule theorem prover in order to make a methods paper look broader.

---

## 11. Discussion

**Proposal versus authority.** The useful role of an AI in this workflow is to propose typed edges, draft residuals, and point at likely substitutions. The dangerous role is to notarize its own output. Derivation Audit makes the second role structurally unavailable: there is no API by which model text becomes `TABLE_VERIFIED`.

**Provenance, not ranking.** It is tempting to present `DIRECT_EXACT > SUBSTITUTION_EXACT > RULE_CERTIFICATE > UNKNOWN` as a credibility ladder. That is the wrong picture. A substitution-exact row can be the scientifically central identity. A rule certificate can be the only honest encoding of a standard theorem. An `UNKNOWN` remainder can be the most important scientific caveat. The labels exist so a reviewer can see the *evidence chain*.

**Field-driven growth.** The BZ IBP adapter exists because a published PRL supplement used that step and the frozen v0.2 taxonomy could only say `NOT_LOWERED`. That is the intended evolution: ship; a real paper exposes a gap; apply a generic minimal fix; preserve provenance. Speculative catalogues (`STOKES`, `HERMITICITY`, `COMPLETENESS`, …) would invert the method: they would invite fake `ZERO` in the name of coverage.

**Relation to proof assistants and CAS.** Lean, Coq, and Isabelle certify theorems in a trusted kernel; they require a different encoding investment than a manuscript audit. SymPy and commercial CAS systems evaluate expressions but do not, by themselves, bind a printed equation number to a hashed residual and a generated reviewer table. Derivation Audit sits between those traditions: weaker than a kernel, stricter than a notebook.

**What would constitute a second case.** Another *public* theoretical-physics derivation, audited without changing engine semantics, that either (i) fits the existing taxonomy or (ii) exposes one new generic adapter with explicit fail-closed conditions and human authorization. Unpublished local work is not that case.

---

## 12. Conclusion

An AI may propose a derivation. Only explicit, source-grounded machine evidence may certify it.

Derivation Audit records theoretical-physics calculations as typed graphs, lowers only honest residuals, fails closed on `UNKNOWN`, binds certificates to hashed provenance, generates reviewer tables that cannot be authored, and distinguishes local engine `ZERO` from theorem-mediated `CERTIFIED_BY_RULE`. A public field validation on Guo et al. (2026) shows that this discipline is usable on a published derivation without pretending to have proved the paper.

Engineering for v0.2 is closed. The next scientific object is this methods manuscript, not a broader verifier.

---

## Appendix A. Schemas and versions

| Identity | Value |
|---|---|
| Package | `0.2.1-alpha` / PEP 440 `0.2.1a0` |
| Engine | `0.3.0` |
| Audit protocol | `0.2.1` |
| Schema | `DerivationAuditV1` |
| Verifier route | `python_sympy_exact_v1` |
| Product tag | `derivation-audit-v0.2.1-alpha` @ `783ec64` |
| Historical tag | `derivation-audit-v0.2.0-alpha` @ `aaf1199` |

See public `docs/STATUS_SEMANTICS.md`, `docs/EDGE_TYPES.md`, `docs/RULE_CERTIFICATES.md`.

## Appendix B. Status semantics (condensed)

See Table 1 in `tables/table1-status-semantics.md`. Invariant: only integrity-ok executable `status == result == ZERO` rows enter `TABLE_VERIFIED`. `CERTIFIED_BY_RULE` is never displayed as `ZERO`.

## Appendix C. Reproduction

Product:

```bash
git clone --branch derivation-audit-v0.2.1-alpha \
  https://github.com/DarrenWongKaWa/symbolic-compactification.git
```

Evidence:

```bash
git clone --branch engineering/real-paper-validation-arxiv-2511-16422 \
  https://github.com/DarrenWongKaWa/symbolic-compactification.git
cd examples/real_papers/arxiv_2511_16422 && ./reproduce.sh
```

Adversarial tests: `pytest tests/test_audit_adversarial.py tests/test_audit_schema.py tests/test_audit_tables.py tests/test_audit_bz_ibp.py`.

## Appendix D. Additional public audit rows

The unified evidence table on the evidence branch (`reports/TABLE_EVIDENCE.md`) lists each selected paper step with certificate class, machine child, declared rule/assumption, and status. That file is generated from `verification_table.json` plus a non-authoritative overlay. It cannot create `ZERO`.

---

## Draft notes (not for submission)

- Target venue is unset. Keep claim boundaries intact regardless of venue.
- Figures 1–4 are specified; artwork is not yet drawn to journal SVG/PDF.
- Related-work bibliography is a seed, not a complete literature review.
- Do not add a second paper, a new rule, or a product patch to “strengthen” §9.
