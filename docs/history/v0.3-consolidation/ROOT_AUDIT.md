# Root audit — v0.3 consolidation

Written before any delete or move. Base: `origin/main` `af022ca`.
Flagship precondition: `FULL_PAPER_AUDIT_DEMONSTRATED` on
`experiment/guo-full-paper-audit-flagship-v1` `d92f3ec`.

Pre-clean remote branch count: 10.

## Root items

| current path | classification | destination | keep / move / delete | reason | historical authority |
|---|---|---|---|---|---|
| README.md | USER_DOC | README.md | keep (rewrite) | Product front door | current main |
| AGENTS.md | PRODUCT_CORE | AGENTS.md | keep (rewrite) | Canonical agent/skill contract | current main |
| Makefile | PRODUCT_CORE | Makefile | keep (rewrite) | Install + test + demo replay | current main |
| pyproject.toml | PRODUCT_CORE | pyproject.toml | keep (version 0.3.0-alpha) | Package identity | current main |
| setup.py | PRODUCT_CORE | setup.py | keep if still required by packaging tests | Legacy packaging helper | current main |
| src/ | PRODUCT_CORE | src/ | keep | Engine; semantics unchanged | derivation-audit-v0.2.1-alpha / 783ec64 |
| tests/ | TEST_REQUIRED | tests/ | keep product tests; delete research-only | Product regression | current main |
| docs/ | USER_DOC | docs/ | move/rewrite into named v0.3 docs | User docs | current main |
| examples/ | FLAGSHIP_DEMO | examples/forward, examples/audit, tests/fixtures | move | Teach product, not history | current main |
| .github/ | PRODUCT_CORE | .github/ | keep (CI rewrite) | Release CI | current main |
| .gitignore | PRODUCT_CORE | .gitignore | keep | Hygiene | current main |
| .grok/ | PRODUCT_CORE | .grok/skills/symbolic-compactification/SKILL.md | keep (rewrite one skill) | User-facing skill | current main |
| scripts/check_clean_room.py | PRODUCT_CORE | scripts/check_clean_room.py | keep | Firewall | current main |
| LICENSE | USER_DOC | LICENSE | add | Missing on main; required at root | none (to add) |
| CAPABILITIES.json | RESEARCH_HISTORY | docs/history/ | move summary only; delete root copy | Superseded capability registry | research-preview-v0.1.0-alpha |
| CAPABILITY_BOUNDARY.md | RESEARCH_HISTORY | docs/history/capability-boundary.md | move shortened | Boundary text still useful | v0.1/v0.2 tags |
| FINAL_DERIVATION_AUDIT_RELEASE.md | RELEASE_HISTORY | delete from main | delete | Preserved by tag derivation-audit-v0.2.1-alpha | 783ec64 |
| FINAL_ENGINEERING_RELEASE.md | RELEASE_HISTORY | delete from main | delete | Preserved by tags | v0.1/v0.2 |
| NEGATIVE_RESULTS.md | RESEARCH_HISTORY | docs/history/negative-results.md | move | Do not reopen frozen negatives | v0.1 |
| REPERTOIRE_V2.md | RESEARCH_HISTORY | delete from main | delete | Recoverable from git/tags | v0.1 |
| REPRODUCIBILITY.md | USER_DOC | fold into docs/getting-started.md | delete root | Replaced by product docs | v0.1 |
| REPRODUCIBILITY_STRUCTURE_DISCOVERY.md | RESEARCH_HISTORY | delete from main | delete | Structure-discovery campaign | v0.1 |
| SCIENTIFIC_EXPERIMENTS_CLOSED.md | RESEARCH_HISTORY | docs/history/scientific-experiments-closed.md | move | Still true; not root | current main |
| benchmark/ | BENCHMARK_HISTORY | delete from main | delete | Not v0.3 product; git/tags keep it | research-preview-v0.1.0-alpha |
| benchmark_abstraction/ | BENCHMARK_HISTORY | delete from main | delete | Abstraction-invention corpus | v0.1 |
| benchmark_structure/ | BENCHMARK_HISTORY | delete from main | delete | Structure-discovery corpus | v0.1 |
| benchmark_v0.2/ | BENCHMARK_HISTORY | delete from main | delete | Historical v0.2 bench | v0.1 |
| research/ | RESEARCH_HISTORY | delete from main | delete | Experiment trees; evidence via archive tags | v0.1 program |
| engineering/ | RELEASE_HISTORY | examples/* distilled; rest delete | delete after copying demos | v0.1/v0.2 demo + release notes live in tags | derivation-audit-v0.2.1-alpha |
| release/ | RELEASE_HISTORY | delete from main | delete | v0.1 release packet in tag research-preview-v0.1.0-alpha | v0.1 |
| reviews/ | RELEASE_HISTORY | delete from main | delete | Internal reviews | v0.1 |
| roles/ | PRODUCT_CORE | keep STRUCTURAL_PROPOSER.md if skill needs it; else docs/history | move needed role into skill refs | Proposer role | v0.1 |
| third_party/ | USER_DOC | docs/history/third-party.md or keep ATTRIBUTION | keep ATTRIBUTION.md at docs/ or third_party if small | Attribution | current main |
| workspace/ | GENERATED | delete tracked skeleton or keep empty? | delete from product root | Runtime; .gitignore covers runs | v0.1 |
| cases/ | OBSOLETE | delete if present | delete | Empty/local | local only |
| manuscripts/ | ACTIVE_PAPER | not on origin/main | n/a | Paper lives on paper/derivation-audit-method | paper branch |
| consolidation/ | PRODUCT_CORE | consolidation/ | keep | This audit + later reports | this campaign |

## tests/

Product / semantic regression (keep):

- test_release_critical.py, test_derivation_audit_release_critical.py
- test_audit_*.py (update demo paths)
- test_verifier.py, test_parser.py, test_workspace.py, test_residual.py
- test_research_api.py, test_research_cli.py, test_session.py
- test_provenance.py, test_run_provenance.py, test_reporting.py, test_reporting_delta.py
- test_packaging_contract.py, test_namespace_rules.py, test_process_lifecycle.py
- test_release_demos.py, test_release_security.py (update paths)
- test_conjecture.py, test_proposer_protocol.py, test_skill_proposer_contract.py
- test_requested_proposer_mode.py, test_wolfram_adapter.py
- test_transforms.py, test_structure.py, test_observations_layer.py
- test_budgets.py, test_fidelity.py, test_ordering.py
- test_smoke_generic.py, test_smoke_long_expression.py
- test_examples_medium.py, test_examples_long_sigma_abc.py (fixtures → tests/fixtures)
- test_v022_* if they still encode current engine contracts
- conftest.py

Historical research-only (delete from main; recoverable from tags):

- test_rps_*, test_ac_*, test_cl_*, test_ic_*, test_mb_*, test_sv_*, test_rc_*
- test_representation_*, test_structure_discovery.py, test_abstraction_invention.py
- test_beyond_lgg.py, test_llm_abstraction.py, test_grounded_proposer.py
- test_method_v2_expand.py, test_obligation_ir.py, test_pg_*, test_saa_*
- test_research_evaluator.py, test_consolidation_contracts.py if v0.2.2-only

## examples/ (current main)

| path | action |
|---|---|
| examples/basic | distill to tests/fixtures or drop; identities covered by forward demos |
| examples/medium | tests/fixtures/medium |
| examples/long | tests/fixtures/long (Guo σ_abc ingest lock) |

New:

| path | source |
|---|---|
| examples/forward/exact-step | engineering/release_v0_1/demos/demo_a_zero |
| examples/forward/refused-step | demo_a with mutated candidate |
| examples/audit/minimal | engineering/derivation_audit_v0_2/demos/C plus one STRUCTURAL definition |
| examples/flagship/guo | experiment/guo-full-paper-audit-flagship-v1 (minimum manifests) |

## Archive tags to create (before branch deletion)

| tag | original branch | HEAD |
|---|---|---|
| archive/derivation-audit-v0.2 | engineering/derivation-audit-v0.2 | aaf1199eb6d8c471589948e1dcdaeeffe2945025 |
| archive/derivation-audit-v0.2.1 | engineering/derivation-audit-v0.2.1 | 3c8c68936c8c1b03c83c1ef31b38f5c7c4e51a76 |
| archive/guo-selected-edge-validation-v1 | engineering/real-paper-validation-arxiv-2511-16422 | 69ad474a43ebea55cb2e524934d982e518db026b |
| archive/forward-proposer-replay-v1 | experiment/forward-proposer-replay-v1 | b9b69727c696a741a797e3bf4b1b9e782149e175 |
| archive/approximation-authority-v1 | experiment/approximation-authority-v1 | 5477cf2447207aba2b218224be419d43f456fe9a |
| archive/prd-cross-paper-stress-v1 | experiment/prd-theory-derivation-audit-v1 | 4f124019d0dc337f4a34391c157f55f71fa1688f |
| archive/guo-full-paper-audit-flagship-v1 | experiment/guo-full-paper-audit-flagship-v1 | d92f3ec693d35bc52658bc7500eb881a2e7434e8 |

Do not move: derivation-audit-v0.2.0-alpha, derivation-audit-v0.2.1-alpha, research-preview-v0.1.0-alpha.

Keep branch: paper/derivation-audit-method (ed9af5a) — unique manuscript work.

## Versioning

| identity | v0.2.1 | v0.3.0-alpha |
|---|---|---|
| RELEASE_VERSION | 0.2.1-alpha | 0.3.0-alpha |
| PACKAGE_VERSION | 0.2.1a0 | 0.3.0a0 |
| ENGINE_VERSION | 0.3.0 | 0.3.0 (unchanged semantics) |
| AGENT_PROTOCOL_VERSION | 0.3.0 | 0.3.0 (unchanged) |
