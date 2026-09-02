# Reproducibility (every reported machine result)

Every machine result in the paper must be traceable to a public artifact.

## Product

| Item | Value |
|---|---|
| Repository | https://github.com/DarrenWongKaWa/symbolic-compactification |
| Immutable product tag | `derivation-audit-v0.2.1-alpha` |
| Product SHA | `783ec64c0bb4ffd0b4b6ad33f33ead96dba49087` |
| Historical tag (do not move) | `derivation-audit-v0.2.0-alpha` → `aaf1199` |
| Package | `0.2.1-alpha` (PEP 440 `0.2.1a0`) |
| Engine | `0.3.0` (`python_sympy_exact_v1`) |
| Protocol | `0.2.1` |
| GitHub pre-release | https://github.com/DarrenWongKaWa/symbolic-compactification/releases/tag/derivation-audit-v0.2.1-alpha |

Install:

```bash
git clone --branch derivation-audit-v0.2.1-alpha \
  https://github.com/DarrenWongKaWa/symbolic-compactification.git
cd symbolic-compactification
python3.12 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/symbolic-compactification --version
```

Public demos: `engineering/derivation_audit_v0_2/demos/{A,B,C}/`.

Adversarial tests: `tests/test_audit_adversarial.py`,
`tests/test_audit_schema.py`, `tests/test_audit_tables.py`,
`tests/test_audit_bz_ibp.py`.

Versioned semantics: `docs/STATUS_SEMANTICS.md`, `docs/EDGE_TYPES.md`,
`docs/RULE_CERTIFICATES.md`, `docs/THREAT_MODEL.md`.

## Public real-paper evidence

| Item | Value |
|---|---|
| Branch | `engineering/real-paper-validation-arxiv-2511-16422` |
| SHA | `69ad474a43ebea55cb2e524934d982e518db026b` |
| Workspace | `examples/real_papers/arxiv_2511_16422/` |
| Paper | Guo et al., PRL 136, 206303 (2026), arXiv:2511.16422v2 |

```bash
git clone --branch engineering/real-paper-validation-arxiv-2511-16422 \
  https://github.com/DarrenWongKaWa/symbolic-compactification.git
# install product tag 0.2.1-alpha (or the evidence-branch tree)
cd examples/real_papers/arxiv_2511_16422
./reproduce.sh
```

Authoritative generated tables live under `reports/` and in
`reviewer-verification-package/`. Markdown cannot create `ZERO`.
