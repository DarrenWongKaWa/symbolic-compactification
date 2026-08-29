# thermal-01-fermi-im-digamma

Rejected: no. Ladder: `R5_special_function`. `is_guo`: false.

## Expression

\[
\Im\psi\!\left(\tfrac12 + iy\right) = \frac{\pi}{2}\tanh(\pi y)
\]

SymPy residual (engine whitelist):

```text
im(polygamma(0, Rational(1,2) + I*y)) - (pi/2)*tanh(pi*y)
```

## Source (DECLARED domain)

NIST DLMF 5.4.17, <https://dlmf.nist.gov/5.4.E17>:

> \(\Im\psi(1/2 + i y) = (\pi/2)\tanh(\pi y)\)
>
> Symbols: \(y\): real variable.

Psi poles are stated in the same chapter, DLMF 5.2.2: \(\psi(z)\) for \(z\neq 0,-1,-2,\ldots\). For real \(y\), \(\tfrac12+iy\) never hits that set (DERIVED).

## Latent structure

The fermionic occupation kernel is the imaginary part of digamma on the vertical line \(\tfrac12+i\mathbb{R}\), equivalently \(\tanh\). Algebraic companion (commentary, not an extra domain):

\[
\frac{1}{e^{x}+1} = \frac12 - \frac12\tanh\frac{x}{2},
\qquad
\frac{1}{e^{x}+1} = \frac12 - \frac1\pi\Im\psi\!\left(\tfrac12 + i\frac{x}{2\pi}\right)
\]

with real \(x=2\pi y\). Master special function, not a CSE of the series for \(\psi\).

## Why not CSE / LGG

Different heads (`polygamma` vs `tanh`). CSE does not identify them. LGG does not introduce the Fermi kernel.

## Proposer leak risk

Keep psi / tanh / Im. Do not expose “Fermi–Dirac occupation” or a target compact name in proposer-visible context.

## Notes

Numeric check: residual \(0\) at \(y\in\{0,1/7,2/3,-5/4\}\). \(y=0\) is allowed.
