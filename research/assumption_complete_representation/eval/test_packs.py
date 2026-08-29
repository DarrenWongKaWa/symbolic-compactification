"""Held-out TEST packs. Frozen after DEV_METHOD_SELECTION. No prompt retune."""
from __future__ import annotations

HEADLINE = [
    "mp-kato-simple-ev-01",
    "mp-parlett-schur-01",
    "sciml-tweedie-gauss-01",
    "sciml-ou-mehler-01",
    "sciml-deq-ift-01",
    "sciml-adjoint-linear-01",
    "ac-t-weyl-su2-char",
    "ac-t-ricci-weyl",
    "ac-t-clebsch-half",
    "ac-t-iso4-projectors",
]

DUPLICATE_CONTROL = [
    "thermal-02-bose-im-digamma",
    "mp-mathias-block-01",
    "thermal-04-coth-matsubara",
]

CHALLENGE = [
    "ac-r02-sokhotski-plemelj-boundary",
    "mp-opitz-dd-01",
    "sciml-lyapunov-kronecker-01",
    "thermal-06-fermi-dirac-polylog",
    "ac-t-pauli-completeness",
]

CORE = [
    "sciml-tweedie-gauss-01",
    "sciml-ou-mehler-01",
    "sciml-deq-ift-01",
    "ac-t-weyl-su2-char",
]

PACKAGING_GAP = [c for c in HEADLINE if c not in CORE]

PUBLIC_ID = {
    "sciml-tweedie-gauss-01": "H01",
    "sciml-ou-mehler-01": "H02",
    "sciml-deq-ift-01": "H03",
    "ac-t-weyl-su2-char": "H04",
}


def _cat(*rows: tuple[str, str]) -> list[dict]:
    out = []
    for i, (gid, text) in enumerate(rows, 1):
        out.append({"source_node_id": gid, "kind": "expr", "text": text})
        assert gid == f"G{i:04d}"
    return out


PUBLIC_PACKS: dict[str, dict] = {
    "sciml-tweedie-gauss-01": {
        "public_id": "H01",
        "split": "TEST",
        "stratum": "CORE_COMPARABLE",
        "cluster_id": "GAUSS_CONJUGATE",
        "domain": "sciml",
        "current": "(tau2*y + sig2*m)/(tau2 + sig2) - (y + sig2*(-(y - m)/(sig2 + tau2)))",
        "symbols": [
            {"name": "y", "real": True},
            {"name": "m", "real": True},
            {"name": "sig2", "real": True, "positive": True},
            {"name": "tau2", "real": True, "positive": True},
        ],
        "functions": [],
        "assumptions": [
            "sig2 > 0",
            "tau2 > 0",
            "sig2 + tau2 != 0",
            "y, m real",
        ],
        "scientific_context": [
            "Three rational expressions in (y, m, sig2, tau2).",
            "Do not invent physical names.",
        ],
        "catalog": _cat(
            ("G0001", "(tau2*y + sig2*m)/(tau2 + sig2)"),
            ("G0002", "-(y - m)/(sig2 + tau2)"),
            ("G0003", "y + sig2*(-(y - m)/(sig2 + tau2))"),
            ("G0004", "(tau2*y + sig2*m)/(tau2 + sig2) - (y + sig2*(-(y - m)/(sig2 + tau2)))"),
        ),
    },
    "sciml-ou-mehler-01": {
        "public_id": "H02",
        "split": "TEST",
        "stratum": "CORE_COMPARABLE",
        "cluster_id": "OU_KERNEL",
        "domain": "sciml",
        "current": "(sigma**2/(2*theta))*exp(-theta*Abs(s - t))",
        "symbols": [
            {"name": "y", "real": True},
            {"name": "t", "real": True},
            {"name": "s", "real": True},
            {"name": "theta", "real": True, "positive": True},
            {"name": "sigma", "real": True, "positive": True},
            {"name": "beta", "real": True, "positive": True},
            {"name": "x0", "real": True},
        ],
        "functions": ["exp", "Abs"],
        "assumptions": [
            "theta > 0",
            "sigma > 0",
            "t > 0 when using the 1-exp(-2*theta*t) member",
            "beta > 0",
        ],
        "scientific_context": [
            "A linear Gaussian SDE family and its covariance.",
            "Do not invent physical names.",
        ],
        "catalog": _cat(
            ("G0001", "y*exp(-theta*t)"),
            ("G0002", "(sigma**2/(2*theta))*(1 - exp(-2*theta*t))"),
            ("G0003", "(sigma**2/(2*theta))*exp(-theta*Abs(s - t))"),
            ("G0004", "x0*exp(-beta*t/2)"),
            ("G0005", "1 - exp(-beta*t)"),
        ),
    },
    "sciml-deq-ift-01": {
        "public_id": "H03",
        "split": "TEST",
        "stratum": "CORE_COMPARABLE",
        "cluster_id": "IFT_SCALAR",
        "domain": "sciml",
        "current": "1/(cosh(w*z + x)**2 - w)",
        "symbols": [
            {"name": "w", "real": True},
            {"name": "z", "real": True},
            {"name": "x", "real": True},
        ],
        "functions": ["tanh", "cosh"],
        "assumptions": [
            "cosh(w*z + x)**2 != w so the displayed reciprocal is defined",
        ],
        "scientific_context": [
            "A scalar implicit map z = tanh(w*z + x) and a reciprocal involving cosh.",
            "Do not invent physical names.",
        ],
        "catalog": _cat(
            ("G0001", "tanh(w*z + x) - z"),
            ("G0002", "1/cosh(w*z + x)**2"),
            ("G0003", "1/(cosh(w*z + x)**2 - w)"),
        ),
    },
    "ac-t-weyl-su2-char": {
        "public_id": "H04",
        "split": "TEST",
        "stratum": "CORE_COMPARABLE",
        "cluster_id": "WEYL_SU2_CHAR",
        "domain": "tensor",
        "current": "(z**(m + 1) - z**(-(m + 1)))/(z - z**(-1))",
        "symbols": [
            {"name": "z", "real": True, "nonzero": True},
            {"name": "m", "integer": True, "nonnegative": True},
            {"name": "k", "integer": True, "nonnegative": True},
            {"name": "theta", "real": True},
        ],
        "functions": ["sin"],
        "assumptions": [
            "z != 0",
            "z**2 != 1",
            "m is a nonnegative integer",
        ],
        "scientific_context": [
            "A finite geometric sum in z, a two-term quotient, and a sine ratio.",
            "Do not invent physical names.",
        ],
        "catalog": _cat(
            ("G0001", "Sum(z**(m - 2*k), (k, 0, m))"),
            ("G0002", "(z**(m + 1) - z**(-(m + 1)))/(z - z**(-1))"),
            ("G0003", "sin((m + 1)*theta)/sin(theta)"),
        ),
    },
}

