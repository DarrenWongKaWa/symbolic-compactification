# thermal-03-digamma-reflection

Rejected: no. Ladder: `R6_master_object`. `is_guo`: false.

## Expression

\[
\psi(z)-\psi(1-z) = -\frac{\pi}{\tan(\pi z)} = -\pi\cot(\pi z)
\]

SymPy residual:

```text
polygamma(0, z) - polygamma(0, 1 - z) + pi/tan(pi*z)
```

## Source (DECLARED domain)

NIST DLMF 5.5.4, <https://dlmf.nist.gov/5.5.E4>:

> \(\psi(z)-\psi(1-z)=-\pi/\tan(\pi z)\),
>
> \(z\neq 0,\pm 1,\ldots\).

DLMF notes that Abramowitz–Stegun 6.3.7 omitted the condition on \(z\); DLMF writes it on the equation.

## Latent structure

Master generating identity for Matsubara kernels: reflection operator \(z\mapsto 1-z\) on digamma produces the cotangent thermal kernel. Differentiating in \(z\) yields the polygamma reflection DLMF 5.15.6 (higher-order Matsubara poles). One meromorphic object plus one operator.

## Why not CSE / LGG

Functional equation / reflection, not a common subexpression. The latent operator is not an LGG rewrite.

## Proposer leak risk

Source already names \(\psi\) and \(\tan/\cot\). Do not leak “Matsubara master” or sequels (5.15.6) as gold.

## Notes

Integer exclusion is written on the identity. That is the analytic domain; nothing is borrowed from another scientific problem.
