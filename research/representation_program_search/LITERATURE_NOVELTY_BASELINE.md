# Literature and novelty baseline

Status: **PRELIMINARY METHOD BOUNDARY — NOT A NOVELTY CLAIM**  
Audit date: 2026-08-30  
Source policy: primary papers / official proceedings only

This ledger prevents the experiment from claiming novelty for established
ingredients. It must be expanded and independently reviewed after held-out
results exist. A distinctive combination is not itself a publishable novelty
unless it demonstrates a new, replicated, held-out capability.

## Closest method families

### Program synthesis and learned search

- **DeepCoder** (Balog et al., ICLR 2017) learns to predict program properties
  that guide search over a domain-specific language. It is prior art for
  neural guidance of bounded program synthesis; neither a grammar nor learned
  state/action ranking is novel here. Primary record:
  <https://openreview.net/forum?id=ByldLrqlx>.
- **DreamCoder** (Ellis et al., PLDI 2021) jointly learns reusable library
  components and a neural search policy under a probabilistic program grammar,
  using an MDL/Bayesian compression objective and e-graph-based refactoring.
  It is direct prior art for latent abstraction/library induction, reuse-aware
  complexity, and neural guidance. DOI: <https://doi.org/10.1145/3453483.3454080>;
  author manuscript:
  <https://people.csail.mit.edu/asolar/papers/EllisWNSMHCST21.pdf>.
- **FunSearch** (Romera-Paredes et al., Nature 2024) couples LLM-generated
  programs, evolutionary search, program skeletons, and a systematic
  evaluator. It is direct prior art for LLM-guided mathematical program search
  with machine evaluation. The present experiment differs operationally by
  restricting the LLM to auditable legal actions or rankings and by making
  exact symbolic equivalence a hard certification gate, but those differences
  are not presumed novel or important before results. DOI:
  <https://doi.org/10.1038/s41586-023-06924-6>.

### Equality saturation and representation sharing

- **Equality saturation** (Tate et al., POPL 2009) represents many equivalent
  programs simultaneously and delays extraction, avoiding destructive phase
  ordering. It is prior art for preserving alternative representations during
  optimization. Author manuscript:
  <https://www.cs.cornell.edu/~lerner/papers/popl09.pdf>.
- **egg** (Willsey et al., POPL 2021) supplies fast, extensible e-graphs and
  e-class analyses for equality-saturation workloads, including synthesis and
  optimization. It is prior art for rewrite-space management and analyses;
  adding an e-graph would not itself be novel. DOI:
  <https://doi.org/10.1145/3434304>.

### Neural theorem proving and verifier feedback

- **CoqGym / ASTactic** (Yang and Deng, ICML 2019) generates tactics as AST
  programs in a predefined grammar and interacts with a proof assistant that
  returns new goals. It is close prior art for learned structured actions plus
  formal-system feedback. Primary paper:
  <https://proceedings.mlr.press/v97/yang19a/yang19a.pdf>.
- **GPT-f** (Polu and Sutskever, 2020) studies language-model generation of
  original mathematical terms inside an automated prover for Metamath; its
  successful proofs are checked by the formal system. It is prior art for
  language models proposing formally checkable mathematical steps. Primary
  record: <https://arxiv.org/abs/2009.03393>.
- **AlphaGeometry** (Trinh et al., Nature 2024) combines a neural language
  model with a symbolic deduction engine for olympiad geometry. It is prior
  art for neuro-symbolic mathematical search and machine-checked deductions.
  DOI: <https://doi.org/10.1038/s41586-023-06747-5>.

### Symbolic regression and scientific equation discovery

- **SINDy** (Brunton, Proctor, and Kutz, PNAS 2016) identifies governing
  equations by sparse regression over a supplied candidate-function library.
  It is prior art for library-constrained scientific equation discovery and a
  warning that the library can supply the answer. DOI:
  <https://doi.org/10.1073/pnas.1517384113>.
- **AI Feynman** (Udrescu and Tegmark, Science Advances 2020) combines
  physics-inspired transformations with symbolic regression to recover
  analytic expressions. It is prior art for structural heuristics in equation
  discovery. DOI: <https://doi.org/10.1126/sciadv.aay2631>.

### Anti-unification and abstraction

- Syntactic and higher-order **anti-unification** formalize least-general
  generalization and abstraction over terms. The maintained survey by Cerna
  and Kutsia (IJCAI 2023) establishes a broad prior-art family relevant to LGG,
  member grouping, and latent schemas. Primary proceedings paper:
  <https://www.ijcai.org/proceedings/2023/0736.pdf>.

## Claims prohibited by this baseline

Absent stronger evidence and a final independent novelty review, do not claim
novelty for:

- grammar-constrained or typed program search;
- enumeration, random search, beam search, best-first search, A*, or MCTS;
- learned/LLM ranking of states or prediction of next actions;
- an evaluator or proof checker in the loop;
- exact symbolic verification;
- e-graphs or equality saturation;
- reuse/description-length penalties;
- latent function or library induction;
- structural heuristics or symbolic regression;
- the mere combination of an LLM with a verifier.

## Potentially distinctive empirical question

The defensible question is narrower: on fresh, assumption-complete scientific
expression families, does a controlled mathematical representation grammar
enable exact R3+ programs, and under an identical legal frontier and matched
state budget does an LLM improve navigation beyond enumeration, random search,
symbolic heuristics, frozen SOL observations, and verifier-only feedback?

Even a positive answer establishes an empirical capability result first. A
novelty claim requires the final literature audit to show that the exact causal
decomposition, benchmark, or demonstrated scientific capability is absent
from prior work.
