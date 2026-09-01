# Historical benchmark corpus

The v0.1 research-preview tree shipped a symbolic-compactification
benchmark under `benchmark/`, plus later `benchmark_v0.2/`,
`benchmark_structure/`, and `benchmark_abstraction/`. Those corpora
supported method-search experiments. They are not part of the v0.3
product surface.

Recover them from git history and from tag `research-preview-v0.1.0-alpha`
(and later commits on `main` before v0.3). Do not treat missing directories
on current `main` as a claim that the benchmarks never existed.
