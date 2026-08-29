"""Curated parameter probes. Guo atoms are not used.

A witness satisfies DECLARED symbol flags, positivity_conditions, and
nonzero/analytic exclusions that are concrete enough to check, and still
makes a required kernel hit a pole, a cut, or a division by zero.
"""

from __future__ import annotations

from typing import Any

CLEAN = "CLEAN"
DISQUALIFIED = "DISQUALIFIED"
GAP = "GAP"
SKIPPED_REJECTED = "SKIPPED_REJECTED"
SKIPPED_GUO = "SKIPPED_GUO"

# Headline clean DLMF: declared/derived z-domain matches the pole set.
HEADLINE_CLEAN = "thermal-01-fermi-im-digamma"

# Optional sealed analogue only. Guo atom tables are not ingested.
GUO_ANALOGUE = {
    "used_as_candidate": False,
    "atoms_loaded": False,
    "note": (
        "Sealed source-assumption audit 9fc3c8a: frozen real-only beta, gamma "
        "allow beta=1, gamma=-pi, mu=0, epsilon(n)=0, hence z0=0 in Z_<=0. "
        "That is the pattern (declared symbol/positivity too weak for a "
        "required pole/cut/div0 predicate). This falsifier does not ingest "
        "Guo atoms or the G0016 table."
    ),
}


def _w(
    witness_id: str,
    assignment: dict[str, Any],
    kind: str,
    predicate: str,
    declared_ok: list[str],
    expr: str,
    fix: str,
) -> dict[str, Any]:
    return {
        "witness_id": witness_id,
        "assignment": assignment,
        "kind": kind,
        "predicate": predicate,
        "declared_ok": declared_ok,
        "probe": {"expr": expr, "expect_singular": True},
        "fix": fix,
    }


def _blocked(
    assignment: dict[str, Any],
    expr: str,
    blocked_by: str,
) -> dict[str, Any]:
    return {
        "assignment": assignment,
        "probe": {"expr": expr, "expect_singular": True},
        "declared_blocks": True,
        "blocked_by": blocked_by,
    }


def _finite(assignment: dict[str, Any], expr: str) -> dict[str, Any]:
    return {
        "assignment": assignment,
        "probe": {"expr": expr, "expect_singular": False},
    }


# ---------------------------------------------------------------------------
# DISQUALIFIED: interior assignment allowed by DECLARED flags/exclusions
# ---------------------------------------------------------------------------

