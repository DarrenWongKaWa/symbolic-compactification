# thermal-04-coth-matsubara

Rejected: no. Ladder: `R5_special_function`. `is_guo`: false.

## Expression

\[
\coth z = \frac1z + 2z\sum_{n=1}^{\infty}\frac{1}{z^2+n^2\pi^2}
\qquad(z\neq n\pi i,\ n\in\mathbb{Z})
\]

Equivalent compact form of the same poles (algebra on the source, same domain):

\[
\sum_{n=-\infty}^{\infty}\frac{1}{n^2+q^2} = \frac{\pi\coth(\pi q)}{q}.
\]

SymPy residual:

```text
cosh(z)/sinh(z) - (1/z + 2*z*Sum(1/(z**2 + n**2*pi**2), (n, 1, oo)))
```

## Source (DECLARED domain)

NIST DLMF 4.36, <https://dlmf.nist.gov/4.36>, immediately before 4.36.3–4.36.5:

> When \(z\neq n\pi i\), \(n\in\mathbb{Z}\),

then 4.36.3 (coth partial fractions). Sibling 4.36.4 is \(\operatorname{csch}^2 z=\sum(z-n\pi i)^{-2}\) on the same set.

## Latent structure

Bosonic Matsubara frequency sum: simple poles on \(i\mathbb{Z}\) compactify to \(\coth\). Closed special function versus spectral sum. Not CSE.

## Why not CSE / LGG

Infinite rational sum vs one hyperbolic function. CSE cannot perform the Mittag-Leffler summation.

## Proposer leak risk

Do not leak “Matsubara” or the \(\pi\coth(\pi q)/q\) alias as a gold name. Source writes \(\coth\) and the sum.

## Notes

\(\beta>0\) is **not** imported: the source is a complex identity with explicit pole exclusion. `coth` \(\notin\) PARSE_POLICY; use \(\cosh/\sinh\). Numeric: residual \(0\) at \(z=2/5+i/7\).
