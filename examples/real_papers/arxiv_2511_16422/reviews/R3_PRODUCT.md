# R3 — product evaluator

**Verdict: ALPHA_READY**

This run uses the frozen public CLI (`audit inventory|inspect|verify|table|report|package`)
on the public workspace layout. `src/symbolic_compactification/` is unchanged.
Demos A/B/C are untouched. Packaged `reproduce.sh` is the generic exporter
script. Wording does not claim the paper is proved.

Bibliographic `SOURCE.yaml` in the package is a post-export copy (generic
`audit package` does not emit it). Native residuals substitute identities
that `assumptions.yaml` cannot encode. Those are product-boundary notes, not
an engine fork.
