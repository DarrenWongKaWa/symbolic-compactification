# Derivation-step verification (blinded)

Each step below is a claim inside a derivation, with the author's justification. Judge every step ON ITS OWN, assuming the definitions given (do not assume earlier steps are right). A step is VALID if the claim holds exactly (or, for O(.) or limit claims, as stated) for all admissible parameters; otherwise INVALID. Justifications may be misleading; judge the mathematics.

Answer format: your final message must be ONLY a JSON array:
[{"id": "K1.1", "verdict": "VALID" or "INVALID", "reason": "one sentence", "confidence": 0.0-1.0}, ...] covering all steps in order (the full sheet also had 23 private Part K steps).

## Part G definitions (Guo et al., open-system model with a wide-band fermionic bath)

Same beta, G, mu, f0; e_nm = e_n - e_m (note the order in Part G).
Bath integrals (definitions):
  rho0_n = int dw_b/(2 pi) 2G/(w_b^2 + G^2) f0(e_n + w_b)
  rho1_mn(w) = int dw_b/(2 pi) 2G/(w_b^2 + G^2) [f0(e_n + w_b) - f0(e_m - w_b)]/(w + w_b + e_nm + iG)
  rho2_mln(w1,w2) = int dw_b/(2 pi) 2G/(w_b^2 + G^2) [ f0(e_m - w_b)/((w1+w2+w_b+e_nm+iG)(w1+w_b+e_lm+iG)) + f0(e_n + w_b)/((w1+w2+w_b+e_nm+iG)(w2+w_b+e_nl+iG)) - f0(e_l + w_b)/((w1+w_b+e_lm+iG)(w2-w_b+e_nl+iG)) ]
Residue form of rho2 (claimed in G1.4), with rho1 in its residue form and r_pm^(1)(w, e_m, e_n) as written in G1.3 but with f_+(e_m - w) in r_+:
  rho2_mln(w1,w2) = [rho1_ln(w2) - rho1_ml(w1) + r_+^(2) + r_-^(2)]/(w1 + w2 + e_nm + 2iG),
  r_+^(2) = [r_+^(1)(w2, e_l, e_n) - r_+^(1)(w1, e_m - w2, e_l - w2)]/(w1 + w2 + e_nm),
  r_-^(2) = [r_-^(1)(w2, e_l + w1, e_n + w1) - r_-^(1)(w1, e_m, e_l)]/(w1 + w2 + e_nm).
Taylor coefficients: rho1_mn(w) = sum_k C^(1,k)_mn w^k;  rho2_mln(w,-w) = sum_k C^(2,k)_mln w^k.
z_{n,pm} = 1/2 + beta (G pm i (e_n - mu))/(2 pi);  z0_{n,pm} = 1/2 pm i beta (e_n - mu)/(2 pi).  psi0..psi4 = polygamma of order 0..4.

## Part G steps

### G1.1
Claim: rho0_n = int dw_b/(2 pi) 2G/(w_b^2+G^2) f0(e_n + w_b) = (f_+(e_n) + f_-(e_n))/2, with f_pm(e) = 1/2 pm (i/pi) psi(1/2 pm i beta (e mp iG - mu)/(2 pi))
Justification: residue theorem on the Lorentzian-weighted bath integral

### G1.2
Claim: lim_{G->0} rho0_n = 1/(1 + exp(beta (e_n - mu)))
Justification: the Lorentzian tends to a delta function

### G1.3
Claim: rho1_mn(w) (bath integral Eq. SM_rho1) = [rho0_n - rho0_m + r_+ + r_-]/(w + e_nm + 2iG), r_+ = iG (f_+(e_n) - f_+(e_m + w))/(w + e_nm), r_- = iG (f_-(e_n + w) - f_-(e_m))/(w + e_nm)
Justification: close the w_b contour; residues of the Lorentzian and of f0

### G1.4
Claim: rho2_mln(w1,w2) (bath integral Eq. SM_rho2) equals the residue form of Eq. (tilde-rho_2_supp) with r_pm^(2) built from r_pm^(1) at shifted arguments
Justification: same contour argument applied to the three terms

### G2.1
Claim: C^(1,2)_nn = [w^2] rho1_nn(w) = beta/(96 pi^4 G^2) [6 pi^2 (psi1(z+) + psi1(z-)) - 3 pi beta G (psi2(z+) + psi2(z-)) + (beta G)^2 (psi3(z+) + psi3(z-))], z_pm = 1/2 + beta(G pm i(e_n - mu))/(2 pi)
Justification: Taylor-expand the residue form at coincident labels

### G2.2
Claim: C^(1,2)_nn = (1/G^2) [beta/(16 pi^2) sum_pm psi1(z0_pm)] + [beta^3/(192 pi^4) sum_pm psi3(z0_pm)] + O(G), z0_pm = 1/2 pm i beta (e_n - mu)/(2 pi)
Justification: expand the polygammas around G = 0

### G2.3
Claim: C^(1,2)_nm = i/(8 pi^3 e_nm^3 (2iG - e_nm)^2) [4 pi^2 (2G + i e_nm)^2 (-psi0(z_n+) + psi0(z_m+) + psi0(z_n-) - psi0(z_m-)) + 8 pi beta G e_nm (iG - e_nm)(psi1(z_n+) + psi1(z_m-)) + beta^2 G e_nm^2 (2G + i e_nm)(psi2(z_n+) + psi2(z_m-))]
Justification: Taylor-expand the residue form at distinct labels

### G2.4
Claim: C^(1,2)_nm = -i/(2 pi e_nm^3) [psi0(z0_n-) - psi0(z0_n+) - psi0(z0_m-) + psi0(z0_m+)] + O(G)
Justification: set G = 0 in the closed form

### G2.5
Claim: C^(2,2)_nnn = [w^2] rho2_nnn(w,-w) = i beta^4/(768 pi^5) [psi4(z_n+) - psi4(z_n-)]
Justification: Taylor-expand the second-order kernel at coincident labels
