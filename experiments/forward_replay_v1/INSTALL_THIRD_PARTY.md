# Third-party symbolic proposer actually executed

This campaign requires at least one independently developed public symbolic
tool to be installed and run, not emulated.

## Executed: gplearn 0.4.3

- Paper / docs: Stephens, gplearn (scikit-learn compatible GP)
- Repository: https://github.com/trevorstephens/gplearn
- License: BSD-3-Clause
- Install (experiment venv only):

```bash
python -m pip install 'gplearn==0.4.3' numpy scikit-learn
```

- Recorded versions in this worktree:
  - gplearn 0.4.3
  - numpy 2.5.2
  - scikit-learn 1.9.0
  - sympy 1.14.0 (already required by the frozen product)
- Seed: 0
- Search budget: population_size=200, generations=8, n_samples=80
- Native I/O: numeric design matrix (X, y) sampled from E_t → program string
- Adapter: `proposers/gplearn_sr.py` translates `add/sub/mul/div` when possible
- Honest class: symbolic regression, not derivation transformation

## Attempted, not executed as the third-party engine

### ERRLESS (arXiv:2608.09617 / ICLR 2026 anonymous PDF)

No public implementation was found. Classification:
`PAPER_ONLY_OR_NOT_REPRODUCIBLE`. Not emulated.

### PySR

Preferred SR engine if a Julia binary is present.

```
which julia  → not found
import pysr  → ModuleNotFoundError
```

Classification: `RUNNABLE_BUT_TASK_MISMATCH` and **blocked here** (no Julia).
The Guo masked tasks are derivation rewrites, not (X, y) discovery problems.
We did not install PySR in order to avoid a fake integration.

### AI Feynman

Same native class as gplearn/PySR (data-fit SR). Not installed: gplearn already
satisfies the mandatory "real released implementation" requirement, and the
frozen tasks are not Feynman-style data-fit problems.

## Deterministic CAS family

SymPy 1.14.0, already bundled with the frozen engine environment.
Script: `proposers/cas_sympy.py` (`expand` / `factor` / `together` / `cancel` /
`simplify`).
