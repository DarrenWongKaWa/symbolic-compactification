# Reproducibility — Research Preview v0.1

The authoritative clean-room record is
`engineering/release_v0_1/CLEAN_ROOM_HEAD_REPLAY.md` in the repository
checkout of tag `research-preview-v0.1.0-alpha`.

Product commit under test: `bd6f0a1ecb766526be3eb5cc596eeb337e4b69d0`.

## Exact commands

From a clean clone of that commit, on CPython 3.12:

```bash
python3.12 -m venv env
env/bin/python -m pip install -U pip
env/bin/python -m pip install '.[dev]'
env/bin/python -m pip check
env/bin/symbolic-compactification --version
env/bin/python -m pytest -q -m release_critical
python engineering/release_v0_1/demos/run_demos.py
```

Copy each demo out of the checkout before CLI replay:

```bash
symbolic-compactification inspect COPY
symbolic-compactification verify COPY
symbolic-compactification report COPY
```

Expected demo results: A `ZERO` (exit 0), B `ZERO` (exit 0), C `UNKNOWN`
(exit 3).

## Clean-room outcome (2026-09-01, macOS arm64, CPython 3.12.13)

- ordinary and wheel installs: PASS
- release-critical: 17 passed
- demos: ZERO / ZERO / UNKNOWN
- provenance commit: exact `bd6f0a1…`
- source immutability: PASS
- secret canaries: 0 matches
- report symlink/forged-file attacks: fail closed, no canary

The historical full suite is **not** green (`2049 passed, 24 failed`) and is
not part of the alpha contract. See
`engineering/release_v0_1/FULL_SUITE_RESULT.md`.
