# R8 Final Review — Systems Architecture

Reviewer role: independent systems-architecture reviewer  
Authority inspected: `e5b3694` (final gate decision at `b542567`, binding
scientific authority `a7ad6ab`)  
Review mode: read-only architecture audit; no scientific search, live model
call, parser/verifier change, or repository restructuring

## Recommendation

**Publication decision: F — STRUCTURED SEARCH ALSO FAILS TO SUPPORT
REPRESENTATION INVENTION.**

The qualifier is essential: this is a failure-to-support verdict for the
closed experiment, not an empirical failure of S0–S7 or F0. The mandatory DEV
suite was not assembled, no scientific condition ran, and no TEST freeze
exists. The software stack is a substantial, fail-closed research prototype;
it is not evidence that representation search, AI guidance, verifier feedback,
or SOL is a supported user capability. A–D require scientific method or system
evidence that was not generated, while E would add an unsupported positive
assessment of promise.

## Evidence and independent checks

I inspected the frozen contracts; M1 model, schema, canonicalization, loader,
and compiler; the public-case firewall; S0/S1, S2, S3, S4/S5, S6, S7, and F0
boundaries; the atomic condition runner and aggregation layer; the existing
`ssc` CLI; the core verifier/session pipeline; the open `real:false` namespace
defect; and `audits/dev_gate_final/GATE_AUDIT.{md,json}`.

The tree contains no RPS `DEV_MANIFEST.json`, `TEST_MANIFEST.json`,
`FREEZE_MANIFEST.json`, scientific `JOB_MANIFEST.json`/`JOB_RESULT.json`, or
LLM search-result/run-header artifact. This agrees with the gate prohibition
on scientific runs and live LLM calls.

I independently ran the focused M1, S0–S7, F0, runner, aggregation, and final
gate tests: **151 passed in 187.08 seconds**. This establishes software
conformance on the exercised paths only; it is not a scientific evaluation.

## Architectural assessment

The strongest architectural property is separation of authority:

1. A hash-bound public proposer view excludes reference programs, evaluator
   fields, verification artifacts, and hidden target labels.
2. Search creates only typed legal states from a finite public candidate pool.
3. M1 compiles a program into explicit exact obligations but emits no proof
   verdict.
4. Persisted verifier sessions alone produce ZERO/NONZERO/UNKNOWN and promote
   only ZERO.
5. The one-condition runner consumes a separate hash-bound clearance receipt,
   writes method-native evidence, preserves exceptions as `METHOD_ERROR`, and
   atomically publishes a completed job directory.
6. Aggregation excludes unavailable or inadmissible records from scientific
   denominators.

That is a sound research-control architecture. It reduces silent leakage,
state ambiguity, and result laundering. It does not establish that the
candidate language covers the intended mathematics or that any search policy
can discover useful programs.

## Evidence-based component dispositions

