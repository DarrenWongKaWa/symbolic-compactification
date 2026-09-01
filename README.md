# symbolic-compactification

Verified symbolic reasoning for theoretical physics.

Two workflows, one deterministic kernel:

- **Forward derivation.** You (or an optional helper) propose the next
  expression. The engine checks whether the candidate is exactly equal to
  the current one under the declared assumptions. Promote only on `ZERO`.
- **Paper audit.** Inventory every numbered equation, record only
  source-supported derivation relations, run the same engine, and emit a
  human-readable `RESULTS.md`.

AI may propose. It may not certify itself. This is not a CAS and not a
theorem prover. Core verification needs no model service and no API key.
`ZERO` means exact engine `ZERO`. `UNKNOWN` never promotes. A rule
certificate is not engine `ZERO`. Promote only on `ZERO`.

Package `0.3.0-alpha`. Engine `0.3.0` (same exact-adjudication semantics as
the 0.2.1 preview). Research Preview, not a stable v1.0.

## Quickstart

```bash
python -m pip install -e ".[dev]"
symbolic-compactification --version
```

### Forward

```bash
cp -R examples/forward/exact-step /tmp/ssc-exact
symbolic-compactification verify /tmp/ssc-exact
# result: ZERO  -> promote this candidate

cp -R examples/forward/refused-step /tmp/ssc-refused
symbolic-compactification verify /tmp/ssc-refused
# result: NONZERO  -> do not promote
```

### Audit

```bash
cp -R examples/audit/minimal /tmp/ssc-audit
symbolic-compactification audit verify /tmp/ssc-audit
symbolic-compactification audit table /tmp/ssc-audit
```

The table lists `ZERO` coefficient identities and leaves the enclosing
`O(g)` remainder `UNKNOWN`.

## Flagship demo

Guo et al., Phys. Rev. Lett. 136, 206303 (arXiv:2511.16422v2): complete
numbered-equation inventory and a source-grounded derivation audit.

See [examples/flagship/guo/RESULTS.md](examples/flagship/guo/RESULTS.md).
Replay: [examples/flagship/guo/REPRODUCE.md](examples/flagship/guo/REPRODUCE.md).

## Docs

- [Getting started](docs/getting-started.md)
- [Forward derivation](docs/forward-derivation.md)
- [Paper audit](docs/paper-audit.md)
- [Semantics](docs/semantics.md)
- [Limitations](docs/limitations.md)
- [Architecture](docs/architecture.md)
- [Research evidence](docs/research-evidence.md)

## Limitations

The engine certifies exact local residuals, not papers, novelty, or
physics. Integrals, remainders, and undeclared identities stay `UNKNOWN`
or structural. See [docs/limitations.md](docs/limitations.md).

## Citation and license

MIT License. Historical campaigns are summarized in
[docs/research-evidence.md](docs/research-evidence.md) and kept in
archive tags, not as the current product surface.
