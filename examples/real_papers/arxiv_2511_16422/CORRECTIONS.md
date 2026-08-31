# Transcription / encoding corrections

No post-freeze residual retuning for ZERO is recorded.

## C-1 — catalog printed numbers (metadata only)

`equations/CATALOG.yaml` initially used a TeX-counter simulation that reset at
`\appendix`, so appendix “printed” labels were off by the eight main-text
equations (local D-1 labelled D-49 instead of public HTML/PDF **D-57**).

Correction: rebuild the catalog from arXiv HTML printed tags. Frozen edges
and `TABLE_VERIFIED` already cited HTML numbers (`eq.D-57`, …) and were not
retuned. Curated `equations.yaml` `local_id` fields were aligned to the same
map (local D-1 = printed D-57).

This is a provenance-metadata fix, not a residual change. Re-run
`ssc audit verify` because the equation-manifest hash is in the snapshot.
