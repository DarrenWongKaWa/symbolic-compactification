# Product honesty lock

Verdict: **PRODUCT_HONESTY_LOCKED**

Date (UTC): 2026-09-02  
Software authority: `v0.3.0-alpha` @ `f1d225e` (unchanged)  
Scientific counts: `PAPER_AUTHORITY_LOCK.md`, `CLAIM_EVIDENCE_MATRIX.md`  
This lock does **not** move the tag, retune residuals, or change ZERO semantics.

v0.3 delivers an **obligation certificate** for submitted encodings.
It does not deliver a transcription certificate, a relation-completeness
certificate, or a paper-correctness certificate.

```text
v1 targets obligation soundness;
audit validity remains partly human-mediated.
```

---

## What v1 may be sold as

- An author checking appendix algebra they already encoded
- A collaborator rechecking a submitted derivation ledger
- A journal / group-meeting **local obligation ledger**

## What v1 must not be sold as

- Upload a PDF, automatically prove the paper
- “The AI reviewer thinks this derivation holds”
- `NONZERO = 0` as a promotional score
- “189 equations verified”
- “five papers fully verified”

---

## Frozen copy (product surface)

The three first-screen denominators, and only these, are equal:

| Count | Label | Means |
|---|---|---|
| 189/189 | inventoried equations | every numbered equation was listed |
| 146 | extracted relations | source-grounded derivation edges |
| 53 | executable obligations | compiled for the exact engine |

Coverage 100% may appear only as small type on the **inventory** cell.
It is inventory coverage, not certification coverage.

Write, and do not paraphrase away:

> `NONZERO=0` means none of the submitted executable relations ended
> `NONZERO`. It does not mean the paper has no incorrect steps.

Direct `NONZERO` before a recorded substitution is part of
`ZERO_UNDER_SUBSTITUTION`. It is not, by itself, a paper error.

---

## Residual card (atomic unit)

The product unit is not a table row. For every executable edge the
surface must be able to show, in this order:

1. Left / right encodings (paper numbers + compiled forms)
2. Factorisation of \(R_{\mathrm{direct}}\)
3. Why the direct residual is nonzero (which recorded relation is missing)
4. Condition \(A\) and `who_certifies(A)`
5. \(R_{\mathrm{cond}}\)
6. Machine status

Flagship teaching card: **Eq. (D-117) → Eq. (5)**.
Do not bury it as one row of an empty “Flagship transitions” table.

`who_certifies(A) ∈ {SOURCE, UPSTREAM, DOMAIN, AUDITOR}`.
`AUDITOR` / `AUDITOR_ASSERTED` may exist, but must use warning colour —
never the same visual language as `EXACT_ZERO`.

Presentation must not invent a second paraphrase family
(\(f_n'\) vs \(f_n^{(4)}\)). Use machine fields (`condition.tex`,
`residual_tex`, frozen encodings).

---

## Assumption provenance (presentation overlay)

Current frozen input may still store `subst: {"f4": "2*f04"}` as a
string. The product must ask: who certified \(A\)?

Engine IR change (graph-valued assumptions) is **next product work**,
not a v0.3.0-alpha verifier change. Until then, the HTML maps the
already-recorded condition kind:

| Frozen kind | `who_certifies` |
|---|---|
| source-grounded substitution | `SOURCE` |
| author-declared remainder | `SOURCE` (author-declared ≠ machine-certified) |
| declared rule / domain | `DOMAIN` |
| none | none |
| auditor-only assertion | `AUDITOR` (warning colour) |

Do not silently upgrade `AUDITOR` to `SOURCE`.

---

## Self-certifying report (target)

```text
evidence bundle (JSON records + hashes)
  → RESULTS.md generated from bundle
  → HTML generated from bundle
  → page banner: presentation is not certificate
  → local `verify bundle` (no API)
```

v0.3 flagship `RESULTS.md` on the tag remains scientific authority and
is **not** regenerated in this campaign. The human-facing HTML is a
projection of that frozen table. A scientist who cannot check a hash
is looking at a poster.

---

## Offline / no-JS floor

- Data inlined in the HTML (sibling `report-data.js` is optional)
- If JS fails: three denominators + stacked bar + full ledger table
  + flagship residual card remain
- Empty Derivation map / Edge evidence boxes are forbidden
- Map may be absent; the ledger may not

---

## LLM role (optional, off-line-able)

Constructor (model A) proposes encodings / edges.
`AUDIT_REVIEWER` (model B or a new session) may emit only:

- `MISSING_EDGE`
- `TRANSCRIPTION_DIFF`
- `ASSUMPTION_UNGROUNDED`
- `RULE_PRECONDITION_UNCHECKED`
- `STATUS_OVERCLAIM`
- `EXPLAIN_RESIDUAL` (explains; does not re-judge)

Forbidden reviewer outputs: `ZERO`, `promote`, `looks correct`,
paper scores, “the derivation holds”.

A human decides which findings enter the next encoding round.
The verifier sees only submitted obligations.
Proposer/reviewer output is always `HYPOTHESIS` or a finding, never
a verdict.

Do not productize an LLM that “talks away” the 18 `UNSUPPORTED` and
17 remainder-summary rows.

---

## Verifier line (do not relax)

- `UNKNOWN` never promotes
- Rule certificates must not display as `ZERO`
- Finite Laurent coefficients do not certify a remainder
- Core verify: no API key
- Do not retune frozen residuals
- Do not move `v0.3.0-alpha`

---

## Acceptance before any public “product” claim

1. Same bundle, another machine: RESULTS hash unchanged (tag authority)
2. Deliberately omit a stated substitution → reviewer may mark
   `MISSING_EDGE` / `ASSUMPTION_UNGROUNDED` (skill; not auto-promote)
3. Deliberate PDF/encoding mismatch → `TRANSCRIPTION_DIFF`
4. Injected bad residual still 0 false promotions (already frozen: 0/155)
5. HTML without JS still shows the ledger + flagship card
6. Public copy contains no “full derivation verified”

---

## Full chain (honest)

```text
transcription certificate
  → relation-completeness certificate
  → assumption provenance
  → obligation certificate
  → tamper-evident report
```

v0.3 has the obligation certificate. Product work should punch holes
in the first three rings and **show those holes**, not hide them.

---

## Next allowed product work (not this paper draft)

1. Residual cards + first-screen ledger (this presentation campaign)
2. Optional `AUDIT_REVIEWER` skill, off by default
3. Assumption-provenance IR (later; not a tag move)
4. Bundle-generated RESULTS/HTML (later; not a tag move)

Do not start draft-v4 from this lock. Draft-v4, when asked, must obey
the copy rules above.
