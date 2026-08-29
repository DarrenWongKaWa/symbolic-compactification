# Evaluation strata (Phase III freeze)

Authority: DEV_MANIFEST.json, BASELINES_DEV.json.
Parser is **not** extended in this experiment.

Two strata. They are not interchangeable.

## A. CORE_COMPARABLE (n=6)

Tasks the frozen symbolic stack can ingest (parseable under the
frozen whitelist) and for which an LLM hypothesis can be compiled
and fail-closed adjudicated (ZERO / NONZERO / UNKNOWN).

| case_id | R | domain | frozen baseline quality |
|---|---|---|---|
| mp-resolvent-dd-01 | R2 | mathphys | TYPE_ONLY (B9 name, no operational F) |
| ac-r01-resolvent-hilbert-identity | R2 | green | TYPE_ONLY |
| thermal-01-fermi-im-digamma | R5 | thermal | NO_HYPOTHESIS; B0 residual not simplify-ZERO |
| thermal-03-digamma-reflection | R5 | thermal | NO_HYPOTHESIS |
| thermal-05-trigamma-double-pole | R5 | thermal | NO_HYPOTHESIS |
| sciml-phi-hermite-01 | R3 | sciml | NO_HYPOTHESIS |

These six support **AI vs frozen-symbolic representation** comparison.

B0 residual ZERO is not representation discovery. None of the six
has `operational_baseline=true`.

Special-function identities may still adjudicate UNKNOWN: SymPy
simplify does not close DLMF. UNKNOWN is an adjudication, not a
parser gap.

## B. PACKAGING_GAP (n=8)

`UNPARSEABLE_WHITELIST` under the frozen parser. Legitimate
scientific tasks. They **must not** count as AI_UNIQUE_SUCCESS
because the LLM can read notation the frozen packager cannot.

| case_id | R | domain | gap (illustrative) |
|---|---|---|---|
| mp-daleckii-krein-01 | R3 | mathphys | matrix / Loewner kernel |
| mp-hermite-fA-01 | R3 | mathphys | matrix interpolant |
| mp-cauchy-dunford-01 | R6 | mathphys | contour / matrix |
| sciml-vanloan-blockexp-01 | R6 | sciml | block matrix exp |
| sciml-daleckii-krein-01 | R3 | sciml | matrix / Hadamard |
| ac-t-eps-delta | R8 | tensor | Levi-Civita |
| ac-t-young-s3 | R8 | tensor | Young projectors |
| ac-r03-helmholtz-outgoing-green | R5 | green | spherical Hankel / `exp(I*k*R)/R` packaging |

For these, optional later P0×1 diagnostics report only:

```
LLM_READS_OBJECT
SYMBOLIC_PACKAGING_UNSUPPORTED
```

Never headline representation superiority.

## Fairness

Frozen operational baseline success **0/14** is not “LLM beat 14
symbolic baselines.” Eight of fourteen never entered the comparable
stack.

AI_UNIQUE_SUCCESS is defined only on CORE_COMPARABLE, and only when
the baseline failure is not a packaging/whitelist gap.

Do not fix the eight whitelist failures in this method version.
