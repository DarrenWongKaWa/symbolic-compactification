"""Can frozen assumptions prove the 14 z0 avoid polygamma poles?"""
from __future__ import annotations

import json
from pathlib import Path

import sympy
from sympy.assumptions import assuming, Q, ask

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ATOMS = ROOT / "research" / "remainder_certification" / "FROZEN_G0016_ATOMS.json"
OUT = HERE / "DERIVATION.json"

_PARSE = {
    "I": sympy.I,
    "pi": sympy.pi,
    "beta": sympy.Symbol("beta", real=True),
    "gamma": sympy.Symbol("gamma", real=True),
    "mu": sympy.Symbol("mu", real=True),
    "epsilon": sympy.Function("epsilon"),
    "ell": sympy.Symbol("ell", real=True),
    "n": sympy.Symbol("n", real=True),
    "m": sympy.Symbol("m", real=True),
}


def _expr(text: str) -> sympy.Expr:
    return sympy.sympify(text, locals=_PARSE)


def _unique_z0(rows: list[dict]) -> list[str]:
    seen: list[str] = []
    for row in rows:
        z = row.get("z0") or ""
        if z and z not in seen:
            seen.append(z)
    return seen


def run() -> dict:
    blob = json.loads(ATOMS.read_text())
    rows = blob.get("rows") or []
    z0s = [_expr(z) for z in _unique_z0(rows)]
    beta, gamma, mu = _PARSE["beta"], _PARSE["gamma"], _PARSE["mu"]
    n = _PARSE["n"]
    eps_n = _PARSE["epsilon"](n)

    frozen_proofs = []
    for z0 in z0s:
        re_z = sympy.simplify(sympy.re(z0))
        im_z = sympy.simplify(sympy.im(z0))
        frozen_proofs.append({
            "z0": str(z0),
            "re": str(re_z),
            "im": str(im_z),
            "ask_re_positive": ask(Q.positive(re_z)),
            "ask_im_nonzero": ask(Q.nonzero(im_z)),
            "ask_not_zero": ask(Q.nonzero(z0)),
        })

    # Concrete pole on the frozen real line: Re = 0, Im = 0.
    witness = {
        "beta": 1,
        "gamma": str(-sympy.pi),
        "mu": 0,
        "epsilon(n)": 0,
        "z0_at_n_plus": str(sympy.simplify(_expr(
            "beta*gamma/(2*pi) + I*beta*mu/(2*pi) - I*beta*epsilon(n)/(2*pi) + 1/2"
        ).subs({beta: 1, gamma: -sympy.pi, mu: 0, eps_n: 0}))),
        "is_polygamma_pole": True,
        "note": "z0=0 in Z_<=0. Frozen real-only assumptions allow this point.",
    }

    pos_proofs = []
    with assuming(Q.positive(beta), Q.positive(gamma)):
        for z0 in z0s:
            re_z = sympy.simplify(sympy.re(z0))
            pos_proofs.append({
                "z0": str(z0),
                "re": str(re_z),
                "ask_re_positive": ask(Q.positive(re_z)),
                "blocked_by_complex_epsilon": "im(epsilon(" in str(re_z),
            })

    def _real_eps(expr: sympy.Expr) -> sympy.Expr:
        reps = {}
        for fn in expr.atoms(sympy.Function):
            if str(fn.func) != "epsilon":
                continue
            key = ",".join(str(a) for a in fn.args)
            reps[fn] = sympy.Symbol(f"eps_{key}", real=True)
        return expr.xreplace(reps)

    # Counterfactual: epsilon real-valued AND beta>0, gamma>0.
    # Not frozen. Then Re(z0) = 1/2 + beta*gamma/(2*pi) > 1/2.
    eps_real_pos = []
    with assuming(Q.positive(beta), Q.positive(gamma)):
        for z0 in z0s:
            z_r = _real_eps(z0)
            re_z = sympy.simplify(sympy.expand(sympy.re(z_r)))
            extra = sympy.simplify(re_z - sympy.Rational(1, 2))
            target = beta * gamma / (2 * sympy.pi)
            extra_ok = extra == target or sympy.expand(extra - target) == 0
            re_pos = extra_ok  # extra>=0 under beta>0,gamma>0
            eps_real_pos.append({
                "z0": str(z0),
                "re_if_epsilon_real": str(re_z),
                "extra_re": str(extra),
                "extra_is_beta_gamma_over_2pi": extra_ok,
                "re_gt_half_under_positive_beta_gamma": extra_ok,
            })

    # Minimal sufficient inequality: beta*gamma > -pi => Re > 0.
    re_template = sympy.Rational(1, 2) + beta * gamma / (2 * sympy.pi)
    with assuming(Q.gt(beta * gamma, -sympy.pi), Q.real(beta), Q.real(gamma)):
        min_re_pos = ask(Q.positive(re_template))

    n_atoms = len(rows)
    derived_from_frozen = all(
        p["ask_re_positive"] is True or p["ask_im_nonzero"] is True
        for p in frozen_proofs
    )
    derived_from_beta_gamma_positive = all(
        p["ask_re_positive"] is True for p in pos_proofs
    )
    derived_from_positive_and_real_epsilon = all(
        p["re_gt_half_under_positive_beta_gamma"] for p in eps_real_pos
    )

    report = {
        "n_atoms": n_atoms,
        "n_unique_z0": len(z0s),
        "unique_z0": [str(z) for z in z0s],
        "frozen_real_only": frozen_proofs,
        "derived_from_frozen_assumptions": derived_from_frozen,
        "pole_witness_under_frozen_reals": witness,
        "if_beta_and_gamma_positive": pos_proofs,
        "derived_if_beta_and_gamma_positive": derived_from_beta_gamma_positive,
        "if_beta_gamma_positive_and_epsilon_real": eps_real_pos,
        "derived_if_beta_gamma_positive_and_epsilon_real": derived_from_positive_and_real_epsilon,
        "minimal_sufficient_predicate": "beta*gamma > -pi  (equivalently Re(z0)>0), or Im(z0)!=0",
        "strong_sufficient_predicate": "beta>0 and gamma>0  (Re(z0)=1/2+beta*gamma/(2*pi)>1/2)",
        "gamma_zero_is_not_a_pole": "gamma=0 => z0=1/2 or 1/2+i..., never in Z_<=0",
        "verdict": "TRULY_ADDITIONAL" if not derived_from_frozen else "DERIVED",
        "no_llm": True,
    }
    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n")
    return report


if __name__ == "__main__":
    r = run()
    print(json.dumps({
        "derived_from_frozen": r["derived_from_frozen_assumptions"],
        "witness_z0": r["pole_witness_under_frozen_reals"]["z0_at_n_plus"],
        "derived_if_positive": r["derived_if_beta_and_gamma_positive"],
        "verdict": r["verdict"],
    }, indent=2))
