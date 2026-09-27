"""Plant two sign errors in the downloaded source and in the cards' quotes.

Used by fetch_and_run.sh with MUTATE=1 to show that the review catches
them: the digamma relation becomes NONZERO and the short-time form fails
after the bracket erratum.
"""
import sys
from pathlib import Path

root = Path(sys.argv[1])
swaps = [(r"[\Psi(a)-\Psi(b)]", r"[\Psi(b)-\Psi(a)]"),
         (r"{1-i\Delta\delta t \over", r"{1+i\Delta\delta t \over")]
for path in [root / "manuscript" / "source.tex", *sorted((root / "cards").glob("*.yaml"))]:
    text = path.read_text()
    for old, new in swaps:
        text = text.replace(old, new, 1)
    path.write_text(text)
