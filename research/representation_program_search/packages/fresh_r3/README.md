# Fresh strict-R3 candidate

`rps-case-q7v3` is a candidate-only DEV case. It is not admitted to a shared
benchmark manifest and remains `CANDIDATE_FOR_INDEPENDENT_REVIEW`.

## Scientific identity

The case specializes Theorem 2, equations (8)--(9), of Marcel Schweitzer,
“Integral representations for higher-order Fréchet derivatives of matrix
functions: Quadrature algorithms and new results on the level-2 condition
number,” *Linear Algebra and its Applications* 656 (2023), 247--276,
[DOI 10.1016/j.laa.2022.10.005](https://doi.org/10.1016/j.laa.2022.10.005),
[arXiv:2203.03930v2](https://arxiv.org/abs/2203.03930v2).

The fixed instance uses the third Fréchet derivative of the matrix
exponential at `diag(a,b,c)`. Three rank-one direction paths isolate scalar
components whose evaluator-only coefficient sequences have arity four and
multiplicity partitions `(2,2)` and `(2,1,1)`. This is distinct from the
historical generic arity-three `[x,x,y]` task, from C3J9's second-order
logarithm identity, and from the fixed-zero-node exponential phi family. The
bounded audit and its limitations are recorded in
`source/duplicate_audit.json`.

## Primary-source binding

The exact TeX bytes for equations (8)--(9) are stored at
`source/theorem2-equations.tex` with SHA-256
`76cbf6191983c656681daca3b3c58bf9d62688fb5f4602ba0e42005dff0222a1`.
`source_manifest.json` also binds the arXiv v2 source archive and full TeX
hashes, the journal/TeX locators, the fixed-instance lowering, the exact
symbol namespace, and all assumption locators. The package records only a
short equation block, not the article text.

## Public/evaluator boundary

The public loader reads exactly the proposer view, assumptions, source
catalog, symbol namespace, and three member expressions. The public case and
member/locator identifiers are opaque. Target type, derivative order,
operator names, node roles, repeated-node language, reference programs, and
proof receipts are evaluator-only. Explicit multiplicity occurs only in the
evaluator reference and lowering.

## Exact checks

The full reference program compiles under M1 with no schema delta and is
non-tautological. Three required obligations are session-recorded `ZERO`.
`G_NO_HERMITE` and `G_PRIMITIVE` reconstruct all three members using only
`VALUE`, `DERIVATIVE`, `SUBSTITUTE`, and `LINEAR_COMBINATION`; each variant
also has three session-recorded `ZERO` receipts. Thus a named `HERMITE_DD`
primitive is not required for reference-program expressibility.

Run the fail-closed validator with:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. .venv/bin/python \
  -m research.representation_program_search.packages.fresh_r3.validate
```

## Claim boundary

Primitive compilation proves expressibility, not discovery. The current
frozen action generator may not enumerate this arity-four program. No search
run, search-policy change, grammar change, scientific DEV admission, or
generalization claim is part of this package.
