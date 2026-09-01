# Getting started

Install from a clone:

```bash
python -m pip install -e ".[dev]"
symbolic-compactification --version
```

You should see package `0.3.0-alpha`, engine `0.3.0`, protocol `0.3.0`.
Engine `0.3.0` is the same exact-adjudication kernel shipped with the
0.2.1 preview. This release does not change `ZERO` / `NONZERO` / `UNKNOWN`.

Core verification does not read an API key.

Then run one of:

- [Forward derivation](forward-derivation.md): `examples/forward/exact-step`
- [Paper audit](paper-audit.md): `examples/audit/minimal`
- Flagship: `examples/flagship/guo/RESULTS.md`
- Flagship HTML (presentation only): `examples/flagship/guo/human_audit/index.html`

`verify` never overwrites your input files. Generated records go under
`runs/` inside the workspace you copied.
