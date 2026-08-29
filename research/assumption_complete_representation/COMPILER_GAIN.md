# COMPILER_GAIN (not a prompt retune)

The frozen schema asks for proof obligations of the form

```
G0001 - F(lam) = 0
```

Compiler v1.0 parsed those tokens as unknown symbols / undefined
`F(·)` and scored every operational hypothesis `VERIFIER_UNKNOWN`.

That is a software bug in obligation expansion, not a scientific
failure of the proposer.

v1.1 expands:

* catalog IDs `G0001`… to catalog text
* latent-head calls `F(arg)` by substituting the parsed F

Same raw API responses are rescored. No new API request is made to
hide the v1.0 UNKNOWN.

Label: `COMPILER_GAIN` on any run whose V/Q/operational_success
changes under v1.1.

Parser scientific content is still not repaired. Format-only JSON
wrap of a single hypothesis object remains format-only.