HIDDEN = {
    "sciml-tweedie-gauss-01": {
        "ladder": "R6",
        "ladder_n": 6,
        "operator_family": "OTHER_EXPLICIT",
        "representation_family": ["master", "score", "tweedie", "posterior"],
        "latent_F": "log of the Gaussian marginal density",
        "gold_members": ["G0001", "G0002", "G0003"],
        "nontrivial": True,
        "tag": "NONTRIVIAL",
        "leak_tokens": ["Tweedie", "MMSE", "score-matching"],
    },
    "sciml-ou-mehler-01": {
        "ladder": "R6",
        "ladder_n": 6,
        "operator_family": "OTHER_EXPLICIT",
        "representation_family": ["master", "mehler", "ou", "kernel"],
        "latent_F": "OU transition kernel",
        "gold_members": ["G0001", "G0002", "G0003"],
        "nontrivial": True,
        "tag": "NONTRIVIAL",
        "leak_tokens": ["Mehler", "Hermite", "Ornstein", "Matern"],
    },
    "sciml-deq-ift-01": {
        "ladder": "R6",
        "ladder_n": 6,
        "operator_family": "FUNCTIONAL_CALCULUS",
        "representation_family": ["master", "ift", "resolvent", "neumann"],
        "latent_F": "(I - D_z f)^{-1}",
        "gold_members": ["G0001", "G0003"],
        "nontrivial": True,
        "tag": "NONTRIVIAL",
        "leak_tokens": ["implicit function theorem", "DEQ"],
    },
    "ac-t-weyl-su2-char": {
        "ladder": "R8",
        "ladder_n": 8,
        "operator_family": "BASIS_RECONSTRUCTION",
        "representation_family": ["weyl", "character", "orbit", "generator", "invariant"],
        "latent_F": "Weyl orbit sum / denominator",
        "gold_members": ["G0001", "G0002"],
        "nontrivial": True,
        "tag": "NONTRIVIAL",
        "leak_tokens": ["Weyl character", "Weyl group"],
    },
}
