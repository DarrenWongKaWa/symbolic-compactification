# thermal-02-bose-im-digamma

Rejected: no. Ladder: `R5_special_function`. `is_guo`: false.

## Expression

\[
\Im\psi(iy) = \frac{1}{2y} + \frac{\pi}{2}\coth(\pi y)
\]

SymPy residual (`coth` not in PARSE_POLICY):

```text
im(polygamma(0, I*y)) - (Rational(1,2)/y + (pi/2)*cosh(pi*y)/sinh(pi*y))
```

## Source (DECLARED domain)

NIST DLMF 5.4.16, <https://dlmf.nist.gov/5.4.E16>:

> \(\Im\psi(i y) = 1/(2y) + (\pi/2)\coth(\pi y)\)
>
> Symbols: \(y\): real variable.

The same chapter defines \(\psi(z)\) only for \(z\neq 0,-1,-2,\ldots\) (DLMF 5.2.2). For real \(y\) the only hit is \(y=0\), which is also the pole of \(1/(2y)\) written in 5.4.16. So \(y\neq 0\) is DECLARED from those two co-located formulas, not from thermal folklore.

## Latent structure

Bosonic thermal kernel = \(\Im\psi\) on the imaginary axis = \(\coth\) plus an elementary \(1/(2y)\). Occupancy commentary:

\[
\frac{1}{e^{x}-1} = \frac12\left(\coth\frac{x}{2}-1\right).
\]

## Why not CSE / LGG

Special-function identification \(\Im\psi\leftrightarrow\coth+1/(2y)\). Not a shared subexpression.

## Proposer leak risk

Do not leak \(n_B\) / “Bose function”. Write \(\cosh/\sinh\) if the engine is used.

## Notes

Numeric check: residual \(0\) at \(y\in\{1/7,2/3,-5/4\}\). No extra pole-exclusion is imported.
