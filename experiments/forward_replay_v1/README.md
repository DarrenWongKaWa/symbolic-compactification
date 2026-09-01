# Forward proposer replay v1

Experiment branch: `experiment/forward-proposer-replay-v1`
Frozen product: tag `derivation-audit-v0.2.1-alpha` peel `783ec64`
Public Guo evidence (read-only): `69ad474`

This tree is an **experiment**, not a product release. `src/` is untouched.

## Object

```
proposal → verify → promote/refuse → next step
```

The question is not whether an AI discovers the best representation.
It is whether untrusted candidates from heterogeneous proposers can be
gated by the existing typed evidence layer.

## Reproduce

```bash
python -m venv .venv
.venv/bin/pip install -e . 'gplearn==0.4.3' numpy scikit-learn pyyaml
.venv/bin/python experiments/forward_replay_v1/scan_leakage.py
# proposers already frozen under candidates/; re-run only if deliberately regenerating
.venv/bin/python experiments/forward_replay_v1/verify_candidates.py
.venv/bin/python experiments/forward_replay_v1/summarize_metrics.py
.venv/bin/python experiments/forward_replay_v1/experiment_c_rollout.py
```

Do not re-run proposers against verifier outcomes for Experiment A.

## Layout

| Path | Role |
|---|---|
| `TASKS_FROZEN.yaml` | Frozen masked tasks |
| `contexts/` | Permitted proposer context only |
| `hidden/targets/` | Evaluator-only ground truth |
| `candidates/` | Frozen proposer outputs |
| `verification/records.json` | Mode A results |
| `PROPOSER_LANDSCAPE.md` | External tool audit |
| `INSTALL_THIRD_PARTY.md` | gplearn execution record |
| `LEAKAGE_PROTOCOL.md` | Masking rules |
| `PRODUCT_GAPS.md` | Gaps; not a todo list |
| `FINAL_REPORT.md` | Verdict |

## Verdict

See `FINAL_REPORT.md`: `FORWARD_WORKFLOW_DEMONSTRATED_WITH_CAVEATS`.
