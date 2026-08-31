# Release demos

The v0.1 release has exactly three standalone researcher workspaces. Their
committed files are immutable inputs; verification outputs belong only in a
copied workspace's `runs/<run_id>/` directory.

| demo | purpose | required result |
|---|---|---|
| `demo_a_zero` | researcher-supplied exact algebraic factorization | `ZERO` |
| `demo_b_grounded_newton_dd` | one fixed, denominator-safe rational instance of the frozen C9H4/M9H1 Newton divided-difference evidence | `ZERO` |
| `demo_c_unknown` | frozen order-two polygamma recurrence proof gap | `UNKNOWN` |

Demo B is a verification demonstration, not a search or discovery result. It
does not certify the full symbolic C9H4 family: its nodes are the fixed
positive rationals `10/9` and `25/9`, with fixed nonzero difference `5/3`.
Demo C makes the fail-closed contract visible: `UNKNOWN` does not promote the
hypothesis and is neither likely true nor likely false.

## Deterministic Python replay

After installing the package, run:

```bash
python engineering/release_v0_1/demos/run_demos.py
```

The runner copies each workspace to a temporary directory, calls
`load_workspace(...)`, `verify_hypothesis(...)`, and `generate_report(...)`,
checks source-file immutability, then deletes the temporary outputs. Standard
output contains only a deterministic summary: expected/actual verdicts,
per-obligation verdicts, source snapshot hash, and artifact checks.

To retain the generated provenance and reports for inspection, choose a new
output directory:

```bash
python engineering/release_v0_1/demos/run_demos.py \
  --output-root /tmp/ssc-v0.1-demo-replay
```

The runner refuses to overwrite an existing output path.

## CLI replay after integration

The workspaces use the final external workspace contract directly, so the
workspace CLI can replay any copied demo without conversion:

```bash
symbolic-compactification inspect /tmp/ssc-v0.1-demo-replay/demo_a_zero
symbolic-compactification verify /tmp/ssc-v0.1-demo-replay/demo_a_zero
symbolic-compactification report /tmp/ssc-v0.1-demo-replay/demo_a_zero
```

Use the same commands for Demo B and Demo C. The final CLI implementation is
an integration dependency; this demo branch does not modify `cli.py`.

## Interpretation

- `ZERO` certifies only the declared obligations under the documented engine
  semantics and assumptions.
- `NONZERO` would be an exact refutation of at least one obligation.
- `UNKNOWN` is a proof gap and cannot be promoted.
- Notes and reference files provide context and grounding; the verifier does
  not silently turn their prose into assumptions or proof.
- No proposer is used. These are Mode A, researcher-supplied hypotheses.