| component | disposition | supported boundary |
|---|---|---|
| Exact parser/verifier/session/promotion pipeline | **KEEP_CORE** | Exact fail-closed adjudication and persisted ZERO-only promotion are established repository capabilities. Keep the open `real:false` contract defect explicit; affected complex-domain cases require a separately versioned migration and replay. |
| ScientificAssumptionContract and assumption audit | **KEEP_CORE** | Explicit DECLARED/DERIVED/NOT_DECLARED semantics remain necessary. The compiler checks statuses used by a program, while completeness is an external audited clearance; do not describe compilation alone as assumption certification. |
| Source grounding, exact member hashes, and obligation provenance | **KEEP_CORE** | Exact source references and non-fuzzy binding are reusable controls. ZERO establishes the bound equality, not representation discovery. |
| Existing observation layer, B9/LGG, and Beyond-LGG graph | **KEEP_BASELINE** for frozen comparisons; **KEEP_DIAGNOSTIC** where historically non-operational | Preserve their frozen authorities and labels. TYPE_ONLY and reachability evidence must not be promoted to operational search capability. |
| M1 Program IR and constructor | **KEEP_DIAGNOSTIC** / experimental infrastructure | Deterministic JSON, alpha-normalized hashing, source hashes, repeated nodes, explicit operator outputs, and exact obligations are implemented. Do not promote to core until fresh admissible cases exercise it beyond known/reference constructions. |
| `RepresentationGrammarV1` | **KEEP_DIAGNOSTIC** / frozen experiment artifact | Its scalar operations are executable and ablations are enforceable. The grammar was not scientifically validated for R3+, and named latent forms do not by themselves supply matrix, tensor, noncommutative, block, integral, trace, or determinant semantics. |
| S0 random | **KEEP_BASELINE** | Matched finite-frontier random control is implemented; no scientific outcomes exist. |
| S1 enumerative | **KEEP_BASELINE** | Deterministic increasing-cost traversal of the generated finite frontier is implemented. Call it bounded enumeration, never exhaustive enumeration of all grammar programs. |
| S2 symbolic beam | **KEEP_DIAGNOSTIC** | Frozen public-structure heuristic and full-frontier beam are implemented. No effectiveness result exists. |
| S3 SOL-conditioned search | **KEEP_DIAGNOSTIC** | Frozen replay/authority boundary exists; it remained scientifically unavailable because no eligible case-bound replay ran. Historical SOL evidence remains separate and mixed/negative. |
| S4 LLM state ranker and S5 LLM action proposer | **KEEP_DIAGNOSTIC** | Legal-output, final-only, token/provenance, fallback, and matched-batch controls are software-tested with mocks. No live scientific LLM decision exists. |
| S6 verifier-in-the-loop search | **KEEP_DIAGNOSTIC** | Exact four-class feedback and session evidence are implemented. No scientific run tests whether feedback improves discovery. The core verifier remains core; this search controller does not. |
| S7 LLM + verifier | **KEEP_DIAGNOSTIC** | The matched verifier-only batch control and auditable LLM role are implemented. No scientific or live-model evidence supports the combined method. |
| F0 old free-form architecture | **KEEP_BASELINE** | Retain for historical comparison. Its strict translator covers only unambiguous specialization programs, and its no-state-budget semantics prevent a nominally matched state-expansion comparison. |
| Atomic runner and statistical aggregation | **KEEP_DIAGNOSTIC** / reusable research infrastructure | Hash-bound one-condition jobs, atomic publication, explicit unavailable states, Wilson intervals, and censoring-aware summaries are implemented. No scientific records exercised the reporting estimands. |
| Guo pipelines and sealed G3 evidence | **ARCHIVE** with **KEEP_DIAGNOSTIC** access | Preserve immutable evidence and compatibility; do not expose a new search route or reopen assumptions. |
| Remainder certifier | **KEEP_DIAGNOSTIC** | Retain the exact boundary that finite coefficients plus UNKNOWN remainder do not imply an exact limit. It is not part of this search method. |

## Program IR and grammar limits

M1 is appropriately described as a typed constructor at the repository's
current symbolic level. It validates identifiers, explicit graph links,
allowed arguments, node multiplicity, ablation membership, source paths and
hashes, and declared assumption references. Canonical identity excludes
scores, timestamps, and LLM traces; bound latent parameters receive limited
alpha normalization.

Three qualifications prevent a stronger architecture claim:

- The latent-form tags are not a complete mathematical type system. In
  particular, `MATRIX_FUNCTION`, `TENSOR_GENERATOR`, and `BASIS_OBJECT` are not
  accompanied by general matrix/noncommutative/index/contraction semantics.
  The R6 feasibility audit's `PACKAGING_GAP` is consistent with this boundary.
- A canonical program hash is canonical for the serialized IR under the
  implemented alpha normalization, not a semantic normal form for equivalent
  mathematical programs.
- Compatibility with early `RPSCasePackageV1` artifacts is inspectable but
  intentionally not silently executable: the loader records missing output
  links and legacy hash deltas, then compilation fails closed. This is a good
  safety choice, but it is not full backward execution compatibility.

Accordingly, Program IR and Grammar V1 should remain in the frozen research
namespace. They may inform a future Scientific IR design, but should not be
advertised as a general matrix/tensor representation engine.

## Search and evaluation limits

The search implementation consistently records incompleteness. S0/S1 share a
finite syntax-derived candidate pool with fixed caps; S2 is a width-32 beam;
S4/S5 and S7 see first-32 batches; the matched S2 and S6 controls are required
for causal attribution. These controls are architecturally valuable, but the
word “enumerative” must always be qualified by the generated finite frontier.

The V2 frontier repair occurred before scientific execution and restored
generic legal reachability for known diagnostic paths. It does not demonstrate
search discovery. Because those paths informed reachability engineering, they
and close variants must remain diagnostics in any future method version.

The runner's clearance receipt is an explicit trust boundary: it validates
the receipt bytes and embedded audit SHA formats, then trusts the independent
clearance authority. It does not itself redo scientific admission, assumption,
or leakage review. That separation is acceptable, but any future coordinator
or CLI must expose it rather than present the runner as a self-contained
scientific gate.

## CLI disposition

