"""Frozen proposer-visible DEV packs. Hidden gold lives in hidden/.

Catalog IDs are task-local (not Guo atoms). No gold type names.
"""
from __future__ import annotations

# Forbidden in proposer-visible blobs (case-insensitive).
PUBLIC_FORBIDDEN = (
    "divided difference",
    "divided_difference",
    "newton dd",
    "newton_dd",
    "hermite",
    "confluence",
    "phi_gamma",
    "master function",
    "hurwitz",
    "matsubara",
    "fermi-dirac",
    "loewner",
    "hadamard product",
    "genocchi",
    "f[z,w]",
    "f[z, w]",
)

CORE = [
    "mp-resolvent-dd-01",
    "ac-r01-resolvent-hilbert-identity",
    "thermal-01-fermi-im-digamma",
    "thermal-03-digamma-reflection",
    "thermal-05-trigamma-double-pole",
    "sciml-phi-hermite-01",
]

PACKAGING_GAP = [
    "mp-daleckii-krein-01",
    "mp-hermite-fA-01",
    "mp-cauchy-dunford-01",
    "sciml-vanloan-blockexp-01",
    "sciml-daleckii-krein-01",
    "ac-t-eps-delta",
    "ac-t-young-s3",
    "ac-r03-helmholtz-outgoing-green",
]

P4_ELIGIBLE = [
    "mp-resolvent-dd-01",
    "ac-r01-resolvent-hilbert-identity",
    "sciml-phi-hermite-01",
]

CLUSTER_OF = {
    "mp-resolvent-dd-01": "RESOLVENT_CLUSTER",
    "ac-r01-resolvent-hilbert-identity": "RESOLVENT_CLUSTER",
    "mp-daleckii-krein-01": "DALECKII_KREIN_CLUSTER",
    "sciml-daleckii-krein-01": "DALECKII_KREIN_CLUSTER",
    "mp-hermite-fA-01": "MP_HERMITE_FA",
    "mp-cauchy-dunford-01": "MP_CAUCHY_DUNFORD",
    "thermal-01-fermi-im-digamma": "THERMAL_01_FERMI_DIGAMMA",
    "thermal-03-digamma-reflection": "THERMAL_03_DIGAMMA_REFLECTION",
    "thermal-05-trigamma-double-pole": "THERMAL_05_TRIGAMMA_SERIES",
    "sciml-phi-hermite-01": "SCIML_PHI_EXP_FAMILY",
    "sciml-vanloan-blockexp-01": "SCIML_VANLOAN",
    "ac-t-eps-delta": "TENSOR_EPS_DELTA",
    "ac-t-young-s3": "TENSOR_YOUNG_S3",
    "ac-r03-helmholtz-outgoing-green": "HELMHOLTZ_OUTGOING_GREEN",
}

PUBLIC_ID = {
    "mp-resolvent-dd-01": "T01",
    "ac-r01-resolvent-hilbert-identity": "T02",
    "thermal-01-fermi-im-digamma": "T03",
    "thermal-03-digamma-reflection": "T04",
    "thermal-05-trigamma-double-pole": "T05",
    "sciml-phi-hermite-01": "T06",
}


def _cat(*rows: tuple[str, str]) -> list[dict]:
    out = []
    for i, (gid, text) in enumerate(rows, 1):
        out.append({"source_node_id": gid, "kind": "expr", "ops_hint": None, "text": text})
        assert gid == f"G{i:04d}"
    return out


