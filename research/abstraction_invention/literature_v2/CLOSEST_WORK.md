# Literature — beyond first-order LGG

Audit date: 2026-08-27. First-order LGG is **closed** as solved substitution
abstraction, not as a novelty claim.

## Anti-unification family

| Work | What it generalizes | F-classes |
|---|---|---|
| Plotkin 1970; Reynolds 1970 | first-order terms | substitution LGG (our frozen B1) |
| Cerna–Kutsia surveys | HO, equational, nominal, constrained AU | F2–F4 map |
| Higher-order *pattern* AU (Miller patterns; Baumgartner–Kutsia–Levy–Villaret) | λ-terms with restricted free vars | F3-like |
| AU modulo AC / A / C | commutative/associative theories | F2 |
| E-generalization (Burghardt et al.) | congruence induced by E | F2, partial F3 |
| Nominal AU | names/binders | not our physics CAS |

Answers:

1. **Already standard:** F1 ranking (compression); F2 AC/A/C AU and
   canon; F8 library learning; fragments of F3 via HO-AU.
2. **Hard but well-defined:** unrestricted HO-AU, AU modulo arbitrary E,
   F5–F6 representation change, F7 invariant bases.
3. **Require search (not unique LGG):** F3–F8; also AC-AU can be
   *non-unique* (many incomparable generalizations).
4. **LLM niche:** proposing *which* operator family / representation to
   try when the theory is not given; not computing AC-LGG of `x*(y+z)`.
5. **Would be a reimplementation:** shipping AC-LGG or HO-pattern AU and
   calling it a new method.
6. **Physics-specific:** `Sum`/`Piecewise`/indexed kernels, confluence of
   thermal special functions, tensor generators — not in AU datasets.

## Library learning (serious neighbors)

DreamCoder (PLDI 2021), LAPS, Stitch (POPL 2023), babble (POPL 2023):
invent reusable λ-abstractions across a **corpus of programs**. That is
F8. They are not fail-closed residual obligations on one physics
expression. Do not claim “abstraction invention” generically as new.

## Physics CAS

IBP/master integrals *reduce* to a known master basis. They do not invent
the master from an untrusted agent. FORM CSE is F0/F1. Cadabra/xAct
canonicalize tensors (near F2/F6 for index notation).
