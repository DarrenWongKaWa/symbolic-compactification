# ScientificAssumptionContract

No scientific task enters the benchmark without this object.

```
symbol_assumptions        # name → {real, integer, positive, nonzero, ...}
function_domains          # head → analytic/meromorphic domain
nonzero_conditions        # explicit inequalities
positivity_conditions     # explicit inequalities
real_valued_functions     # function heads that are real on the domain
analytic_domains          # disks / cuts / pole sets the verifier may use
branch_conventions        # logs, roots, arg
limit_domains             # variables and allowed approaches
source_provenance         # citations / URLs / frozen file hashes
derived_conditions        # proved from declared; class B only
```

Labels on every predicate: `DECLARED` | `DERIVED` | `NOT_DECLARED`.

A task whose verifier needs `NOT_DECLARED` analytic-domain hypotheses
is **PROBLEM_UNDERSPECIFIED**, not DISCOVERY_FAILURE.

Physical folklore (T>0, broadening>0, energies real) is NOT_DECLARED
unless the source writes it.
