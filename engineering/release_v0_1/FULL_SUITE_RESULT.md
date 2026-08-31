# Full-suite integration result

The engineering protocol authorized one full-suite run and one rerun if the
first attempt exposed a setup defect.

## Attempt 1 — environment collection failure

Command:

```bash
python -m pytest -q
```

The attempt stopped during collection because the test environment lacked the
declared optional `observations` dependency (`matchpy`). No test executed and
no production-code failure was observed. The environment was corrected with
the repository's declared `dev`, `observations`, and `egraph` extras; `pip
check` then passed.

## Authorized rerun

Result:

```text
2049 passed, 24 failed in 455.57s
```

The 24 failures are outside the research-preview release path and are retained
without rewriting frozen scientific evidence:

| count | historical test group | cause |
|---:|---|---|
| 1 | RPS final-closure hash audit | the terminal context-campaign registry updates changed `CAPABILITIES.json`, `NEGATIVE_RESULTS.md`, and `REPERTOIRE_V2.md` after the older frozen RPS closure manifest; this drift predates the engineering branch |
| 19 | frozen RPS SOL replay/search authority | the authority deliberately pins the old SHA-256 of `src/symbolic_compactification/models.py`; the engineering-only external package-version change is correctly reported as `SOL_AUTHORITY_SOURCE_DRIFT` |
| 1 | research-only LLM transport test | optional `openai` client is not a declared alpha dependency and was absent from the full-suite environment |
| 3 | frozen matrix-package directory enumeration | historical tests treated a generated `__pycache__/` directory as a package directory; no source package failed |

These failures do not change the release-critical result and are not repaired
inside this program because doing so would mutate or reinterpret closed
scientific infrastructure. The explicit release gate and affected external
workflow suites pass separately.

## Release interpretation

- This is not a fully green historical repository suite.
- It is not evidence of a new scientific defect.
- Alpha readiness depends on the release-critical, clean-install, clean-room,
  demo, security, source-immutability, and review gates defined for this
  engineering program.
- Frozen RPS/SOL artifacts remain unchanged.
