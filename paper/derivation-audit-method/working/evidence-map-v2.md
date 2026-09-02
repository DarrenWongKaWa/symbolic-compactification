# Evidence map v2 (paper-writer Phase 2)

| ID | Source | Level | Supports | Cannot support | Planned use | Risk |
|---|---|---|---|---|---|---|
| E-user-brief | user restructuring brief (two modes, claim bounds, Guo accounting) | L1 | story, RQs, MAY/MUST NOT | new numbers | whole paper | none |
| E-product-tag | tag `v0.3.0-alpha` peel `f1d225e` | L1 | package 0.3.0-alpha, engine 0.3.0, Forward+Audit CLI, schema | later `main` hygiene | Methods, Implementation | do not cite `main`; engine unchanged |
| E-readme | `README.md` on product tree | L1 | Mode A workflow; audit workflow; proposer experimental | discovery rates | §4, §6 | none |
| E-cap | `CAPABILITY_BOUNDARY.md` | L1 | experimental proposer; unestablished invention; no RAG | — | §4.4, Discussion | none |
| E-closed | `SCIENTIFIC_EXPERIMENTS_CLOSED.md` | L1 | representation campaign closed | "AI failed to invent" as a measured null | limitations | do not report zero success rate |
| E-neg | `NEGATIVE_RESULTS.md` | L1 | NR-004 remainder; NR-001 invention unsupported | Mode A gating failure | Discussion | Guo G3 NR-003 is not Mode A |
| E-sem | `docs/STATUS_SEMANTICS.md`, `EDGE_TYPES.md`, `RULE_CERTIFICATES.md`, `THREAT_MODEL.md` | L1 | tokens, two axes, inclusion, threats | schema vs docs mismatch on CBR bucket row | §3, §6 | schema.py normative |
| E-schema | `src/symbolic_compactification/audit/schema.py` | L1 | `may_appear_in_verified_table`, `table_bucket`, CBR exclusions | — | App B | do not edit |
| E-modeA-demos | `engineering/release_v0_1/DEMOS.md`, three demo workspaces | L1 | ZERO/ZERO/UNKNOWN; no proposer | multi-step physics derivation | RQ1, Fig 3 | one-shot |
| E-modeA-retest | `EXTERNAL_USER_FINAL_RETEST.md` | L1 | mutation NONZERO residual `-1`, counterexample `x=-2` | live-LLM | RQ1 | not a second demo tree |
| E-session | `tests/test_proposer_protocol.py`, `tests/test_session.py` | L1 | scripted multi-candidate gate; proposal cannot promote | AI proposer quality | RQ1, Fig 3 | scripted |
| E-adv | `tests/test_audit_adversarial.py`, `tests/test_audit_bz_ibp.py` | L1 | threat-model attacks | "forgery impossible" | RQ2 | implemented threat model only |
| E-guo-flagship | `archive/guo-full-paper-audit-flagship-v1` `d92f3ec`; product `examples/flagship/guo/RESULTS.md` | L1 | 189/189; 146 relations; 32/21/11/17/47/18; false promo 0/155 | "189 proved"; held-out generalisation | RQ3, Fig 4, App A | trust RESULTS.md summary |
| E-guo-selected | `archive/guo-selected-edge-validation-v1` `69ad474` | L1 | precursor selected-edge table | flagship UX | App A2 lineage | not the public headline |
| E-breadth | `archive/prd-cross-paper-stress-v1` `4f12401` RESULTS.md | L1 | 5 papers, 41 edges, false promo 0/30 | five complete audits; productized approximation overlays | RQ3 field sample, Table 8 | experiment-tree statuses stay experimental |
| E-cas | Meurer 2017; MacCallum 2018; Peeters 2007 | L3 | "CAS used in physics/Python" | internals beyond abstract | Intro, RW | metadata-only |
| E-pcc | Necula POPL 1997 | L3 | producer/checker exists | PCC implements derivation graphs | RW | citation-level |
| E-hidden | Gottliebsen et al. JSC 2005 | L3 | hidden CAS verification | method steps | RW | citation-level |
| E-sttt | Kaufmann Biere STTT 2023 | L3 | SAT+CA certificates | Nullstellensatz sizes | RW | citation-level |
| E-prov | Moreau et al. 2008 | L3 | workflow provenance | physics typing | RW | citation-level |
| E-nb | Kluyver 2016; Koop 2021 | L3 | notebooks; incomplete notebook provenance | — | Intro, RW | citation-level |
| E-lean | de Moura 2021; Yang 2023; Song 2024 | L3 | kernels and copilots | HEP formalisation completeness | RW | citation-level |
| E-ai | Polu 2020; Trinh 2024 | L3 | LM proposes, checker checks | physics manuscript audit | RW | citation-level |
| E-fair | Wilkinson 2016 | L3 | FAIR data | derivation typing | RW | citation-level |
| E-pdg | Physics Derivation Graph project pages | L3/project | named adjacent software | no journal article found | RW | no fake bib entry |
| E-guo-paper | Guo et al. PRL 136, 206303 (2026), arXiv:2511.16422v2 | L3 + L1 validation | identity of the field case | physics conclusions | RQ3 | do not verify physics |

L4 (model memory) is not in this map.

Contribution-to-evidence:

| Contribution | Method section | Experiment | Evidence |
|---|---|---|---|
| C1 unified graph | §§2–3 | Fig 1 | E-user-brief, E-sem, E-schema |
| C2 two-axis semantics | §3 | Fig 2, Table status | E-sem, E-schema, E-guo |
| C3 gated forward derivation | §4 | RQ1, Fig 3 | E-modeA-demos, E-modeA-retest, E-session, E-cap |
| C4 parallel audit + Guo | §§5, 7 | RQ2–RQ3, Fig 4 | E-adv, E-guo |