PUBLIC_PACKS: dict[str, dict] = {
    "mp-resolvent-dd-01": {
        "case_id": "mp-resolvent-dd-01",
        "public_id": "T01",
        "split": "DEV",
        "stratum": "CORE_COMPARABLE",
        "cluster_id": "RESOLVENT_CLUSTER",
        "domain": "mathphys",
        "current": "(1/(lam - a) - 1/(mu - a))/(lam - mu) + 1/((lam - a)*(mu - a))",
        "symbols": [
            {"name": "lam", "real": True},
            {"name": "mu", "real": True},
            {"name": "a", "real": True},
        ],
        "functions": [],
        "assumptions": [
            "lam, mu, a are real parameters",
            "lam != mu",
            "lam != a",
            "mu != a",
            "the map t |-> 1/(t - a) is defined for t != a",
        ],
        "scientific_context": [
            "Scalar model of a resolvent kernel 1/(t-a) evaluated at two spectral parameters.",
            "Source family: first resolvent identity (Higham/Glück convention).",
            "Do not invent physical names.",
        ],
        "catalog": _cat(
            ("G0001", "1/(lam - a)"),
            ("G0002", "1/(mu - a)"),
            ("G0003", "(1/(lam - a) - 1/(mu - a))/(lam - mu)"),
            ("G0004", "1/((lam - a)*(mu - a))"),
            ("G0005", "(1/(lam - a) - 1/(mu - a))/(lam - mu) + 1/((lam - a)*(mu - a))"),
        ),
    },
    "ac-r01-resolvent-hilbert-identity": {
        "case_id": "ac-r01-resolvent-hilbert-identity",
        "public_id": "T02",
        "split": "DEV",
        "stratum": "CORE_COMPARABLE",
        "cluster_id": "RESOLVENT_CLUSTER",
        "domain": "green",
        "current": "(1/(a - z) - 1/(a - w))/(z - w) - 1/((a - z)*(a - w))",
        "symbols": [
            {"name": "a", "real": True},
            {"name": "z", "real": True},
            {"name": "w", "real": True},
        ],
        "functions": [],
        "assumptions": [
            "z != w",
            "a != z",
            "a != w",
            "the map t |-> 1/(a - t) is defined for t != a",
        ],
        "scientific_context": [
            "Scalar model of a resolvent kernel 1/(a-t) at two spectral parameters z and w.",
            "Convention: (A - zeta I)^{-1} (opposite sign relative to (zeta I - A)^{-1}).",
            "Do not invent physical names.",
        ],
        "catalog": _cat(
            ("G0001", "1/(a - z)"),
            ("G0002", "1/(a - w)"),
            ("G0003", "(1/(a - z) - 1/(a - w))/(z - w)"),
            ("G0004", "1/((a - z)*(a - w))"),
            ("G0005", "(1/(a - z) - 1/(a - w))/(z - w) - 1/((a - z)*(a - w))"),
        ),
    },
    "thermal-01-fermi-im-digamma": {
        "case_id": "thermal-01-fermi-im-digamma",
        "public_id": "T03",
        "split": "DEV",
        "stratum": "CORE_COMPARABLE",
        "cluster_id": "THERMAL_01_FERMI_DIGAMMA",
        "domain": "thermal",
        "current": "im(polygamma(0, Rational(1, 2) + I*y)) - (pi/2)*tanh(pi*y)",
        "symbols": [{"name": "y", "real": True}],
        "functions": ["im", "polygamma", "tanh"],
        "assumptions": [
            "y is a real variable",
            "1/2 + I*y is not a nonpositive integer (so polygamma(0, ·) is defined)",
            "tanh has no poles on the real axis",
        ],
        "scientific_context": [
            "Identity relating Im polygamma(0, 1/2 + I y) to tanh(pi y) (NIST DLMF 5.4.17).",
            "y real; y = 0 is allowed.",
            "Do not invent physical names.",
        ],
        "catalog": _cat(
            ("G0001", "im(polygamma(0, Rational(1, 2) + I*y))"),
            ("G0002", "(pi/2)*tanh(pi*y)"),
            ("G0003", "im(polygamma(0, Rational(1, 2) + I*y)) - (pi/2)*tanh(pi*y)"),
        ),
    },
    "thermal-03-digamma-reflection": {
        "case_id": "thermal-03-digamma-reflection",
        "public_id": "T04",
        "split": "DEV",
        "stratum": "CORE_COMPARABLE",
        "cluster_id": "THERMAL_03_DIGAMMA_REFLECTION",
        "domain": "thermal",
        "current": "polygamma(0, z) - polygamma(0, 1 - z) + pi/tan(pi*z)",
        "symbols": [{"name": "z", "real": True}],
        "functions": ["polygamma", "tan"],
        "assumptions": [
            "z is not an integer",
            "z and 1-z avoid the polygamma(0, ·) poles at nonpositive integers",
            "tan(pi*z) != 0 on the same set (equivalently z not integer)",
        ],
        "scientific_context": [
            "Three meromorphic expressions in z: polygamma at z, polygamma at 1-z, and pi/tan(pi z).",
            "Source: NIST DLMF 5.5.4, written with pi/tan rather than cot.",
            "Do not invent physical names.",
        ],
        "catalog": _cat(
            ("G0001", "polygamma(0, z)"),
            ("G0002", "polygamma(0, 1 - z)"),
            ("G0003", "pi/tan(pi*z)"),
            ("G0004", "polygamma(0, z) - polygamma(0, 1 - z) + pi/tan(pi*z)"),
        ),
    },
    "thermal-05-trigamma-double-pole": {
        "case_id": "thermal-05-trigamma-double-pole",
        "public_id": "T05",
        "split": "DEV",
        "stratum": "CORE_COMPARABLE",
        "cluster_id": "THERMAL_05_TRIGAMMA_SERIES",
        "domain": "thermal",
        "current": "polygamma(1, z) - Sum(1/(k + z)**2, (k, 0, oo))",
        "symbols": [
            {"name": "z", "real": True},
            {"name": "k", "integer": True, "nonnegative": True},
        ],
        "functions": ["polygamma"],
        "assumptions": [
            "z is not a nonpositive integer",
            "k runs over nonnegative integers in the sum",
        ],
        "scientific_context": [
            "Named special function polygamma(1, z) and an infinite sum of squared reciprocals.",
            "Source: NIST DLMF 5.15.1.",
            "Do not invent physical names.",
        ],
        "catalog": _cat(
            ("G0001", "polygamma(1, z)"),
            ("G0002", "Sum(1/(k + z)**2, (k, 0, oo))"),
            ("G0003", "polygamma(1, z) - Sum(1/(k + z)**2, (k, 0, oo))"),
        ),
    },
    "sciml-phi-hermite-01": {
        "case_id": "sciml-phi-hermite-01",
        "public_id": "T06",
        "split": "DEV",
        "stratum": "CORE_COMPARABLE",
        "cluster_id": "SCIML_PHI_EXP_FAMILY",
        "domain": "sciml",
        "current": "(exp(z) - 1)/z",
        "symbols": [{"name": "z", "real": True}],
        "functions": ["exp"],
        "assumptions": [
            "z is complex (entire continuation); the z != 0 quotient form is used for G0002, G0003, G0004",
            "exp is entire on C",
            "each u_k defined below extends to an entire function with u_k(0) = 1/k!",
            "integral parameter theta ranges over the compact interval [0, 1]",
        ],
        "scientific_context": [
            "Exponential-integrator phi family (Hochbruck–Ostermann): u_0(z)=exp(z),",
            "u_k(z)=(u_{k-1}(z)-u_{k-1}(0))/z for z != 0, and u_k(0)=1/k!.",
            "Integral form: u_k(z)=1/(k-1)! * Integral(exp((1-theta)*z)*theta**(k-1), (theta,0,1)) for k>=1.",
            "Do not invent physical names.",
        ],
        "catalog": _cat(
            ("G0001", "exp(z)"),
            ("G0002", "(exp(z) - 1)/z"),
            ("G0003", "(exp(z) - 1 - z)/z**2"),
            ("G0004", "(exp(z) - 1 - z - z**2/2)/z**3"),
            ("G0005", "1"),
            ("G0006", "1/2"),
        ),
    },
}

