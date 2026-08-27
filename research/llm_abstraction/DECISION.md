# Decision

Protocol: `deepseek-abstraction-protocol-v1-dev` (prompts/model frozen).
Constructor: `expr_xreplace_v2` (verifier-side; not a prompt retune).

## Case

**CASE A overall** — RAW ≈ SOL on success (0.54 vs 0.52) after constructor
repair. Certified is slightly higher with SOL (0.83 vs 0.90) because
packets make *some* substitution maps easier to emit in a parseable form,
not because SOL invents new objects.

Local qualifications that must not be flattened:

1. **CASE D on T1.** SOL CSE packets pull `parameterized_family` →
   `repeated_kernel` (success 1.00 → 0.20). Anchoring is real.
2. **CASE C locally on T5 (and T2).** Confluence-toy success 0.20 → 0.80.
   Distributivity 0 → 0.60. Small DEV toys only.
3. **CASE E was real, then partly fixed.** T7 permutation and polygamma
   `d/dθ` were untestable because the constructor string-replaced `i`
   into English. After parsed xreplace, T7 is 1.00 on **both** arms.
   Guo DD/master obligations remain UNKNOWN (CASE E residual).
4. **CASE F on T6 / F6.** Neither arm invents a new certified head.

Flash A0 vs A2 reproduces anchoring (success 0.54 → 0.38).

## Answers

1. Does SOL help DeepSeek? **Not in aggregate success.**
2. Levels: helps F5-style specialize typing (T5) and T2; hurts T1 type;
   T7 is a constructor problem, not an observation problem; F6 null.
3. Anchoring? **Yes (T1, Flash A2, Guo A3 local packets).**
4. Certified vs verbal? Constructor v2 converts some verbal maps into
   ZERO. Guo DD/confluence stay verbal.
5. Guo: 2/12 shallow certified kernels; 0 certified masters/DDs.
6. Strongest failure: F6 new-head (T6 0/10 useful) + T1 SOL anchoring +
   negatives that still mint hole-product templates.
7. Next bottleneck: **representation-change search**, and a Guo-scale
   obligation language for DD/confluence (not more SOL backends).
8. Claim: wrapping SOL packets around DeepSeek-v4-pro does not materially
   raise certified abstraction invention on this DEV set and can anchor
   substitution families to CSE. Not: AI discovers physics.
9. Artifacts: `research/llm_abstraction/`; commit of this freeze follows.

Do **not** open held-out TEST to retune prompts.
