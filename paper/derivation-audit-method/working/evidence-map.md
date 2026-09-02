# Evidence Map (paper-writer working file)

| ID | Source | Level | Supports | Cannot support | Planned use | Risk |
|---|---|---|---|---|---|---|
| E-user-draft0 | manuscript/draft-v0.md | L1 | prior draft claims, frozen metrics, method description | venue choice | rewrite | none |
| E-user-freeze | CLAIMS.md, CONTRIBUTIONS.md, user five-act brief | L1 | titles, RQs, Guo counts, claim boundaries | new experiments | whole paper | none |
| E-guo-report | evidence branch VALIDATION_REPORT.md / TABLE_EVIDENCE.md | L1 | 25/19/13/6/2/1/0, printed eq numbers, IBP, D-57 | physics conclusions of Guo | running example, RQ3 | none |
| E-product | docs/STATUS_SEMANTICS.md, RULE_CERTIFICATES.md, tests/test_audit_adversarial.py | L1 | statuses, inclusion rules, attack tests | unstated software internals | §4–6 | none |
| E-sympy | Meurer et al., PeerJ CS 2017, doi:10.7717/peerj-cs.103 | L3 | CAS exists as scientific Python library | how physicists use it | Intro, RW | metadata-only |
| E-jupyter | Kluyver et al., ELPUB 2016, doi:10.3233/978-1-61499-649-1-87 | L3 | notebooks mix code, results, prose | notebook failure modes | Intro, RW | metadata-only |
| E-cot | Wei et al., NeurIPS 2022 | L3 | LLMs emit intermediate reasoning | math accuracy numbers unless quoted from abstract | Intro, RW | metadata-only |
| E-minerva | Lewkowycz et al., arXiv:2206.14858, 2022 | L3 | LM quantitative reasoning without external tools | “nearly a third” from abstract only | Intro | L2 if abstract used |
| E-halluc | Ji et al., ACM Comput. Surv. 55(12), 2023, doi:10.1145/3571730 | L3 | NLG hallucination is a documented failure | scientific-derivation rates | Intro | metadata-only |
| E-funsearch | Romera-Paredes et al., Nature 625, 468–475, 2024 | L2 (abstract) | pairs LLM with systematic evaluator | cap-set sizes | Intro, Discussion | no numbers beyond abstract |
| E-alphageo | Trinh et al., Nature 625, 476–482, 2024 | L2 (abstract) | neuro-symbolic geometry prover; computer-checked proofs | IMO counts in body | Intro, RW | abstract numbers only if used |
| E-lean | de Moura et al., CADE 2015 | L3 | Lean trusted kernel, interactive+automated | Lean 4 details | Intro, RW | metadata-only |
| E-isabelle | Nipkow, Paulson, Wenzel, LNCS 2283, 2002 | L3 | Isabelle/HOL proof assistant | HOL encoding of physics | RW | metadata-only |
| E-leandojo | Yang et al., NeurIPS 2023 | L3 | LLM theorem proving in Lean | benchmark sizes unless from abstract | RW | metadata-only |
| E-fair | Wilkinson et al., Sci. Data 3, 160018, 2016 | L3 | FAIR is about data reuse by machines | derivation-step audit | RW, Discussion | metadata-only |
| E-guo-pub | Guo et al., PRL 136, 206303 (2026); arXiv:2511.16422v2 | L1 user + L3 arXiv | public field-validation source | we did not re-derive their physics | RQ3 | cite as application, not as our result |

L4 model memory is not in this map.