DISQUALIFIED_WITNESSES: dict[str, list[dict[str, Any]]] = {
    "ac-r04-lindhard-occupation-dd": [
        _w(
            "ac-r04-hbar-zero",
            {"hbar": 0, "m": 1, "delta": 1, "omega": 1, "k": 1, "q": 1},
            "division_by_zero",
            (
                "Lindhard denominator hbar*(omega+I*delta)+(E(k+q)-E(k)) with "
                "E=hbar**2 k**2/(2m) vanishes identically when hbar=0"
            ),
            [
                "hbar real, no nonzero/positive flag",
                "m real; positivity not declared",
                "delta>0 DECLARED",
                "omega real",
            ],
            "1/(hbar*(omega + I*delta) + (hbar**2/(2*m))*((k+q)**2 - k**2))",
            "Declare hbar != 0 in the problem statement (and typically m != 0).",
        ),
        _w(
            "ac-r04-m-zero",
            {"hbar": 1, "m": 0, "k": 1},
            "division_by_zero",
            "Kinetic energy E(k)=hbar**2 k**2/(2m) is undefined at m=0",
            [
                "m real; notes say m>0 is not inserted",
                "hbar real",
            ],
            "hbar**2 * k**2 / (2*m)",
            "Declare m != 0 (or m>0) in the problem statement.",
        ),
    ],
    "ac-r05-lehmann-spectral-master": [
        _w(
            "ac-r05-bose-zero-mode",
            {"omega_n": 0, "xi": 0, "beta": 2, "tau": 1, "zeta": 1, "eta": 1},
            "division_by_zero",
            (
                "Free Matsubara specialization G_M=1/(-I*omega_n+xi) at "
                "bosonic n=0 and xi=0 is 1/0; omega_n=0 is allowed by "
                "omega_n=[2n+theta(-zeta)]*pi/beta with zeta=+1, n=0"
            ),
            [
                "zeta integer (bosons +1)",
                "0<tau<beta DECLARED (tau=1, beta=2)",
                "eta real; not used in this Matsubara probe",
                "xi is written in the free specialization and not excluded from 0",
            ],
            "1/(-I*omega_n + xi)",
            (
                "Declare fermionic Matsubara frequencies, or omega_n != 0, or "
                "xi not on the real-axis evaluation point (z not in supp rho)."
            ),
        ),
        _w(
            "ac-r05-retarded-eta-zero",
            {"omega": 0, "eta": 0, "xi": 0, "beta": 2, "tau": 1},
            "pole",
            (
                "Retarded free kernel 1/(-(omega+I*eta)+xi) at eta=0, "
                "omega=xi is 1/0. eta is real with no positive flag; "
                "eta->0+ is only a limit_domain sentence"
            ),
            [
                "eta real, no positive/nonzero symbol flag",
                "omega real",
                "0<tau<beta DECLARED",
            ],
            "1/(-(omega + I*eta) + xi)",
            "Declare eta>0 (or eta != 0) as a symbol/positivity flag, not only eta->0+.",
        ),
    ],
    "ac-r06-matsubara-pole-family": [
        _w(
            "ac-r06-bose-occupancy-pole",
            {"beta": 1, "xi": 0, "eta": 1, "tau": "Rational(1,2)"},
            "pole",
            (
                "Bosonic occupancy n_B(xi)=1/(exp(beta*xi)-1) has a pole at "
                "xi=0, which is also the n=0 Matsubara frequency. thermal-08 "
                "recorded this exclusion as NOT_DECLARED; ac-r06 still omits it"
            ),
            [
                "eta integer +1 (bosons)",
                "xi complex, reality not extra-inserted",
                "0<tau<beta DECLARED (Green-function interval; does not exclude xi=0)",
                "two-pole nonzero_condition is xi1 != xi2 only",
            ],
            "1/(exp(beta*xi) - 1)",
            (
                "Declare occupancy-pole exclusion exp(beta*xi) != eta, and that "
                "poles of g are disjoint from {I*omega_n}, as thermal-08 listed."
            ),
        ),
    ],
    "ac-r07-lippmann-schwinger-iepsilon": [
        _w(
            "ac-r07-epsilon-zero",
            {"E": 0, "E_beta": 0, "epsilon": 0},
            "division_by_zero",
            (
                "E is declared an eigenvalue of H0, so the naive resolvent is "
                "singular. Causal kernel 1/(E-E_beta+I*epsilon) at epsilon=0 "
                "is 1/0. epsilon has no positive/nonzero flag; positivity_conditions "
                "are empty. 'Slightly complex' is source prose, not epsilon>0"
            ),
            [
                "E real (eigenvalue of H0 as written)",
                "epsilon unconstrained in symbol_assumptions",
                "no DECLARED positivity inequality epsilon>0",
            ],
            "1/(E - E_beta + I*epsilon)",
            "Declare epsilon>0 (or epsilon != 0) in the problem statement.",
        ),
    ],
    "thermal-07-green-spectral-hilbert": [
        _w(
            "thermal-07-omega-n-zero",
            {"omega_n": 0, "x": 0, "beta": 1, "eta": 1, "tau": "Rational(1,2)"},
            "pole",
            (
                "Hilbert integrand rho(x)/(-z+x) with z=I*omega_n at omega_n=0 "
                "places z on the real axis. x=0 is then a pole. Spectral support "
                "of rho is not restricted; omega_n is real with no nonzero flag. "
                "eta>0 and beta>0 (declared) do not exclude the bosonic zero mode"
            ),
            [
                "beta positive and eta positive in symbol_assumptions",
                "0<tau<beta DECLARED",
                "omega_n real, no nonzero flag",
                "analytic_domains do not exclude omega_n=0",
            ],
            "1/(-I*omega_n + x)",
            (
                "Declare omega_n != 0, or restrict to fermionic Matsubara "
                "frequencies (2n+1)*pi/beta, or exclude 0 from supp rho."
            ),
        ),
    ],
}

# ---------------------------------------------------------------------------
# GAP: encoding hole, but no interior pole witness (or only a limit point)
# ---------------------------------------------------------------------------

