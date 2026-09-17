# Getting started

Install from a clone:

```bash
python -m pip install -e ".[dev]"
symbolic-compactification --version
```

You should see package `0.3.2-alpha`, engine `0.3.0`, protocol `0.3.0`.
Engine `0.3.0` is the same exact-adjudication kernel as `v0.3.0-alpha`.
This packaging release does not change `ZERO` / `NONZERO` / `UNKNOWN`.

Core verification does not read an API key.

Then run one of:

- [Forward derivation](forward-derivation.md): `examples/forward/exact-step`
- [Paper audit](paper-audit.md): `examples/audit/minimal`

Historical paper audits under `examples/` are an optional case library.
They are not default knowledge for a new task.

`verify` never overwrites your input files. Generated records go under
`runs/` inside the workspace you copied.
