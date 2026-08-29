# thermal-06-fermi-dirac-polylog

Rejected: no. Ladder: `R1_parameterized_family` (also R5). `is_guo`: false.

## Expression

Fermi–Dirac and Bose–Einstein integrals (DLMF 25.12.14–16):

\[
F_s(x)=\frac{1}{\Gamma(s+1)}\int_0^\infty\frac{t^s}{e^{t-x}+1}\,dt
=-\operatorname{Li}_{s+1}(-e^{x}),
\qquad s>-1,
\]

\[
G_s(x)=\frac{1}{\Gamma(s+1)}\int_0^\infty\frac{t^s}{e^{t-x}-1}\,dt
=\operatorname{Li}_{s+1}(e^{x}),
\]

with Bose domain \(s>-1,\ x<0\) or \(s>0,\ x\le 0\).

Series form writable with `Sum` when \(|e^{x}|<1\) (Bose \(x<0\)):

```text
-Sum((-exp(x))**n / n**(s+1), (n, 1, oo))   # = F_s(x) for x < 0
 Sum( (exp(x))**n / n**(s+1), (n, 1, oo))   # = G_s(x) for x < 0
```

`polylog` and `Integral` are not in PARSE_POLICY; declare `polylog` as a function if ingested.

## Source (DECLARED domain)

- DLMF 25.12.14 <https://dlmf.nist.gov/25.12.E14>: \(s>-1\) under \(F_s\).
- DLMF 25.12.15 <https://dlmf.nist.gov/25.12.E15>: \(s>-1,\ x<0\); or \(s>0,\ x\le 0\) under \(G_s\).
- DLMF 25.12.16 <https://dlmf.nist.gov/25.12.E16>: \(F_s(x)=-\operatorname{Li}_{s+1}(-e^{x})\), \(G_s(x)=\operatorname{Li}_{s+1}(e^{x})\).
- DLMF 25.12.10: \(\operatorname{Li}_s(z)=\sum z^n/n^s\) analytic for \(|z|<1\); \(|z|=1\) if \(\Re s>1\); otherwise analytic continuation.

Wikipedia *Complete Fermi–Dirac integral* matches the \(j>-1\) integral and the polylog identity; also \(F_0(x)=\ln(1+e^{x})\).

## Latent structure

One-parameter family of Fermi/Bose integrals is a single polylogarithm \(\operatorname{Li}_{s+1}(\pm e^{x})\). Derivative family \(dF_s/dx=F_{s-1}\) (Wikipedia) is available as an R1 recurrence.

## Why not CSE / LGG

Integral kernel \(\leftrightarrow\) named polylog family. Parameter \(s\) is a family, not a CSE.

## Proposer leak risk

The source title already says Fermi–Dirac / Bose–Einstein. Do not add a further compact “master \(\Phi\)” name.

## Notes

25.12.16 does not repeat \((s,x)\) on the equation line; domains are those of 25.12.14–15 plus continuation 25.12.10 in the same section. \(x\) is a DLMF real variable. \(T>0\) is not used. Numeric: \(F_1(1/2)\) integral \(+\,\operatorname{Li}_2(-e^{1/2})=0\); \(G_0(-1/3)\) matches \(\operatorname{Li}_1(e^{-1/3})\).
