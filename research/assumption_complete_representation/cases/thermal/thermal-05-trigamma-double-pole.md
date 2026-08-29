# thermal-05-trigamma-double-pole

Rejected: no. Ladder: `R5_special_function`. `is_guo`: false.

## Expression

\[
\psi'(z)=\sum_{k=0}^{\infty}\frac{1}{(k+z)^2},
\qquad z\neq 0,-1,-2,\ldots
\]

SymPy residual:

```text
polygamma(1, z) - Sum(1/(k + z)**2, (k, 0, oo))
```

## Source (DECLARED domain)

NIST DLMF 5.15.1, <https://dlmf.nist.gov/5.15.E1>:

> \(\psi'(z)=\sum_{k=0}^{\infty} 1/(k+z)^2\),
>
> \(z\neq 0,-1,-2,\ldots\).

Corroboration, Wikipedia *Polygamma function*: the general series \(\psi^{(m)}(z)=(-1)^{m+1}m!\sum (z+k)^{-(m+1)}\) “holds for integer values of \(m>0\) and any complex \(z\) not equal to a negative integer.” Primary citation remains DLMF 5.15.1.

## Latent structure

Trigamma is the generating function of double poles at nonpositive integers (order-2 bosonic Matsubara kernel). Equivalent Hurwitz form \(\psi'(z)=\zeta(2,z)\). Also the derivative of the digamma series (repeated-node reading).

## Why not CSE / LGG

Named special function vs infinite sum. CSE does not sum it.

## Proposer leak risk

Do not leak “Hurwitz zeta”, “Hermite DD”, or “Matsubara double pole” as gold names.

## Notes

Fully whitelist-writable (`polygamma`, `Sum`). Pole set is on the equation. Numeric residual \(0\) at \(z=3/4+i/2\).
