# thermal-07-green-spectral-hilbert

Rejected: no. Ladder: `R6_master_object`. `is_guo`: false.

## Expression

Hilbert / Lehmann master (Wikipedia many-body Green, spectral + Hilbert-transform sections):

\[
G(\mathbf{k},z)=\int_{-\infty}^{\infty}\frac{dx}{2\pi}\frac{\rho(\mathbf{k},x)}{-z+x},
\]

\[
\mathcal{G}(\mathbf{k},\omega_n)=G(\mathbf{k},i\omega_n),
\qquad
G^{\mathrm{R}}(\mathbf{k},\omega)=G(\mathbf{k},\omega+i\eta)\ \ (\eta\to 0^+).
\]

Retarded spectral integral as written:

\[
G^{\mathrm{R}}(\mathbf{k},\omega)=\int_{-\infty}^{\infty}\frac{d\omega'}{2\pi}\frac{\rho(\mathbf{k},\omega')}{-(\omega+i\eta)+\omega'}.
\]

Imaginary-time two-point function is defined only for arguments in \([0,\beta]\), with \(0<\tau<\beta\) for (anti)periodicity \(\mathcal{G}(\tau-\beta)=\zeta\mathcal{G}(\tau)\).

## Source (DECLARED domain)

Wikipedia *Green's function (many-body theory)* <https://en.wikipedia.org/wiki/Green%27s_function_(many-body_theory)>:

- “The imaginary-time variables \(\tau_j\) are restricted to the range from 0 to the inverse temperature \(\beta=1/k_{\mathrm{B}}T\).”
- (Anti)periodicity “for \(0<\tau<\beta\)”.
- Retarded formula: “the limit as \(\eta\to 0^+\) is implied.”
- “\(G^{\mathrm{R}}(\omega)\) and \(G^{\mathrm{A}}(\omega)\) have simple analyticity properties: the former (latter) has all its poles and discontinuities in the lower (upper) half-plane.”
- Hilbert transform \(G(\mathbf{k},z)\) and the evaluations \(G(i\omega_n)\), \(G(\omega+i\eta)\).
- Sokhotski–Weierstrass \(\lim_{\eta\to 0^+} 1/(x\pm i\eta)=P(1/x)\mp i\pi\delta(x)\).

\(\beta>0\) is not written as an inequality. It is DERIVED as the length of the declared interval \([0,\beta]\) with Fourier factor \(1/\beta\). Physical folklore \(T>0\) is not inserted as a free inequality.

## Latent structure

One Cauchy kernel interpolates Matsubara, retarded, and advanced propagators. Spectral density is the jump. Three presentations, one master \(G(z)\).

## Why not CSE / LGG

Different denominators \(-i\omega_n+\omega'\) vs \(-(\omega+i\eta)+\omega'\) look unrelated to CSE. Unification is a half-plane evaluation of one Hilbert transform.

## Proposer leak risk

Hide “master analytic object” / “unify \(G_R\) and \(G_M\)”. `Integral` is not in PARSE_POLICY; this is a representation identity.

## Notes

No extra exclusion of spectral poles of \(\rho\) is declared; none is imported. \(\zeta=+1\) bosons, \(-1\) fermions is in the source.