GAPS: dict[str, list[str]] = {
    "ac-r02-sokhotski-plemelj-boundary": [
        (
            "epsilon is real with no positive/nonzero flag; positivity only "
            "writes the limit epsilon->0+. The identity is that distributional "
            "limit, so epsilon=0 is the boundary rather than an interior "
            "parameter. Interior 1/(x+I*epsilon) for epsilon!=0 is holomorphic "
            "on real x. Encoding gap, not a Guo-style interior witness."
        ),
    ],
    "sciml-phi-hermite-01": [
        (
            "Newton quotient (exp(z)-1)/z at z=0 is 0/0, but the contract "
            "declares phi_k entire with value 1/k! at 0. Removable, not a pole."
        ),
    ],
    "sciml-vanloan-blockexp-01": [
        (
            "Scalar (exp(z)-1)/z at z=0 is the same removable point; entire "
            "continuation is DECLARED."
        ),
    ],
    "sciml-ou-mehler-01": [
        (
            "DERIVED text says theta>0 and t>0 imply v_t>0, omitting the "
            "declared sigma!=0 in that sentence. Under all DECLARED flags "
            "(sigma real nonzero) the implication holds; no witness."
        ),
    ],
    "ac-r03-helmholtz-outgoing-green": [
        (
            "n is an integer with analytic_domains n in {2,3}, while the "
            "written kernel is the 3D formula exp(I*k*R)/(4*pi*R). Wrong-n "
            "is a formula mismatch, not a pole witness. R=0 is DECLARED excluded; "
            "k>0 DECLARED; Euclidean |x-x0| has no cut on real vectors."
        ),
    ],
    "ac-r05-lehmann-spectral-master": [
        (
            "beta has no positive symbol flag; positivity is the tau-interval "
            "0<tau<beta. Enforcing that interval derives beta>0 and blocks "
            "beta=0 in 1/beta and omega_n ~ 1/beta. Remaining witnesses are "
            "the bosonic zero mode and eta=0 (catalogued as DISQUALIFIED)."
        ),
    ],
    "ac-r06-matsubara-pole-family": [
        (
            "0<tau<beta is scoped to Green-function weighting, not to the "
            "frequency table S=(1/beta)*Sum. beta=0 is a 1/beta division by "
            "zero if that positivity is not applied to the table. The xi=0 "
            "bosonic occupancy pole survives even with 0<tau<beta."
        ),
    ],
}

# ---------------------------------------------------------------------------
# CLEAN: declared exclusions match the pole/cut/div0 set, or the object
# is entire/polynomial/algebraic.
# ---------------------------------------------------------------------------

