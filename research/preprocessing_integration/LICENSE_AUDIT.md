# License audit

Permissive (may be normal/optional Python deps):
- SymPy BSD-3
- MatchPy MIT
- egglog-python / egg / egglog MIT

Copyleft, **external process only**:
- Cadabra2 GPL-3+
- FORM GPL (see upstream COPYING)

Not in core:
- Mathematica (proprietary)
- Metatheory.jl deferred (MIT, overlap)

This repository does not vendor GPL sources. Optional backends must not
make `pip install symbolic-compactification` fail.
