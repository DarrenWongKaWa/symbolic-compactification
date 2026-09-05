# METHOD

Paper-agnostic derivation audit.

1. **Source.** TeX preferred. arXiv e-print via `scripts/fetch_arxiv.py`.
2. **Inventory.** Numbered outer `equation`/`align`/`gather`/`multline` rows
   only. Nested environments do not receive numbers. Coverage is
   listed/listed, never “verified”.
3. **Claims.** Identify the paper-level scientific claims (not every lemma).
   Each claim: statement, supporting equations, assumptions, status,
   unresolved obligations.
4. **Edges.** Source-grounded transformations only. Record `from_eq`,
   `to_eq`, transformation type, assumptions, status, locator.
   If a section contains several distinct moves (a symmetry identity,
   an antisymmetrization, a named rewrite, a substitution), record each
   as its own edge. Do not collapse a multi-step load-bearing derivation
   into one edge because the algebra lives in one appendix.
5. **Certification.** `EXACT` only for compiled `A − B = 0`. Cited rules
   stay `CITED_RULE`. Remainders stay `ASYMPTOTIC_UNCERTIFIED`. Numerics
   stay `NUMERICAL_SUPPORT`.
6. **Reviewer queue.** Only genuinely unresolved load-bearing decisions.
7. **Render.** `scripts/render.py` from `audit.json`. Do not hand-edit HTML
   statuses.

Forward derivation (optional, if the engine CLI is installed): candidate
must verify `ZERO` before promotion. That path is not required to emit a
paper-audit ledger.
