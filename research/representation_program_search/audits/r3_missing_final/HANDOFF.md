# Handoff — final fresh-R3 mining pass

## Result

- Verdict: `R3_MISSING`
- Candidate packages created: `0`
- Scientific results: `0`
- Method/verifier runs: `0`

The immutable record is `R3_MISSING.json`; `validate.py` replays its schema,
source hash/locator shape, frozen corpus inventory, key duplicate anchors, and
fail-closed disposition.

## Primary-source evidence

| Screen | Version | Archive SHA-256 | Complete TeX SHA-256 | Outcome |
|---|---|---|---|---|
| MassToMI | `1509.05030v2` | `46e50fdfdeaba67d7c0f6d83755b5fdfaf5ce0541e816e854e03bb46aa5c0d13` | `28b21a27bc43480222964f897a4925a32a2fcf22ccd33d6ae3fabfe78e9df694` | target exposed; generic duplicate; local domain incomplete |
| Rubensson | `2306.15814v1` | `c715d8f193772813dbc492a51c5c878a657b0720345f58e303459e04c010fcf4` | `bae495f1f0f061517f9a577d950f8c8c813e7b98547e570222a87788ebe39082` | generic duplicate; old arity-three pattern |
| FET | `1504.00960v2` | `783b0493ddbff7bf4b60c2fea93e50cbc4a207736ad106f93e77461ec83dea04` | `718206b68100fab7d8d936173d2495651f86168e8d75560650ef93728adc6905` | no concrete source-displayed R3 catalog; generic duplicate |

Exact excerpt line ranges and hashes are in the JSON. Replay a source with:

```bash
curl -LfsS https://export.arxiv.org/e-print/1509.05030v2 -o source.tar
shasum -a 256 source.tar
tar xf source.tar
sed -n '1286,1354p' MassToMI.tex | shasum -a 256
```

Use the corresponding version/member/range for the other two records. The
audit intentionally stores hashes and locators rather than copying broad
copyrighted source blocks into the repository.

## Admission self-assessment

There is nothing to submit for DEV admission. Creating a package from any of
these screens would require at least one prohibited move: reuse an inspected
generic identity, select a source because it announces the grammar operator,
infer a missing domain, or author the concrete R3 catalog ourselves.