Do not add `ssc search`, `ssc benchmark`, `--search llm-*`, or an AI-guided
mode from this experiment. Those names would convert software prototypes into
apparent supported capabilities despite zero scientific condition runs.

Keep the existing exact-verification and session commands as the supported
surface. Existing observation commands may retain their historically bounded
meaning. Do not add `ssc ground` until the grounding and assumption-clearance
authorities have one coherent, versioned public contract. A replay command may
be considered only if it is a byte-exact, non-mutating replay of existing
evidence and makes no search-capability claim; this experiment does not require
one.

If the research code remains callable, expose it only as an explicitly
experimental Python namespace or an internal research harness. The condition
runner should not be installed as the default end-user search API.

## Repository architecture and compatibility

Repository-wide restructuring is **not safe or justified at closure**.
Moving frozen historical studies, packages, sessions, or manifests would risk
breaking byte hashes, relative provenance, and replay. Creating top-level
`representation/grammar/program_ir/search/heuristics` packages now would also
encode an unsupported forward architecture as if the method had survived
scientific evaluation.

Recommended closure architecture:

- leave `src/symbolic_compactification/` as the exact verifier/session core;
- leave RPS implementation and evidence under
  `research/representation_program_search/`;
- preserve historical research trees and hashes in place;
- use read-only compatibility loaders or wrappers when old artifacts must be
  inspected;
- never repair missing legacy IR links or scientific assumptions by inference;
- defer extraction into a core representation package until a new, separately
  versioned experiment has fresh admissible cases and demonstrates an actually
  used semantic subset.

The post-closure repertoire can document a layered *aspiration*, but its
machine-readable capability registry must distinguish `SUPPORTED`,
`IMPLEMENTED_UNEVALUATED`, `BASELINE`, `DIAGNOSTIC`, and `UNSUPPORTED_CLAIM`.
It must not label Program IR, S0–S7, or AI-guided search `SUPPORTED` merely
because their tests pass.

## Software-versus-science claim audit

| claim | verdict |
|---|---|
| “A deterministic, auditable representation-search harness was implemented.” | Supported as software. |
| “The exact verifier remains the only certification authority.” | Supported, subject to its documented domain/namespace contract and fail-closed outcomes. |
| “One known public-source R2 reference program is expressible and exactly certified.” | Supported; not search discovery. |
| “Grammar V1 supports general matrix/tensor representation programs.” | Unsupported; several forms are nominal and R6 is a packaging gap. |
| “S1 exhaustively searches RepresentationGrammarV1.” | Unsupported; it exhausts only the bounded generated frontier. |
| “S0–S7 and F0 execute correctly on the intended scientific benchmark.” | Unsupported; the mandatory benchmark gate blocked. |
| “LLM decisions are production-tested and useful.” | Unsupported; only mocked dispatch/interface tests exist. |
| “Verifier feedback or SOL improves search.” | Not evaluated. |
| “The repository now offers representation search through `ssc`.” | False; no such supported CLI exists, and none should be added at closure. |
| “The RPS architecture is ready to replace the historical repertoire.” | Unsupported; preserve it as experimental/diagnostic infrastructure. |

## Principal architecture risks to retain in the final reports

1. The executable symbolic IR is materially narrower than the named grammar
   forms, especially for R6 matrix/operator/tensor science.
2. The benchmark packaging/admission interface failed before method execution,
   including a mismatch between evaluator-only traps and the required runnable
   scientific negative slot.
3. The finite candidate pool and beam/batch caps make all search conditions
   incomplete; matched controls are mandatory for any future AI attribution.
4. The `real:false` parser contract defect can collapse complex-domain
   Piecewise branches or make documented declarations inconsistent. It failed
   closed here but prevents an unqualified “assumption semantics are complete”
   system claim.
5. Exact diagnostic/reference-program ZERO receipts validate construction and
   verification only. Treating them as discovered programs would collapse the
   evaluator/search boundary.
6. F0 and formal search do not share the state-expansion budget unit, so future
   comparisons require an explicitly different common-cost analysis.

## Final R8 recommendation

Issue **Publication F**, with this systems qualifier:

> A carefully separated, fail-closed representation-search research harness
> was implemented, but its mandatory fresh scientific calibration interface
> could not supply the required R3–R6 suite. No search condition received a
> scientific trial. Preserve exact verification, assumptions, and grounding as
> core; retain Program IR, Grammar V1, S0–S7, the runner, and F0 as frozen
> experimental or baseline artifacts; do not add a search CLI or restructure
> the repository around an unevaluated method.

