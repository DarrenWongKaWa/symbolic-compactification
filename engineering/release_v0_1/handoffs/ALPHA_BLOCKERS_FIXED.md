# Alpha blocker fixes

Scope: the four remaining E11 engineering blockers only. No scientific
semantics, frozen research evidence, verifier route, engine identity, or
agent-protocol identity changed.

## Fixed

1. Release identity is explicitly `0.1.0-alpha`; Python packaging installs the
   PEP 440 canonical version `0.1.0a0`. The deterministic engine and agent
   protocol remain `0.3.0`. The distribution summary now uses the approved
   fail-closed research-preview positioning.
2. Default run provenance records both direct runtime dependencies: `PyYAML`
   and `sympy`. It still does not enumerate the environment.
3. `result.json` persists a bounded, credential-redacted workspace summary and
   fixed artifact inventory. `REPORT.md` now includes project/objective,
   declared symbols/functions, the complete typed hypothesis, grounding
   metadata, every recorded input/expression hash, dependency versions,
   warnings, and generated artifacts. Note/reference contents are excluded.
4. Workspace parse/compile failures now expose a stable code, safe
   workspace-relative source or JSON-pointer-like schema location, and fixed
   actionable hint. Raw exception detail, source expressions, submitted
   unsupported values, and secrets remain absent by default.

The previously integrated `ASSUMPTION_REQUIRED` behavior is preserved.

## Verification

- Focused affected tests:
  `tests/test_packaging_contract.py tests/test_run_provenance.py
  tests/test_research_api.py tests/test_research_cli.py
  tests/test_release_security.py` — **62 passed**.
- Explicit release-critical gate: `pytest -m release_critical` — **12
  passed**.
- `git diff --check` — **PASS**.

The commit SHA is reported in the coordinator handoff.
