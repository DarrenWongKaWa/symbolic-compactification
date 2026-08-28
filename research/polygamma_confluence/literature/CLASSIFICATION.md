# Track V4 method classification

Polygamma derivative `d/dz polygamma(n,z) = polygamma(n+1,z)`, Taylor
expansion, and Laurent coefficients of a removable pole are **known
standard**. They are not novelty.

Per-atom series routing (12 terms of 13–51 ops instead of one 327-op
`sympy.series`) is an **engineering adaptation**: fail-closed
ZERO/NONZERO/UNKNOWN, reconstruction of `pref * Add`, together-ops cap,
no Guo table.

A paper may not claim “we introduce polygamma confluence.” A family-level
`FAMILY_ZERO` on frozen Guo 5-branch is still a **gap** (case J-C).
