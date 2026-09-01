# Figure 4 — Real-paper retrospective audit (Guo)

Skill: `figure-designer`. Experimental-results case figure for RQ3.
Supersedes `fig3-real-paper-graph.md` numbering (that content belongs here).
`fig4-fail-closed-asymptotic.md` can remain as an optional supplement on
Demo C remainder soundness; it is not one of the four load-bearing figures.

Public evidence: `v0.3.0-alpha` `examples/flagship/guo/RESULTS.md`
and `archive/guo-full-paper-audit-flagship-v1`. Printed equation numbers
are the public identifiers. The selected-edge table at `69ad474` is
lineage only.

---

### 1. Figure type

- Type: experimental-results (path illustration + accounting inset)
- Reason: the finding is type preservation on a heterogeneous path, not a
  pass-rate bar.

### 2. Paradigm

- Paradigm: annotated path / small graph
- Rejected: "19/19 passed" stacked bar; heat map of greenness.

### 3. Layout sketch

- Canvas: ~170 mm × 90 mm.
- Main: a short path of printed equations (not all 25):

  1. (D-57) \(\Gamma\) remainder — triangle `UNKNOWN`
  2. (D-59)→(D-60) regroup — circle `DIRECT_EXACT` / `ZERO`
  3. (D-66)→(D-67) with \(\varepsilon_{21}=-\varepsilon_{12}\) — square
     `SUBSTITUTION_EXACT` / `ZERO`
  4. (D-114)→(D-119) BZ IBP — diamond `RULE_CERTIFICATE` /
     `CERTIFIED_BY_RULE`, child Leibniz `ZERO`

- Callouts:
  - IBP parent: "not a SymPy integral ZERO"
  - (D-57): "remainder stays UNKNOWN; coefficient ZERO is not a remainder proof"
- Inset box (accounting, canonical):

```
189 numbered eqs → 25 selected paper steps
18 paper-level ZERO = 12 DIRECT + 6 SUBSTITUTION
2 RULE_CERTIFICATE
1 ASYMPTOTIC UNKNOWN
4 structural
+1 Leibniz helper ZERO → 19 complete-run ZERO
NONZERO = 0
```

- Footer: "Formative field validation. Not held-out generalisation.
  Lineage: v0.2.0 → Guo IBP gap → v0.2.1 adapter."

### 4. Caption

> Figure 4. The same evidence system preserves distinct epistemic states on
> a published theoretical derivation (Guo et al., Phys. Rev. Lett. 136,
> 206303 (2026), arXiv:2511.16422v2). Direct exact algebra, substitution-
> conditioned algebra, a Brillouin-zone integration-by-parts rule
> certificate, and an asymptotic remainder occupy different statuses. The
> two non-green results shown are soundness evidence, not failures to
> maximise a pass count. Accounting: 25 selected paper steps; 18
> paper-level engine ZERO; 19 complete-run ZERO including one shared
> Leibniz helper that is not a paper step.

### 5. Tool

- draw.io → SVG/PDF. Shapes dual-encode class. ColorBrewer Set2.

### 6. Integrity

- No 19/19 score: pass.
- Leibniz not drawn as a 26th paper step: pass (helper is a child, not a node
  in the selected-paper path).
- Formative not held-out: in caption.