# Evaluator-only. Never sent to the proposer.
HIDDEN: dict[str, dict] = {
    "mp-resolvent-dd-01": {
        "case_id": "mp-resolvent-dd-01",
        "ladder": "R2",
        "ladder_n": 2,
        "operator_family": "NEWTON_DD",
        "representation_family": [
            "divided_difference",
            "newton_dd",
            "first_newton_dd",
            "difference_quotient",
            "newton",
        ],
        "latent_F": "1/(t - a)",
        "F_variable": "t",
        "nodes": ["lam", "mu"],
        "gold_members": ["G0001", "G0002", "G0003", "G0004"],
        "reconstruction": "G0003 = (F(lam)-F(mu))/(lam-mu); G0004 = -G0003 under lam!=mu, lam!=a, mu!=a",
        "nontrivial": True,
        "tag": "SHALLOW",
        "leak_tokens": ["divided difference", "Newton", "Hermite", "F[z,w]"],
    },
    "ac-r01-resolvent-hilbert-identity": {
        "case_id": "ac-r01-resolvent-hilbert-identity",
        "ladder": "R2",
        "ladder_n": 2,
        "operator_family": "NEWTON_DD",
        "representation_family": [
            "divided_difference",
            "newton_dd",
            "first_newton_dd",
            "difference_quotient",
            "newton",
            "resolvent_identity",
            "hilbert",
        ],
        "latent_F": "1/(a - t)",
        "F_variable": "t",
        "nodes": ["z", "w"],
        "gold_members": ["G0001", "G0002", "G0003", "G0004"],
        "reconstruction": "G0003 = (F(z)-F(w))/(z-w); G0004 = G0003",
        "nontrivial": True,
        "tag": "SHALLOW",
        "leak_tokens": ["divided difference", "Newton", "Hermite"],
    },
    "thermal-01-fermi-im-digamma": {
        "case_id": "thermal-01-fermi-im-digamma",
        "ladder": "R5",
        "ladder_n": 5,
        "operator_family": "OTHER_EXPLICIT",
        "representation_family": [
            "special_function",
            "digamma",
            "polygamma",
            "tanh",
            "dlmf",
        ],
        "latent_F": "polygamma(0, Rational(1,2) + I*y)",
        "F_variable": "y",
        "nodes": [],
        "gold_members": ["G0001", "G0002"],
        "reconstruction": "Im psi(1/2+I y) = (pi/2) tanh(pi y)",
        "nontrivial": True,
        "tag": "NONTRIVIAL",
        "leak_tokens": ["Fermi-Dirac", "Matsubara", "occupation"],
    },
    "thermal-03-digamma-reflection": {
        "case_id": "thermal-03-digamma-reflection",
        "ladder": "R5",
        "ladder_n": 5,
        "operator_family": "RECURRENCE",
        "representation_family": [
            "special_function",
            "reflection",
            "digamma",
            "polygamma",
            "recurrence",
        ],
        "latent_F": "polygamma(0, z)",
        "F_variable": "z",
        "nodes": [],
        "gold_members": ["G0001", "G0002", "G0003"],
        "reconstruction": "psi(z)-psi(1-z)+pi/tan(pi z)=0",
        "nontrivial": True,
        "tag": "NONTRIVIAL",
        "leak_tokens": ["reflection formula", "master"],
    },
    "thermal-05-trigamma-double-pole": {
        "case_id": "thermal-05-trigamma-double-pole",
        "ladder": "R5",
        "ladder_n": 5,
        "operator_family": "RECURRENCE",
        "representation_family": [
            "special_function",
            "series",
            "trigamma",
            "polygamma",
            "hurwitz",
        ],
        "latent_F": "polygamma(1, z)",
        "F_variable": "z",
        "nodes": [],
        "gold_members": ["G0001", "G0002"],
        "reconstruction": "polygamma(1,z)=Sum 1/(z+k)**2",
        "nontrivial": False,
        "tag": "SHALLOW",
        "leak_tokens": ["Hurwitz", "Hermite", "Matsubara"],
        "note": "Defining series: restating G0001=G0002 is SHALLOW_REPACKAGING, not AI_UNIQUE.",
    },
    "sciml-phi-hermite-01": {
        "case_id": "sciml-phi-hermite-01",
        "ladder": "R3",
        "ladder_n": 3,
        "operator_family": "HERMITE_DD",
        "representation_family": [
            "hermite_dd",
            "divided_difference",
            "newton_dd",
            "repeated_node",
            "confluent",
            "phi",
        ],
        "latent_F": "exp(t)",
        "F_variable": "t",
        "nodes": ["0", "z"],
        "gold_members": ["G0001", "G0002", "G0003", "G0004"],
        "reconstruction": "u_k(z)=exp[0^{(k)}, z]; u_1=(exp(z)-1)/z=exp[0,z]",
        "nontrivial": True,
        "tag": "NONTRIVIAL",
        "leak_tokens": ["Hermite", "divided difference", "Genocchi"],
    },
}

R_LEVEL = {
    "R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4,
    "R5": 5, "R6": 6, "R7": 7, "R8": 8,
}
