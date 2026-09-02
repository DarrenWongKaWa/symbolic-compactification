## Table S-Verification

| Claim | Location | Type | Machine status | Assumptions | Artifact |
|---|---|---|---|---|---|
| TRS+BZ reduces 9 local structures to 3 channels | E1→E6 | `symmetry` | **SPLIT** → C01, S610, C04 | TRS sewing gauge, full BZ pairing of k with -k | E001 |
| weak-dissipation projection of the 3 channels onto BCD + O(Γ) | Eq. (1) second arrow / S-VI | `limit` | **UNKNOWN** | Γ→0+ with carriers held fixed, remainder O(Γ) | E002 |
| pair carrier P is the b↔c symmetrized covariant velocity product | P_raw→E3 | `definition` | **DEFINITION** | none | E003 |
| loop carrier L is the b↔c symmetrized vvv product | L_raw→E3 | `definition` | **DEFINITION** | none | E004 |
| conductivity factorizes as M*P + T*L (Eq. 4) | E3→E4 | `definition` | **RECORDED** | DC extraction of App. A, no TRS yet | E005 |
| resolve P,L by coincidence/orientation into G9 | E4→E5 | `definition` | **DEFINITION** | none | E006 |
| T=+1 and full-BZ pairing retain only even generators | E5→E6 | `symmetry` | **SPLIT** → C01, S610, C04 | T^2=+1, full BZ pairing | E007 |
| write the three-channel TRS conductivity (7)=(C6) | E6→E7 | `definition` | **RECORDED** | TRS+BZ | E008 |
| two-band loop equals gap^2 times diagonal-velocity * Berry curvature (8) | Eq. (8) | `algebra` | **SPLIT** → C12, C13 (all certified) | velocity matrix elements commute as c-numbers at fixed bands, metric/curvature factorization (B2) | E009 |
| σ_TRS(Γ) = Babc/Γ + O(Γ) | Eq. (9) / S7.21 | `limit` | **UNKNOWN** | kernel Laurent expansion, remainder O(Γ) | E010 |
| a=b=c=α and Ω^αα=0 remove L2,Im from the longitudinal component | E7→E10 | `algebra` | **SPLIT** → B04 (all certified) | Ω^{aa}=0 identically | E011 |
| mirror lattice: ∂_kx ∂_ky H_AB = 0 so P_Im^{xyy}=0 | E11→H_mixed | `algebra` | **ZERO** | H(k) as in (11) | E012 |
| first-order bath density response | A1→A2 | `definition` | **DEFINITION** | constant-broadening bath, Γ>0 | A01 |
| M and T are defined as the [ω^2] DC Taylor coefficients of ρ̃ | A3→A4 / S2.7 | `definition` | **DEFINITION** | Γ>0 fixed, [ω^2] ≡ (1/2)∂_ω^2 at ω=0 | A02 |
| contact and quadratic-drive sectors have [ω^2]=0 because they are ω-independent | A3→A5 | `algebra` | **ZERO** | those sectors contain no ω | A03 |
| Mc is Mb with b↔c; Tcb is Tbc with b↔c | A5→A6 | `index_swap` | **ZERO** | none | A04 |
| f_- is the reflection of the same master f_+ | A7a→A7b | `definition` | **DEFINITION** | Γ>0 so Re z_± > 0 | A05 |
| H1[f;ϵ1,ϵ2]=(f(ϵ2)-f(ϵ1))/(ϵ2-ϵ1) for a quadratic, away from coincidence | A8→H1_distinct | `algebra` | **ZERO** | f analytic, ϵ2≠ϵ1 | A06 |
| regular value of that difference at coincidence is f'(ϵ)=2ϵ | A8→H1_coincident | `algebra` | **ZERO** | H1 is the analytic continuation of the quotient | A07 |
| Peierls vertex equals covariant derivative of velocity | S4.3 completeness | `completeness_insertion` | **RECORDED** | isolated-band charts, Da X = ∂a X - i[Aa,X] | A08 |
| assemble covariant carriers into compact factorization (A16) | A15→A16 | `definition` | **RECORDED** | none | A09 |
| (A16) is Eq. (4) after (bc) notation | A16→E4 | `definition` | **RECORDED** | none | A10 |
| P = PRe + i PIm recovers P from even/odd parts | P_nm→B1_PRe | `algebra` | **ZERO** | none | B01 |
| L = L3,Re + i L3,Im recovers L | L_nml→B1_L3 | `algebra` | **ZERO** | none | B02 |
| velocity bilinear factorizes as ϵ^2 (g - i/2 Ω) | Eq. (B2) / S5.9 | `algebra` | **ZERO** | n≠m, ϵ_nm ≠ 0 | B03 |
| Berry curvature is antisymmetric so Ω^aa=0 | Eq. (B3) Ω^{aa} | `algebra` | **ZERO** | none | B04 |
| quantum metric is symmetric | B3→g_sym | `algebra` | **ZERO** | none | B05 |
| diagonal pair splits into Hessian CH plus metric remainder | B4→B5 | `definition` | **RECORDED** | resolution of identity in the band basis | B06 |
| metric remainder equals -2/ϵ L2,Re after (B2) and symmetric sum | Eq. (B6) pairwise | `algebra` | **ZERO** | curvature drops from the a↔c symmetric combination, fixed pair n≠m; no BZ sum | B07 |
| insert CG into the nine-generator conductivity | B7→B8 | `definition` | **RECORDED** | none | B08 |
| local TRS signs T=diag(-1,-1,+1,-1,+1,-1,-1,+1,-1) | C1→C3 | `symmetry` | **ZERO** | T H(k) T^{-1}=H(-k), local sewing gauge | C01 |
| odd generator projector (1+s)/2 vanishes at s=-1 | C3→C4 | `algebra` | **ZERO** | none | C02 |
| even generator projector (1+s)/2 is 1 at s=+1 | C3→C4b | `algebra` | **ZERO** | none | C03 |
| full-BZ integral of odd integrands vanishes after k↔-k pairing | S6.8 | `integration` | **NOT_LOWERED** | integral over the whole BZ, thermal kernels even in k | C04 |
| write the three surviving channels | C5→C6 | `definition` | **RECORDED** | TRS+BZ | C05 |
| M_Γ = M0 + Γ M1 + O(Γ^2) | C6→C9 | `asymptotic` | **UNKNOWN** | carriers held fixed, remainder O(Γ^2) | C06 |
| antisymmetrized T at coinciding arguments supplies the Γ^{-1} pole | C6→C11 | `limit` | **UNKNOWN** | ϵ_nm≠0, fn' defined by (C8) as Γ→0 | C07 |
| M0(n,m)=M0(m,n) kills the orientation-odd Γ^0 pair residue | C13→C14 | `index_swap` | **ZERO** | M0 symmetry as a kernel property | C08 |
| L3,Im(m,n,ℓ)=-L3,Im(n,m,ℓ) converts the sum into an n↔m difference | C16→C16b | `index_swap` | **ZERO** | dummy relabeling of a complete n≠m≠ℓ sum | C09 |
| T0(m,n,ℓ)=T0(n,m,ℓ) on n≠m≠ℓ, so the Γ^0 triangle residue cancels | C17→C18 / S7.16 | `index_swap` | **ZERO** | fixed-gap residue formulas (S7.10)–(S7.11), all-distinct energies | C10 |
| remaining iΓ/2iΓ in T_Γ makes the L3,Im channel O(Γ) | C18→C19 | `asymptotic` | **UNKNOWN** | C17, ϵ_mn≠0 | C11 |
| L2,Im=(L_nmn-L_mnn)/(2i) equals the commuting-symbol curvature bilinear | Eq. (8) child / S7.19 | `algebra` | **ZERO** | matrix elements commute as c-numbers | C12 |
| that bilinear is (ϵ^2/2)(v^b Ω^{ac}+v^c Ω^{ab}) | Eq. (8) child / S7.19 | `algebra` | **ZERO** | Ω definition (B3) | C13 |
| ϵ^2 in (C20) cancels the 1/ϵ^2 in (C11) at the level of the prefactor algebra | S7.20 prefactor | `algebra` | **ZERO** | C11 Laurent coefficient, ϵ_nm≠0 | C14 |
| σ_TRS = B/Γ + O(Γ) | C22→E9 | `limit` | **UNKNOWN** | remainder O(Γ) | C15 |
| longitudinal exact finite-Γ formula is O(Γ) after the kernel analysis | C23→C23_O | `asymptotic` | **UNKNOWN** | C14 pair O(Γ), C19 triangle O(Γ), Ω^{aa}=0 | C16 |
| on xxx, P = 2 v^x (Dx v^x) | E3→D1P | `algebra` | **ZERO** | b=c=x | D01 |
| on xxx, L = 2 v^x v^x v^x | E3→D1L | `algebra` | **ZERO** | b=c=x | D02 |
| Im[v_ab (Dx v)_sp] = ϵ_ab(ϵ_ca-ϵ_bc)Λ after v=iϵA | Eq. (D7) / S9.8 | `algebra` | **ZERO** | v_ij = i ϵ_ij A_ij, spectator covariant derivative (D5), Λ = Re(A_ab A_bc A_ca) | D03 |
| Im[v_ba v_ac v_cb] = -ϵ_ab ϵ_ac ϵ_bc Λ | Eq. (D8) / S9.9 | `algebra` | **ZERO** | v_ij = i ϵ_ij A_ij | D04 |
| assemble pair-extracted vvv and triangle into K_abc | D7→D9 | `definition` | **RECORDED** | none | D05 |
| S3 orbit of completed-K residue: sum_π K0_π = 0 (Γ^0 part of sum_π (K_π+D_π); D is O(Γ) in (S9.6)) | S9.12 / S9.19 Γ^0 | `index_swap` | **ZERO** | fixed-gap M0,T0 from (S7.10)–(S7.11), Λ invariant under S3, single ordered triple need not satisfy K=-D | D06 |
| pair dictionary plus loop orbit give σ_xxx = -2 σ_xxx^Anan | D4→D16 | `algebra` | **ZERO** | TRS+BZ, Ω^{xx}=0, D4 and D15 | D07 |
| [ω^2] of (N0+N1 ω+N2 ω^2)/(D0+ω) equals N2/D0 - N1/D0^2 + N0/D0^3 | S3.15 | `algebra` | **ZERO** | truncated O(ω^3) series of 1/(D0+ω) | S315 |
| simplex ∫∫ (1-s-t)^2 ds dt over {s,t≥0,s+t≤1} equals 1/12 | S3.22 | `algebra` | **ZERO** | H2 Taylor coefficient identity (S3.23) | S322 |
| nested H1 of H1 for f=x^2 equals the second divided difference 1 | S3.25 | `algebra` | **ZERO** | distinct nodes | S325 |
| even projector Π+=(I+T)/2 is diag(0,0,1,0,1,0,0,1,0) | S6.10 | `algebra` | **ZERO** | T the local TRS sign matrix (S6.4) | S610 |
| P_nm(-k)=-P_nm(k)* implies PIm is TRS-even | S6.5 | `symmetry` | **ZERO** | P_mn=P_nm^*, local TRS sewing | S65 |
| explicit M0(ϵ1,ϵ2)=(F(ϵ2)-F(ϵ1))/(2(ϵ2-ϵ1)^3) is symmetric | S7.10 | `algebra` | **ZERO** | fixed-gap Γ→0 residue formula (S7.10), ϵ1≠ϵ2 | S706 |
| completed all-distinct Γ^0 coefficient T0+(M0(n,ℓ)-M0(ℓ,m))/ϵ_mn vanishes | S7.12 | `algebra` | **ZERO** | T0 defined by (S7.11), ϵ_mn≠0 | S712 |
| T0(m,n,ℓ)=T0(n,m,ℓ) from (S7.10)–(S7.11) and M0 symmetry | S7.16 | `index_swap` | **ZERO** | fixed-gap residues (S7.10)–(S7.11), ϵ_n≠ϵ_m | S716 |
| Anan's 1/2+β xa/(2πi) equals z_-(ϵ) | S9.15 | `algebra` | **ZERO** | xa=ϵ-μ+iΓ | S93 |
| f_+^A(xa)=f_-(ϵ)/2 as coefficients of the same ψ(z_-) | S9.16 | `algebra` | **ZERO** | (S9.3) argument map, dxa/dϵ=1 | S94 |

## Policy

- Typed statuses: ZERO, NONZERO, DEFINITION, RECORDED, SPLIT, NOT_LOWERED, UNKNOWN, ASSUMPTION_REQUIRED.
- Eq. (8) is SPLIT onto C12 and C13 (both ZERO).
- D14 Γ^0 orbit of completed K is an executable residual; finite-Γ orbit of full Anan D is not claimed as that residual.
- `σ(Γ)=B/Γ+O(Γ)` remainder stays **UNKNOWN**.
- Completeness `∑|r⟩⟨r|=I` is a declared reconstruction rule, not a hidden assumption repair.
- Physics was not edited to chase a green board.

Engine: `symbolic-compactification 0.1.0-alpha`.
