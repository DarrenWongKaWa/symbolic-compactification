# AUDIT_REVIEWER — locked output types

Constructor uses model A (or a human).
Reviewer uses model B **or a new session**.
The verifier never reads reviewer prose. It reads submitted obligations.

This skill does not adjudicate mathematics. It does not emit `ZERO`.

---

## Allowed findings (closed set)

| Type | Means | Must cite |
|---|---|---|
| `MISSING_EDGE` | A source-supported derivation step is not in the submitted ledger | paper location (eq. numbers / section) |
| `TRANSCRIPTION_DIFF` | Printed form and encoding differ | left printed, left encoding, or right analog |
| `ASSUMPTION_UNGROUNDED` | Condition \(A\) is used but `who_certifies(A)` is missing or `AUDITOR` without disclosure | the edge and the subst/rule |
| `RULE_PRECONDITION_UNCHECKED` | A `CERTIFIED_BY_RULE` parent is missing a checked local identity or an explicit domain | parent id + rule id |
| `STATUS_OVERCLAIM` | Human or HTML copy treats inventory as verification, rule as `ZERO`, remainder as false, or `NONZERO=0` as “paper has no errors” | quoted overclaim |
| `EXPLAIN_RESIDUAL` | Explain a **already recorded** residual / factor; do not change the verdict | residual TeX from the record |

## Forbidden outputs

- `ZERO`
- `NONZERO` as a new verdict (the engine already has one)
- `promote`
- `looks correct`
- a paper score, grade, or “the derivation holds”
- merging `UNKNOWN` into a remainder certificate
- talking `UNSUPPORTED` or `UNKNOWN_REMAINDER` into a pass

Each finding is `HYPOTHESIS`. A human accepts or rejects it before any
re-encoding. Accepted findings may create new submitted obligations.
They do not write RESULTS statuses.

---

## JSON shape

```json
{
  "role": "AUDIT_REVIEWER",
  "authority": "finding",
  "not_a_verdict": true,
  "findings": [
    {
      "type": "MISSING_EDGE",
      "target": "Eq. (D-64) -> Eq. (D-65)",
      "evidence": "…",
      "suggested_encoding": null
    }
  ]
}
```

If nothing in the closed set applies, return `"findings": []`.
Do not invent a compliment.
