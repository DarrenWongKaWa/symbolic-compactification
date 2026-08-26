# Reviewer B — PL / symbolic algebra (actively rejecting novelty)

Is this just CSE, equality saturation, or library learning?

**Recommendation: Reject novelty of the method.**

- Repeated srepr inventory **is** common-subexpression elimination.
- `F(n,m)+F(m,n)` **is** a two-argument permutation check.
- `(f(x)-f(y))/(x-y)` **is** a local syntactic pattern.
- Identical-value Piecewise collapse **is** a trivial branch fold.
- The residual gate is the authors’ previous engine, already published
  in the repo as fail-closed ZERO/NONZERO/UNKNOWN.

DreamCoder/Stitch/babble invent *new* library functions by anti-unification
over a corpus. This system does not anti-unify `V(p)*G0(p)*V(p)` with
`V(q)*G0(q)*V(q)` (DEV miss). egg would search equivalences; this does not.

The **problem statement** (typed H on scientific expressions, negative
tasks, UNKNOWN ≠ success) is cleaner than most LLM+CAS papers. That is
an evaluation contribution, not a new synthesis algorithm.

I will desk-reject any abstract that says “we discover scientific
abstractions” without showing an invented object that CSE cannot name.
