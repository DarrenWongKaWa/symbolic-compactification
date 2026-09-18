# Full derivation audit: Guo et al., PRL 136, 206303

Source: arXiv:2511.16422v2

All numbered equations in the public paper and appendices were inventoried. Only source-supported derivation relations are tested as equalities. ZERO means exact machine ZERO.

## Coverage

| Item | Count |
|---|---:|
| Numbered equations in source | 189 |
| Inventoried | 189 |
| Coverage | 100% |
| Derivation relations extracted | 146 |
| Executable relations | 53 |
| Structural / no equality claim (relation rows) | 47 |
| Standalone numbered equations (no equality claim) | 0 |
| Unsupported | 18 |

## Equation audit

| Eq. relation | Mathematical content | Claimed move | Direct check | Condition / authority | Conditional check | Final status |
|---|---|---|---|---|---|---|
| Eq. (1) | $\Gamma$ expansion of $\sigma_{abc}$ | asymptotic expansion | UNKNOWN | author-declared $O(\Gamma)$ remainder | UNKNOWN | UNKNOWN_REMAINDER |
| Eq. (D-57) -> Eq. (1) | main-text $\Gamma$ expansion | bookkeeping | UNKNOWN | author-declared $O(\Gamma)$ remainder | UNKNOWN | UNKNOWN_REMAINDER |
| Eq. (D-69) -> Eq. (2) | $\sigma^{(-2)}$ with $f_n'=2f_{0,n}'$ | substitution | NONZERO | substitute $f_n'=2f_{0,n}'$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eq. (D-78) -> Eq. (3) | $\sigma^{(-1)}$ with $f_n'=2f_{0,n}'$ | substitution | NONZERO | substitute $f_n'=2f_{0,n}'$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eq. (4) | $\sigma^{(0)}=\sigma^{\mathrm{kin}}+\sigma^{\mathrm{geo}}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (D-117) -> Eq. (5) | $\sigma^{\mathrm{kin}}$ with $f_n^{(4)}=2f_{0,n}^{(4)}$ | substitution | NONZERO | substitute $f_n^{(4)}=2f_{0,n}^{(4)}$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eq. (D-127) -> Eq. (6) | $\sigma^{\mathrm{geo}}$ compact form | bookkeeping | N/A | none | N/A | STRUCTURAL |
| Eq. (7) -> Eq. (8) | block-diagonal $S=\tau_z\sigma_z$ form | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (A-9) | total Hamiltonian $H(t)$ as system+bath block matrix | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (A-10) | $\rho_S=\rho^{(0)}+\rho^{(1)}+\rho^{(2)}+O(V^3)$ | asymptotic expansion | UNKNOWN | author-declared $O(V^3)$ remainder | UNKNOWN | UNKNOWN_REMAINDER |
| Eq. (A-11) -> Eq. (A-14) | bath integral $\to$ polygamma $f_\pm$ | special function identity | N/A | none | N/A | UNSUPPORTED |
| Eq. (A-12) -> Eq. (A-16) | $\tilde\rho^{(1)}$ residue form | special function identity | N/A | none | N/A | UNSUPPORTED |
| Eq. (A-13) -> Eq. (A-18) | $\tilde\rho^{(2)}$ residue form | special function identity | N/A | none | N/A | UNSUPPORTED |
| Eq. (A-14) -> Eq. (A-15) | $\Gamma\to 0$ recovers $f_0$ | limit | N/A | none | N/A | UNKNOWN |
| Eq. (A-17) -> Eq. (A-16) | $r_\pm^{(1)}$ inserted in $\tilde\rho^{(1)}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (A-17) -> Eq. (A-19) | $r_+^{(2)}$ as divided difference of $r_+^{(1)}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (A-17) -> Eq. (A-20) | $r_-^{(2)}$ as divided difference of $r_-^{(1)}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eqs. (A-19), (A-20) -> Eq. (A-18) | $r_\pm^{(2)}$ inserted in $\tilde\rho^{(2)}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (B-21) | $V=V^{(1)}+V^{(2)}+O(A^3)$ | asymptotic expansion | UNKNOWN | author-declared $O(A^3)$ remainder | UNKNOWN | UNKNOWN_REMAINDER |
| Eq. (B-22) | $J_a=J_a^{(0)}+J_a^{(1)}+J_a^{(2)}+O(A^3)$ | asymptotic expansion | UNKNOWN | author-declared $O(A^3)$ remainder | UNKNOWN | UNKNOWN_REMAINDER |
| Eq. (B-23) -> Eq. (B-24) | $j_a^{(2)}$ split into (I)-(IV) | bookkeeping | N/A | none | N/A | STRUCTURAL |
| Eq. (B-24) -> Eq. (B-25) | four channels $\to$ $\sigma_{abc}(\omega_1,\omega_2)$ | bookkeeping | N/A | none | N/A | STRUCTURAL |
| Eq. (B-25) -> Eq. (B-26) | DC limit $\omega_1\to 0$, $\omega_2\to-\omega_1$ | limit | N/A | none | N/A | UNKNOWN |
| Eq. (C-27) | Taylor kernels $\mathcal{C}^{(1,k)}$, $\mathcal{C}^{(2,k)}$ | definition | N/A | none | N/A | UNSUPPORTED |
| Eq. (C-28) | polygamma arguments $z_{n,\pm}$ and $z_{n,\pm}^0$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (C-29) -> Eq. (C-30) | intraband $\mathcal{C}_{nn}^{(1,2)}$ in $\Gamma$ | asymptotic expansion | UNKNOWN | author-declared $O(\Gamma)$ remainder | UNKNOWN | UNKNOWN_REMAINDER |
| Eq. (C-31) -> Eq. (C-32) | interband $\mathcal{C}_{nm}^{(1,2)}$ in $\Gamma$ | asymptotic expansion | UNKNOWN | author-declared $O(\Gamma)$ remainder | UNKNOWN | UNKNOWN_REMAINDER |
| Eq. (C-33) -> Eq. (C-34) | $\mathcal{C}_{nnn}^{(2,2)}$ in $\Gamma$ | asymptotic expansion | UNKNOWN | author-declared $O(\Gamma)$ remainder | UNKNOWN | UNKNOWN_REMAINDER |
| Eq. (C-35) -> Eq. (C-39) | mixed $\mathcal{C}_{nmn}^{(2,2)}$ in $\Gamma$ | asymptotic expansion | UNKNOWN | author-declared $O(\Gamma)$ remainder | UNKNOWN | UNKNOWN_REMAINDER |
| Eq. (C-40) -> Eq. (C-45) | $\mathcal{C}_{nnm}^{(2,2)}$ Laurent in $\Gamma$ | asymptotic expansion | UNKNOWN | author-declared $O(\Gamma)$ remainder | UNKNOWN | UNKNOWN_REMAINDER |
| Eq. (C-46) -> Eq. (C-51) | $\mathcal{C}_{nmm}^{(2,2)}$ Laurent in $\Gamma$ | asymptotic expansion | UNKNOWN | author-declared $O(\Gamma)$ remainder | UNKNOWN | UNKNOWN_REMAINDER |
| Eq. (C-52) -> Eq. (C-56) | fully interband $\mathcal{C}_{nml}^{(2,2)}$ in $\Gamma$ | asymptotic expansion | UNKNOWN | author-declared $O(\Gamma)$ remainder | UNKNOWN | UNKNOWN_REMAINDER |
| Eqs. (C-36), (C-37), (C-38) -> Eq. (C-35) | $\mathcal{C}_{nmn}^{(2,2)}=P_0+P_1+P_2$ | bookkeeping | N/A | none | N/A | STRUCTURAL |
| Eqs. (C-41), (C-42), (C-43), (C-44) -> Eq. (C-40) | $\mathcal{C}_{nnm}^{(2,2)}\propto Q_0+Q_1+Q_2+Q_3$ | definition | N/A | none | N/A | STRUCTURAL |
| Eqs. (C-47), (C-48), (C-49), (C-50) -> Eq. (C-46) | $\mathcal{C}_{nmm}^{(2,2)}\propto U_0+\cdots+U_3$ | definition | N/A | none | N/A | STRUCTURAL |
| Eqs. (C-53), (C-54), (C-55) -> Eq. (C-52) | $\mathcal{C}_{nml}^{(2,2)}\propto R_0+R_1+R_2$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (D-57) | $\sigma_{abc}=\Gamma^{-2}\sigma^{(-2)}+\Gamma^{-1}\sigma^{(-1)}+\sigma^{(0)}+O(\Gamma)$ | asymptotic expansion | UNKNOWN | author-declared $O(\Gamma)$ remainder | UNKNOWN | UNKNOWN_REMAINDER |
| Eq. (D-58) | $\sigma^{(-2)}$ written in $K_1,K_2$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (D-59) -> Eq. (D-60) | $K_{1A}$ regroup | algebra | ZERO | none | N/A | EXACT_ZERO |
| unnumbered metric-velocity identity -> Eq. (D-60) | metric-velocity pair index order | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-60) | $K_{1A}\to 2\epsilon_{12}^2(v_1^c g_{ab}+v_1^b g_{ac})$ | substitution | NONZERO | substitute $v_{12}^a v_{21}^b+v_{12}^b v_{21}^a=2\epsilon_{12}^2 g_{ab}$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eq. (D-60) -> Eq. (D-61) | $T_A^{(-2)}$ prefactor $2\epsilon_{12}^2/(8\epsilon_{12})=\epsilon_{12}/4$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eqs. (D-61), (D-67) -> Eq. (D-68) | $T_A+T_{B,\mathrm{geo}}$ cancellation | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-62) | $T_B^{(-2)}$ prefactor from $K_{nB}$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-62) -> Eq. (D-63) | insert $v_{nn}^{ab}=\partial_a\partial_b\epsilon_n-2\epsilon_{n\bar n}g_{ab}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (D-63) -> Eq. (D-64) | $T_B=T_{B,\mathrm{intra}}+T_{B,\mathrm{geo}}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (D-64) -> Eq. (D-65) | $T_{B,\mathrm{intra}}=-\frac18\sum_n\partial_a(v_n^b v_n^c)f_n'$ | algebra | N/A | none | N/A | UNSUPPORTED |
| Eq. (D-64) -> Eq. (D-66) | $T_{B,\mathrm{geo}}$ two-band form | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eqs. (D-65), (D-68) -> Eq. (D-69) | $\sigma^{(-2)}$ purely intraband | substitution | N/A | after $T_A+T_{B,\mathrm{geo}}=0$; convention $f_n'=2f_{0,n}'$ | N/A | UNSUPPORTED |
| Eq. (D-66) -> Eq. (D-67) | $T_{B,\mathrm{geo}}$ with $\epsilon_{21}=-\epsilon_{12}$ | substitution | NONZERO | substitute $\epsilon_{21}=-\epsilon_{12}$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eqs. (D-70), (D-76) -> Eq. (D-77) | $(-i)(i\epsilon_{12}^2)/(4\epsilon_{12}^2)=1/4$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-71) -> Eq. (D-72) | $C_1,C_2$ regroup | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eqs. (D-72), (D-75) -> Eq. (D-76) | $C_1,C_2$ in $\Omega$ | substitution | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-73) | $V_{ab}$ Feynman-Hellmann expansion | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-73) (second equality) | $V_{ab}$ with $\epsilon_{12}\epsilon_{21}=-\epsilon_{12}^2$ | substitution | NONZERO | substitute $\epsilon_{21}=-\epsilon_{12}$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eq. (D-74) | $A_{21}^a A_{12}^b-A_{12}^a A_{21}^b=-(A_{12}^a A_{21}^b-A_{12}^b A_{21}^a)$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-74) -> Eq. (D-75) | $V_{ab}=i\epsilon_{12}^2\Omega_{ab}^1$ | substitution | NONZERO | substitute $\Omega_{ab}^1:=i(A_{12}^a A_{21}^b-A_{12}^b A_{21}^a)$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eq. (D-77) -> Eq. (D-78) | $\Omega^2=-\Omega^1$ compactification | index relabeling | NONZERO | substitute $\Omega^2=-\Omega^1$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eq. (D-79) | $1/4!=1/24$ in $T_4$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eqs. (D-79), (D-116) -> Eq. (D-117) | $\sigma^{\mathrm{kin}}=T_3+T_4=\frac12 T_4$ | substitution | NONZERO | substitute $f_n^{(4)}=2f_{0,n}^{(4)}$ on the last equality | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eq. (D-80) | $T_3$ written in $K_1,K_2$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (D-81) -> Eq. (D-82) | $T_{3A}$ prefactor $2\epsilon_{12}^2/(48\epsilon_{12})=\epsilon_{12}/24$ | algebra | ZERO | after substituting the metric-velocity pair into $K_{nA}$ | N/A | EXACT_ZERO |
| Eq. (D-81) -> Eq. (D-83) | $T_{3B}$ prefactor from $K_{nB}$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eqs. (D-82), (D-86) | $T_{3B}^{\mathrm{inter}}=-T_{3A}$ | substitution | NONZERO | substitute $\epsilon_{21}=-\epsilon_{12}$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eqs. (D-82), (D-85), (D-86) -> Eq. (D-87) | $T_3=T_{3B}^{\mathrm{intra}}$ after geometric cancel | algebra | N/A | none | N/A | UNSUPPORTED |
| Eq. (D-83) -> Eq. (D-84) | insert diagonal second-derivative identity into $T_{3B}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (D-84) -> Eqs. (D-85), (D-86) | $T_{3B}^{\mathrm{intra}}$ and $T_{3B}^{\mathrm{inter}}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (D-87) -> Eq. (D-115) | $T_3$ IBP | BZ integration by parts | N/A | periodic Brillouin-zone torus; local Leibniz identity checked exactly | local Leibniz child ZERO | CERTIFIED_BY_RULE |
| Eq. (D-88) -> Eq. (D-89) | $T_2$ metric substitution | substitution | NONZERO | substitute $v_{21}^b v_{12}^c+v_{12}^b v_{21}^c=2\epsilon_{12}^2 g_{bc}$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eqs. (D-89), (D-121) -> Eq. (D-122) | $\sigma^{\mathrm{geo}}=T_2+(T_0+T_1)$ | bookkeeping | N/A | none | N/A | STRUCTURAL |
| Eq. (D-89) -> Eq. (D-123) | $v_n^a f_n^{(2)}=\partial_a(f_n')$ | algebra | N/A | none | N/A | UNSUPPORTED |
| Eqs. (D-90), (D-92) -> Eq. (D-93) | $T_1$ prefactor $2\epsilon_{12}^2/(2\epsilon_{12}^3)=1/\epsilon_{12}$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-91) -> Eq. (D-92) | $T_1$ coefficient $C_1$ regroup and metric | substitution | NONZERO | substitute the metric-velocity pair | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eqs. (D-119), (D-93) -> Eq. (D-120) | $T_0+T_1$ combined $f'$ terms | algebra | N/A | none | N/A | UNSUPPORTED |
| Eqs. (D-94), (D-112) -> Eq. (D-113) | $T_0$ after simplified $C_0$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-95) -> Eq. (D-96) | $A=6\epsilon_{12}^2 g_{bc}(v_2^a-v_1^a)$ | substitution | NONZERO | substitute $v_{21}^b v_{12}^c+v_{12}^b v_{21}^c=2\epsilon_{12}^2 g_{bc}$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eq. (D-95) -> Eq. (D-97) | $B=2\epsilon_{12}^2[g_{ac}(v_2^b-v_1^b)+g_{ab}(v_2^c-v_1^c)]$ | substitution | NONZERO | substitute the metric-velocity pair | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eqs. (D-96), (D-97), (D-109) -> Eq. (D-110) | $C_0=A+B+E$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-98) -> Eq. (D-99) | $S_{ac;b}+S_{ab;c}$ | algebra | N/A | none | N/A | UNSUPPORTED |
| Eq. (D-99) -> Eq. (D-100) | metric-velocity inside $\partial_a(v_{21}^c v_{12}^b+\cdots)$ | substitution | NONZERO | substitute the metric-velocity pair | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eqs. (D-100), (D-106) -> Eq. (D-107) | $-i K_{abc}$ becomes $-2\epsilon_{12}[\cdots]$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-101) -> Eq. (D-102) | two-band commutators into $K_{ab;c}$ | algebra | N/A | none | N/A | UNSUPPORTED |
| Eq. (D-103) | $P_{\mathrm{gauge}}=0$ by commuting velocities | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eqs. (D-104), (D-105) -> Eq. (D-106) | $K_{abc}=-2i\epsilon_{12}[(v_2^c-v_1^c)g_{ab}+\cdots]$ | substitution | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-105) | $A_{12}^a v_{21}^b-A_{21}^a v_{12}^b=-i\epsilon_{12}(A_{12}^a A_{21}^b+A_{21}^a A_{12}^b)$ | substitution | NONZERO | substitute $\epsilon_{21}=-\epsilon_{12}$; last paper equality $A_{12}^a A_{21}^b+A_{21}^a A_{12}^b=2g_{ab}$ is the declared metric convention | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eqs. (D-107), (D-108) -> Eq. (D-109) | $E=(S_{ac;b}+S_{ab;c})\epsilon_{12}$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-108) | $\partial_a(2\epsilon_{12}^2 g_{bc})=4\epsilon_{12}(v_1^a-v_2^a)g_{bc}+2\epsilon_{12}^2\partial_a g_{bc}$ | algebra | NONZERO | substitute $\partial_a\epsilon_{12}=v_1^a-v_2^a$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eq. (D-110) -> Eq. (D-111) | $C_0$ grouped by $g_{bc},g_{ac},g_{ab}$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-111) -> Eq. (D-112) | $g_{ac}$ and $g_{ab}$ coefficients cancel | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-113) -> Eq. (D-114) | $T_0=(f_1-f_2)\partial_a(g_{bc}/\epsilon_{12})$ | algebra | NONZERO | substitute $v_2^a-v_1^a=-\partial_a\epsilon_{12}$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eq. (D-114) -> Eq. (D-119) | $T_0$ BZ integration by parts | BZ integration by parts | N/A | periodic Brillouin-zone torus; local Leibniz identity checked exactly | local Leibniz child ZERO | CERTIFIED_BY_RULE |
| Eq. (D-115) -> Eq. (D-116) | chain rule $\partial_a f_n^{(3)}=f_n^{(4)} v_n^a$; $T_3=-\frac12 T_4$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-117) -> Eq. (D-118) | further BZ IBP $\sigma^{\mathrm{kin}}\propto(\partial_a\partial_b\partial_c\epsilon_n)f_0^{(2)}$ | BZ integration by parts | N/A | periodic Brillouin-zone torus; local Leibniz identity checked exactly | local Leibniz child ZERO | CERTIFIED_BY_RULE |
| Eq. (D-119) | $T_0$ local sign algebra after IBP | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-120) -> Eq. (D-121) | $T_0+T_1$ regroup by $f_1',f_2'$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eqs. (D-122), (D-124) -> Eq. (D-125) | $\sigma^{\mathrm{geo}}$ after declared $T_2$ IBP | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (D-123) -> Eq. (D-124) | $T_2$ BZ integration by parts | BZ integration by parts | N/A | periodic Brillouin-zone torus; local Leibniz identity checked exactly | local Leibniz child ZERO | CERTIFIED_BY_RULE |
| Eq. (D-125) -> Eq. (D-126) | $\epsilon_{21}=-\epsilon_{12}$ symmetrization | substitution | NONZERO | substitute $\epsilon_{21}=-\epsilon_{12}$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eq. (D-126) -> Eq. (D-127) | compact $n,\bar n$ form with $f_n'=2f_{0,n}'$ | index relabeling | NONZERO | substitute $f_n'=2f_{0,n}'$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eq. (E-128) | multiband $v_{nn}^{ab}$ identity | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (E-129) | multiband off-diagonal $v_{nm}^{ab}$ identity | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (E-130) -> Eq. (E-131) | multiband $\sigma^{(-2)}$ after diagonal $v_{nn}^{ab}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (E-132) -> Eq. (E-133) | multiband $\sigma^{(-1)}$ via curvature-velocity | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (E-134) | $\sigma^{(0)}=T_0+\cdots+T_4$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (E-135) | $T_4=\frac{1}{4!}\sum_n v_n^a v_n^b v_n^c f_n^{(4)}$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eqs. (E-135), (E-147) -> Eq. (E-148) | $\sigma^{\mathrm{kin}}=\frac12 T_4$ | algebra | NONZERO | local $T_3=-\frac12 T_4$ after declared IBP; substitute $f_n^{(4)}=2f_{0,n}^{(4)}$ | ZERO | ZERO_UNDER_SUBSTITUTION |
| Eq. (E-135) -> Eq. (F-158) | $T_4^{\mathrm{SHG}}=-T_4$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (E-136) -> Eq. (E-137) | multiband $T_3$ after diagonal $v_{nn}^{ab}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (E-137) -> Eq. (E-147) | multiband $T_3$ IBP $=-\frac12 T_4$ | BZ integration by parts | N/A | periodic Brillouin-zone torus; local Leibniz identity checked exactly | local Leibniz child ZERO | CERTIFIED_BY_RULE |
| Eq. (E-138) -> Eq. (E-139) | multiband $T_2$ via metric-velocity | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (E-139) -> Eq. (E-150) | multiband $T_2$ IBP | BZ integration by parts | N/A | periodic Brillouin-zone torus; local Leibniz identity checked exactly | local Leibniz child ZERO | CERTIFIED_BY_RULE |
| Eq. (E-140) -> Eq. (E-141) | multiband $T_1$ via $\mathcal{G}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eqs. (E-141), (E-149), (E-150) -> Eq. (E-151) | multiband $\sigma^{\mathrm{geo}}$ assembly | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (E-142) -> Eq. (E-143) | multiband remainder $\mathcal{M}=0$ | algebra | N/A | none | N/A | UNSUPPORTED |
| Eqs. (E-142), (E-143) -> Eq. (E-144) | $T_0$ reduces to two-band index terms | bookkeeping | N/A | none | N/A | STRUCTURAL |
| Eq. (E-144) -> Eq. (E-145) | shift-vector identity in $T_0$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (E-145) -> Eq. (E-146) | $T_0=\sum_n f_n\partial_a\mathcal{G}_n^{bc}$ | algebra | N/A | none | N/A | UNSUPPORTED |
| Eq. (E-146) -> Eq. (E-149) | multiband $T_0$ IBP | BZ integration by parts | N/A | periodic Brillouin-zone torus; local Leibniz identity checked exactly | local Leibniz child ZERO | CERTIFIED_BY_RULE |
| Eq. (F-152) | SHG $\Gamma$ expansion | asymptotic expansion | UNKNOWN | author-declared $O(\Gamma)$ remainder | UNKNOWN | UNKNOWN_REMAINDER |
| Eq. (F-153) -> Eq. (F-154) | SHG $\sigma^{(-2)}$ after $v_{nn}^{ab}$ and IBP | BZ integration by parts | N/A | periodic Brillouin-zone torus; local Leibniz identity checked exactly | local Leibniz child ZERO | CERTIFIED_BY_RULE |
| Eq. (F-155) -> Eq. (F-156) | SHG $\sigma^{(-1)}$ via curvature-velocity | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (F-157) | $\sigma^{\mathrm{SHG}(0)}=T_0^{\mathrm{SHG}}+\cdots+T_4^{\mathrm{SHG}}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eqs. (F-164), (F-165), (F-166), (F-167), (F-168) -> Eq. (F-157) | $T_0^{\mathrm{SHG}}$ split into five pieces | definition | N/A | none | N/A | STRUCTURAL |
| Eqs. (F-158), (F-177) -> Eq. (F-178) | SHG $\sigma^{\mathrm{kin}}$: $-\frac1{24}+\frac{3}{48}=\frac1{48}$ | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eq. (F-159) -> Eq. (F-160) | $T_3^{\mathrm{SHG}}$ after diagonal $v_{nn}^{ab}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (F-160) -> Eq. (F-177) | $T_3^{\mathrm{SHG}}$ IBP using $4\partial_b\partial_c\epsilon\,\partial_a\epsilon$ identity | BZ integration by parts | N/A | periodic Brillouin-zone torus; local Leibniz identity checked exactly | local Leibniz child ZERO | CERTIFIED_BY_RULE |
| Eq. (F-161) | $T_2^{\mathrm{SHG}}=T_2$ | bookkeeping | N/A | none | N/A | STRUCTURAL |
| Eq. (F-161) -> Eq. (F-180) | $T_2^{\mathrm{SHG}}$ IBP | BZ integration by parts | N/A | periodic Brillouin-zone torus; local Leibniz identity checked exactly | local Leibniz child ZERO | CERTIFIED_BY_RULE |
| Eq. (F-162) -> Eq. (F-163) | $T_1^{\mathrm{SHG}}$ via $\mathcal{G}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eqs. (F-163), (F-179), (F-180) -> Eq. (F-181) | SHG $\sigma^{\mathrm{geo}}$ assembly | algebra | ZERO | none | N/A | EXACT_ZERO |
| Eqs. (F-164), (F-171), (F-173) -> Eq. (F-174) | $T_0^{\mathrm{SHG}}$ reduces to two-band terms | bookkeeping | N/A | none | N/A | STRUCTURAL |
| Eq. (F-165) -> Eq. (F-169) | expand off-diagonal $v_{nm}^{ab}$ in $T_{0,2}^{\mathrm{SHG}}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eqs. (F-166), (F-169) -> Eq. (F-171) | $T_{0,2}+T_{0,3}$ two-band vs multiband split | bookkeeping | N/A | none | N/A | STRUCTURAL |
| Eqs. (F-167), (F-168), (F-171) -> Eq. (F-172) | SHG multiband remainder $\mathcal{M}$ | bookkeeping | N/A | none | N/A | STRUCTURAL |
| Eq. (F-169) -> Eq. (F-170) | rewrite $A_{nn}-A_{mm}$ by off-diagonal $v_{nm}^{ab}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (F-172) -> Eq. (F-173) | SHG $\mathcal{M}=0$ after dummy-index reclassification | algebra | N/A | none | N/A | UNSUPPORTED |
| Eq. (F-174) -> Eq. (F-175) | Feynman-Hellmann rewrite of $T_0^{\mathrm{SHG}}$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (F-175) -> Eq. (F-176) | $T_0^{\mathrm{SHG}}=-\sum_n f_n(2\partial_c\mathcal{G}^{ab}+\cdots)$ | algebra | N/A | none | N/A | UNSUPPORTED |
| Eq. (F-176) -> Eq. (F-179) | $T_0^{\mathrm{SHG}}$ IBP | BZ integration by parts | N/A | periodic Brillouin-zone torus; local Leibniz identity checked exactly | local Leibniz child ZERO | CERTIFIED_BY_RULE |
| Eq. (G-182) -> Eq. (G-183) | open-system Schrödinger equation for $\psi_n^j$ | definition | N/A | none | N/A | STRUCTURAL |
| Eqs. (G-182), (G-183) -> Eq. (G-184) | $i\partial_t\rho_S=[H_S,\rho_S]-2i\Gamma\rho_S+\mathcal{S}$ | algebra | N/A | none | N/A | UNSUPPORTED |
| Eq. (G-184) -> Eq. (G-185) | static-Hamiltonian approximation for $\psi_n^j$ | definition | N/A | none | N/A | STRUCTURAL |
| Eq. (G-185) -> Eq. (G-186) | source $\mathcal{S}$ after static approximation | algebra | N/A | none | N/A | UNSUPPORTED |
| Eq. (G-186) -> Eq. (G-187) | $\Gamma$ truncation $\mathcal{S}=2i\Gamma\rho_0+O(\Gamma^2)$ | asymptotic expansion | UNKNOWN | author-declared $O(\Gamma^2)$ remainder plus static-Hamiltonian approximation | UNKNOWN | UNKNOWN_REMAINDER |
| Eq. (G-187) -> Eq. (G-188) | Lorentzian as Fourier convolution $e^{-\Gamma k}$ | special function identity | N/A | none | N/A | UNSUPPORTED |
| Eq. (G-187) -> Eq. (G-189) | RTA/IFR Liouville equation after two approximations | definition | N/A | none | N/A | STRUCTURAL |

## Summary

- numbered equations inventoried: 189/189
- derivation relations: 146
- EXACT_ZERO: 32
- ZERO_UNDER_SUBSTITUTION: 21
- CERTIFIED_BY_RULE: 11
- UNKNOWN_REMAINDER: 17
- STRUCTURAL / NO_EQUALITY_CLAIM: 47
- UNSUPPORTED / COMPILE_FAILURE: 18
- NONZERO: 0
- false promotion on injected controls: 0/155
