# Frozen-output obligation compilation

No new LLM calls. `research/llm_abstraction/runs/` was not mutated.

n=276 frozen proposals → Obligation IR → verify.

## Layer counts

| layer | n | meaning |
|---|---:|---|
| OK | 116 | gold type compiled and all discharged ZERO |
| D | 118 | discovery: missing or wrong type (includes T1 SOL anchoring) |
| V | 36 | compiled, leftover NONZERO/UNKNOWN |
| C | 6 | type present, compile failed |

## T7 (symmetry)

16 runs: **12 OK**, 2 V, 1 D, 1 C.

Confirms the closed line: the proposer already had the invariant;
L4 can now state \(T(i,j)\leftrightarrow T(j,i)\). Residual V/C/D
are seed noise, not “model cannot see a swap.”

## T1 (substitution) A0 vs A2

A0: 5/5 **OK**. A2: 4/5 **D**, 1/5 OK.

SOL miss is **D**, not C: the model emitted `repeated_kernel` (CSE
packet bias). Those kernels often *do* compile and ZERO. Wrong
abstraction class, successful execution.

## Guo G1–G4 (12 runs)

| cond | seed | G1 | G2 | G3 | G4 | layer |
|---|---:|---|---|---|---|---|
| A0 | 0 | Y | Y | Y | N | V |
| A0 | 1 | Y | Y | Y | N | V |
| A0 | 2 | N | N | N | N | D |
| A1 | 0 | Y (DD+confluent) | Y | Y | N | V |
| A1 | 1 | Y (DD) | Y | Y | N | V |
| A1 | 2 | Y (DD+master) | Y | Y | N | V |
| A2 | 0 | Y (DD+confluent) | Y | Y | N | V |
| A2 | 1 | Y | Y | Y | N | V (3 shallow ZERO) |
| A2 | 2 | Y | Y | N | N | C |
| A3 | 0 | N | N | Y | N | D |
| A3 | 1 | Y | Y | Y | N | V |
| A3 | 2 | N | N | Y | N | D (2 packet ZERO) |

G1 is often true: the frozen text **does** name divided-difference /
confluent / derivative families, not merely “maybe unified.”

G4 is never true: members are nicknames (`S1_True`) or DD/limit
obligations are not bound to source subexpressions. That is **C then V**,
not “discovery never happened.”

Shallow ZERO on A2s1 / A3s2 is parameterized polygamma/affine kernels
already visible to L1. It is not G4 success.

## Language gain vs discovery gain

This compiler did **not** invent new hypothesis types. It only typed
obligations on frozen raw output.

T7 OK is execution of an old discovery.
Guo G1=Y, G4=N is a verifier-language / binding problem.
T1 A2 D is a real discovery (anchoring) problem.

Next Track A work may only claim discovery gain if a **new** `H_repr`
type appears that these frozen files do not already contain.
