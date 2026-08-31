# Public derivation-audit demos (synthetic)

These three workspaces are **independent textbook constructions**. They
are not extracted from, renamed from, or structurally cloned from any
unpublished source.

Expected statuses are the demo contract. They do not bypass the verifier:
LLM text cannot create `ZERO`.

| demo | mathematics | expected statuses |
|---|---|---|
| `demos/A/` | Freshman algebra: `(x+1)**2` vs `x**2+2*x+1`, and `2*(x+1)` vs `2*x+2` | two `ALGEBRAIC_EQUIVALENCE` edges → `ZERO` |
| `demos/B/` | Two-index polynomial `K(m,n)=m+n`, the $2\times 2$ projector `[[0,0],[0,1]]`, and a local pair `A(m,n)+A(n,m)=2S` | `INDEX_RELABELING`, `PROJECTOR_IDENTITY`, `PAIRWISE_REDUCTION` → `ZERO`; `DEFINITION_INSERTION` → `DEFINITION`; `BOOKKEEPING` → `RECORDED` |
| `demos/C/` | Toy Laurent polynomial `F(g)=a/g+b*g` (`g` nonzero) | two `LAURENT_COEFFICIENT` edges → `ZERO`; `ASYMPTOTIC_CLAIM` `F(g)=a/g+O(g)` → `UNKNOWN` (no remainder certificate) |

Finite coefficient identities are not remainder proofs. Demo C does
**not** encode the asymptotic claim as `F(g)-a/g=0`.

Each demo is a complete audit workspace (`audit.yaml`,
`manuscript/source.tex`, `equations/equations.yaml`, `edges/edges.yaml`,
`expressions/*.txt`, `assumptions/assumptions.yaml`). Per-edge expected
statuses are declared in `demo.yaml` and as comments in `edges.yaml`.

```bash
symbolic-compactification audit inspect \
    engineering/derivation_audit_v0_2/demos/A
```

Committed files are inputs. Do not commit `runs/` outputs.
