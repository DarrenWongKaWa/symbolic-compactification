# Context-Grounded Candidate Pool

This pool was mined under the terminal Context-Grounded Verified
Representation Discovery protocol.  A candidate had to be a real
physics/mathematical-physics object, locally representable, source-grounded,
non-leaking, assumption-complete, bounded, and operationally evaluable with
the current verifier.  A beautiful source without a current evaluator was
rejected rather than converted into evaluator-development work.

| task | family | disposition | decisive reason |
|---|---|---|---|
| `CCR-A-KUBO-FERMI-DD-01` | matrix/DD | FAIL | incomplete diagonal/degenerate-node semantics and full Kubo packaging gap |
| `B-CANONICAL-BASIS-01` | canonical DE basis | FAIL | no evaluator for arbitrary basis transforms |
| `CGVRD-D-2210-2LOOP-IBP-01` | IBP/master basis | FAIL | no current integral-module or arbitrary-basis evaluator |
| `ccvrd-feshbach-rydberg-stirap-01` | Feshbach/Schur | FAIL | genuine two-dimensional retained block needs unsupported matrix semantics |
| `CGVRD-C-SSH4-ENDPOINT-CF-01` | continued fraction | FAIL | scalar equalities exist, but no current structured continued-fraction evaluator |
| `cgvr-f-hubbard-dimer-eom-lehmann-01` | Lehmann | FAIL | operator/eigensystem evaluator absent; source slicing and state assumptions also fail |
| `CG-THERMAL-LI-LEVCHENKO-HERMITE-01` | thermal/polygamma | FAIL | source does not declare the required temperature/scattering domain |
| `CG-THERMAL-AG-HERMITE-01` | thermal/polygamma | FAIL | source domain gap and grammar-authored normalized target |
| `CG-A-SPECTRAL-PROJECTOR-DD-01` | matrix/DD | FAIL | author-instantiated target, unsupported domain/matrix semantics, and historical superfamily |
| `CCR-F-HUBBARD-DIMER-LOCAL-LEHMANN-4P-01` | finite Lehmann | FAIL | no typed pole/residue-map evaluator; distractor leak risk |
| `CCR-B-SCALAR-FESHBACH-PHOTONIC-TRIMER-01` | Feshbach/Schur | PASS, not frozen | rank-one projected resolvent has exact scalar self-energy obligations |

The only surviving task is a source-derived site-1 projected resolvent of the
three-site photonic lattice in [Ma et al., arXiv:1607.05180](https://arxiv.org/abs/1607.05180).
Its rank-one retained subspace is genuine: the eliminated Q block remains
two-dimensional.  The source Hamiltonian yields an exact scalar cofactor
target and the Feshbach reconstruction can be tested by the existing exact
verifier.  It was not frozen, shown to a model, or used as a result.

The complete machine-readable dispositions are in
`CANDIDATE_POOL.json`.  There are 11 candidates from seven searched families,
one provisional admission, and therefore no eligible three-task corpus.