CLEAN_WHY: dict[str, str] = {
    "thermal-01-fermi-im-digamma": (
        "DLMF 5.4.17 with y a declared real variable. psi poles are "
        "Z_<=0 (DLMF 5.2.2). Re(1/2+I*y)=1/2 for real y, so "
        "1/2+I*y never in Z_<=0 (DERIVED). tanh has no real poles. y=0 is "
        "allowed and both sides vanish. No extra z not-in-Z declaration is "
        "needed; the declared real line already misses the pole set."
    ),
    "thermal-02-bose-im-digamma": (
        "DLMF 5.4.16. y real and y!=0 are DECLARED (1/(2y) and psi(I*y) at 0). "
        "For real y, I*y in Z_<=0 only at y=0. coth(pi*y) poles are imaginary "
        "except that same point. No remaining witness."
    ),
    "thermal-03-digamma-reflection": (
        "DLMF 5.5.4 writes z != 0, ±1, … (z not an integer) DECLARED. That "
        "is exactly the cot(pi z) pole set and implies z and 1-z avoid the "
        "psi pole set. Assignment z=1 hits polygamma(0,1) is finite but "
        "polygamma(0,0) and 1/tan(pi) are singular; it is blocked by the "
        "declared integer exclusion. Expected clean DLMF z not-in-Z case."
    ),
    "thermal-04-coth-matsubara": (
        "DLMF 4.36 writes z != n*pi*I DECLARED. Those are exactly the poles "
        "of coth/sinh. z=0 is the n=0 point and is excluded."
    ),
    "thermal-05-trigamma-double-pole": (
        "DLMF 5.15.1 writes z != 0,-1,-2,… DECLARED, matching trigamma poles. "
        "z=1 is a positive integer, allowed, and psi'(1)=pi**2/6 is finite."
    ),
    "thermal-06-fermi-dirac-polylog": (
        "F_s: s>-1 DECLARED; argument -exp(x) lies in (-oo,0] for real x, "
        "off the polylog cut [1,oo). G_s domain (s>-1 and x<0) or (s>0 and "
        "x<=0) DECLARED; x=0 is on the branch point only when s>0, where "
        "Li_{s+1}(1)=zeta(s+1) is finite. Gamma(s+1) poles are DERIVED-excluded "
        "by s>-1."
    ),
    "ac-r01-resolvent-hilbert-identity": (
        "z,w in rho(A) DECLARED, which is invertibility of (A-z I) and (A-w I). "
        "The product form of Hilbert's identity has no extra (z-w) pole; the "
        "Newton quotient's z=w point is a declared holomorphic continuation."
    ),
    "ac-r03-helmholtz-outgoing-green": (
        "k>0 DECLARED, R!=0 DECLARED, |x-x0| the Euclidean (nonnegative) root "
        "on real vectors. The only elementary pole is R=0, already excluded."
    ),
    "mp-cauchy-dunford-01": (
        "f analytic on and inside Gamma, and Gamma disjoint from Lambda(A), "
        "are DECLARED (Higham Def. 1.11). That is the resolvent pole set."
    ),
    "mp-daleckii-krein-01": (
        "C^{2n-1} on an open D containing the spectrum, Z invertible, and "
        "the equal-eigenvalue clause as a definition (not a 0/0 to take) "
        "are DECLARED."
    ),
    "mp-hermite-fA-01": (
        "f defined on the spectrum (jets exist) is DECLARED. Holomorphy is "
        "correctly not inserted. No hidden pole of a named f."
    ),
    "mp-kato-simple-ev-01": (
        "Simple eigenvalue, analytic family, and y0* x0=1 are DECLARED. "
        "A multiple eigenvalue is excluded by Assumption 1, not a witness."
    ),
    "mp-mathias-block-01": (
        "C^{2n-1} on D containing spec(X), and spec(A(t)) stays in D near 0, "
        "are DECLARED."
    ),
    "mp-opitz-dd-01": (
        "Polynomial identity, or Hermite jet existence for non-polynomials, "
        "DECLARED. Repeated nodes are in-scope, not poles."
    ),
    "mp-parlett-schur-01": (
        "Scalar recurrence requires distinct diagonals DECLARED; the equal-"
        "diagonal 0/0 is the block/Sylvester stratum, also DECLARED."
    ),
    "mp-resolvent-dd-01": (
        "lambda, mu in rho(A) and z in rho(A)∩rho(B) DECLARED. Spectrum is "
        "the pole set of R, and it is excluded."
    ),
    "sciml-adjoint-linear-01": (
        "Linear constant-coefficient ODE: exp(t A) is entire. T>0 DECLARED. "
        "No pole."
    ),
    "sciml-ou-mehler-01": (
        "theta>0, t>0, sigma!=0, beta>0 DECLARED. Then v_t>0 and the real "
        "square root is defined. Gaussian density has no poles for t>0."
    ),
    "sciml-phi-hermite-01": (
        "phi_k entire on C DECLARED. Quotient z!=0 is a presentation, not a "
        "domain hole; z=0 is the declared value 1/k!."
    ),
    "sciml-vanloan-blockexp-01": (
        "exp entire, so the block identity has no spectral restriction. "
        "Scalar (e^z-1)/z uses the declared entire continuation."
    ),
    "sciml-daleckii-krein-01": (
        "spec(A) subset D, Z invertible, off-diagonal lam_i!=lam_j, and "
        "0 not in spec(A) for the inverse specialization, all DECLARED."
    ),
    "sciml-deq-ift-01": (
        "I-D_z f invertible DECLARED (scalar 1-w*sech**2 != 0). Neumann "
        "member separately requires rho(J)<1, also DECLARED."
    ),
    "sciml-lyapunov-kronecker-01": (
        "spec(A)∩spec(-B) empty DECLARED for uniqueness; Re spec(A)<0 "
        "DECLARED for the Gramian integral. 1x1 probe a!=0 DECLARED."
    ),
    "sciml-tweedie-gauss-01": (
        "sigma>0, tau>0 DECLARED imply marginal variance >0 and f>0, so "
        "real log f has no cut."
    ),
    "ac-t-clebsch-half": (
        "Finite Pauli algebra; 1/sqrt(2) uses the declared positive real root. "
        "No meromorphic poles."
    ),
    "ac-t-eps-delta": (
        "Levi-Civita / Kronecker identities on {1,2,3}. Polynomial, no poles."
    ),
    "ac-t-ricci-weyl": (
        "n=4 DECLARED, hence n(n-1) and n-2 invertible; g nondegenerate "
        "DECLARED so g^{-1} exists."
    ),
    "ac-t-weyl-su2-char": (
        "z!=0 DECLARED; quotient form z**2!=1 (sin theta !=0) DECLARED. "
        "Division-free polynomial identity holds on all of C."
    ),
    "ac-t-young-s3": (
        "Scalars 3 and 6 invertible (char 0) DECLARED. Group-algebra "
        "polynomials, no poles."
    ),
    "ac-t-iso4-projectors": (
        "dim=3 nonzero DECLARED. Kronecker projectors; 1/3 is in Q."
    ),
    "ac-t-pauli-completeness": (
        "Explicit 2x2 Pauli products and completeness. Algebraic, no poles."
    ),
}

