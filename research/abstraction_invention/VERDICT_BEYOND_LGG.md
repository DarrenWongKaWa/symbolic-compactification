# Final Scientific Verdict — Beyond First-Order LGG

## 1. What did first-order LGG solve?

Substitution-level abstraction: related members that differ by consistent
leaf replacement (`V(p)G0(p)V(p)` vs `V(q)G0(q)V(q)`). Frozen B9 is 0/5
invention on that TEST; LGG is 5/5. Closed at `efc0924`.

## 2. What failure classes remained?

F1 shallow holes (Guo `I*mu*theta0`), F2 AC/distributivity, F3–F4 operators,
F5–F8 confluence / representation / bases / libraries.

## 3. Did shallow-abstraction filtering work?

Partly. Gold-free S ranks the Guo polygamma family (12.63, keep) above
`I*mu*theta0` (6.45, keep=false after the depth/named/dl_F rule). High-gain
shallow `beta*gamma*(theta0+theta1)` still has the largest S but is dropped
on depth. Weights were set on DEV Guo, not TEST.

## 4. How much did canonicalization + LGG recover?

T2 distributivity: expand inside function args makes the two members
identical — **CASE A**, not invention. T1 `(p+q)*u` vs `(q+p)*v` are *not*
equal after AC (different coefficients); they need LGG after sorting the
inner Add. Raw LGG still emits *some* template (2/2 cert) of dubious shape.

## 5. Did equational anti-unification solve the problem?

AC-canon + frozen LGG is enough for declared C/A of Add/Mul. That is
standard AU-mod-C, not a contribution. It does not solve F3–F8.

## 6. Was higher-order/operator-aware search needed?

For F3 yes, modestly: relation-graph **permutation** and **derivative**
edges (TEST 2/2) where zip-LGG is wrong (`T(theta,theta)`) or silent on
`d/dz`. Not HO-pattern AU; not a λ-calculus search.

## 7. Did an LLM provide abstractions unavailable to symbolic methods?

**No. BLOCKED.** No usable API. Cannot claim AI abstraction capability.

## 8. What happened on Guo?

Still DEV. Score keeps a parameterized polygamma pair and d/dβ identities
on linear thermal arguments. Junk `I*mu*theta0` filtered. No confluence.
No L4–L7. No closed form.

## 9. Master / confluence / generators?

- Master-as-derivative: **toy polygamma yes**; Guo only linear d/dβ, not Φ_Γ.
- Confluence: **no**
- Generators: **no**

## 10. Discovery-bound failures

F5–F8; Guo Piecewise family; genuine invariant bases. LGG+canon+graph do
not search a new mathematical language.

## 11. Verifier-bound failures

Derivative obligations use `sympy.diff`, not the residual parser’s
`Derivative` (not in whitelist). Limits/confluence identities stay UNKNOWN
if unstated. That is still a backend gap for F5, not the reason T2 failed.

## 12. Strongest baseline now

**Frozen LGG (B1) + expand/AC canon (B3) + operator graph (B5)**, with B9
as the exact-pattern floor. Closest prior: Plotkin; AC-AU; sympy.diff;
DreamCoder only for F8 (untested).

## 13. Survived claims

LGG ≠ CSE on non-identical substitution families. Some “beyond LGG” is
normalization (F2). Operator edges are a real extra bit (F3). Quality
ranking can suppress F1 junk on Guo without gold.

## 14. Falsified / unsupported

LGG as scientific invention in general. Canon as invention. LLM invention.
Guo L3–L7. F5–F8 solved.

## 15. Publication decision

**E.** Conditional P1: LLM vs this stack on F3/F5 with the frozen schema.

## 16. Commits / artifacts

- LGG freeze: `efc0924`, `LGG_CLOSED.md`
- Beyond-LGG: this branch, `benchmark_abstraction/ssc-abstraction-bench-v0.2-beyond-lgg/`
- `research/abstraction_invention/{beyond,literature_v2,final_v02,dev_v02}/`

Frozen B9 and `prototype/antiunify.py` were not edited.

## 17. Next HUMAN_REQUIRED

Provide a real model API, or decide whether to invest in representation-change
search (F5/F6) rather than more AU. Do not run a D6 physicist survey yet.
