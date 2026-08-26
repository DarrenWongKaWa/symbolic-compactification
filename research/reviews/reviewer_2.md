# Reviewer 2 — hostile PL / symbolic-reasoning / e-graph

Recommendation if submitted **now**: **Strong reject**.

1. **Not equality saturation.** There is no e-graph. B6 is a toy
   rewrite loop explicitly documented as not egg. LGuess (2025) already
   does LLM-guided EqSat with rewrite soundness on polynomials. You did
   not compare to it.

2. **ZERO is not a kernel certificate.** SymPy `simplify` plus rational
   probes is CAS semantics. Calling it "certified" without a Lean/SMT
   subset will be treated as misleading. UNKNOWN timeouts are not a
   logic.

3. **C2 is false on your own numbers.** Dev compactify: B1 Δops 0.82 >
   B7-det 0.35. The "structure-aware" method is a pair of named
   linearity transforms. FullSimplify / `simplify` already merge
   polynomials. FORM already compactifies HEP.

4. **"LLM + verifier" is 2020–2026 mainstream.** GPT-f, DSP, LeanDojo,
   FunSearch, AlphaGeometry, AlphaProof, ToRA, O-Forge, Moxia. The
   hashed JSON session is software, not a theorem.

5. **Benchmark is toy.** 7 compactify test items; doubled sums; Guo
   contaminated. Piecewise vs Abs is UNKNOWN in your own generator.
   That is an engine limitation, not a scientific result.

6. **Missing egg, Mathematica, Lean.** Documented unavailability is not
   a free pass when those are the field's actual baselines.

I would reject even a workshop version until C2 is dropped or reversed
on a non-trivial set and certification language is downgraded to
"exact under SymPy engine semantics".