CLEAN_PROBES: dict[str, dict[str, Any]] = {
    "thermal-01-fermi-im-digamma": {
        "finite": [
            _finite({"y": 0}, "polygamma(0, Rational(1,2) + I*y)"),
            _finite({"y": 1}, "polygamma(0, Rational(1,2) + I*y)"),
            _finite({"y": -1}, "polygamma(0, Rational(1,2) + I*y)"),
            _finite({"y": 0}, "(pi/2)*tanh(pi*y)"),
        ],
        "blocked": [],
    },
    "thermal-02-bose-im-digamma": {
        "finite": [
            _finite({"y": 1}, "polygamma(0, I*y)"),
            _finite({"y": -2}, "cosh(pi*y)/sinh(pi*y)"),
        ],
        "blocked": [
            _blocked({"y": 0}, "polygamma(0, I*y)", "DECLARED y != 0"),
            _blocked({"y": 0}, "Rational(1,2)/y", "DECLARED y != 0"),
        ],
    },
    "thermal-03-digamma-reflection": {
        "finite": [
            _finite(
                {"z": "Rational(1,2)"},
                "polygamma(0, z) - polygamma(0, 1 - z) + pi/tan(pi*z)",
            ),
        ],
        "blocked": [
            _blocked({"z": 0}, "polygamma(0, z)", "DECLARED z not an integer"),
            _blocked({"z": 1}, "polygamma(0, 1 - z)", "DECLARED z not an integer"),
            _blocked({"z": 1}, "1/tan(pi*z)", "DECLARED z not an integer"),
            _blocked({"z": -1}, "polygamma(0, z)", "DECLARED z not an integer"),
        ],
    },
    "thermal-04-coth-matsubara": {
        "finite": [
            _finite({"z": 1}, "cosh(z)/sinh(z)"),
            _finite({"z": "pi"}, "cosh(z)/sinh(z)"),
        ],
        "blocked": [
            _blocked({"z": 0}, "cosh(z)/sinh(z)", "DECLARED z != n*pi*I"),
            _blocked({"z": "I*pi"}, "cosh(z)/sinh(z)", "DECLARED z != n*pi*I"),
        ],
    },
    "thermal-05-trigamma-double-pole": {
        "finite": [
            _finite({"z": 1}, "polygamma(1, z)"),
            _finite({"z": "Rational(1,2)"}, "polygamma(1, z)"),
            _finite({"z": "I"}, "polygamma(1, z)"),
        ],
        "blocked": [
            _blocked({"z": 0}, "polygamma(1, z)", "DECLARED z not a nonpositive integer"),
            _blocked({"z": -1}, "polygamma(1, z)", "DECLARED z not a nonpositive integer"),
            _blocked({"z": -2}, "polygamma(1, z)", "DECLARED z not a nonpositive integer"),
        ],
    },
    "ac-r03-helmholtz-outgoing-green": {
        "finite": [
            _finite({"k": 1, "R": 1}, "exp(I*k*R)/(4*pi*R)"),
        ],
        "blocked": [
            _blocked(
                {"k": 1, "R": 0},
                "exp(I*k*R)/(4*pi*R)",
                "DECLARED R != 0",
            ),
        ],
    },
    "sciml-phi-hermite-01": {
        "finite": [
            _finite({"z": 1}, "(exp(z) - 1)/z"),
        ],
        "blocked": [
            _blocked(
                {"z": 0},
                "(exp(z) - 1)/z",
                "DECLARED entire continuation phi_1(0)=1; raw quotient is 0/0, not a pole",
            ),
        ],
    },
    "ac-t-weyl-su2-char": {
        "finite": [
            _finite({"z": 2}, "(z**2 - 1)"),
        ],
        "blocked": [
            _blocked(
                {"z": 1},
                "1/(z - 1/z)",
                "DECLARED z**2 != 1 for the quotient form",
            ),
        ],
    },
}
