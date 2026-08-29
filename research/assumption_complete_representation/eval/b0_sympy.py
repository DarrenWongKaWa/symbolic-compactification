"""B0 frozen SymPy residual on DEV smoke tasks. Not hop ZERO for Guo."""
from __future__ import annotations

import json
from pathlib import Path

import sympy

HERE = Path(__file__).resolve().parents[1]
TASKS = HERE / "benchmark" / "dev_smoke" / "tasks.json"
OUT = HERE / "benchmark" / "dev_smoke" / "B0_RESULTS.json"


def run() -> dict:
    blob = json.loads(TASKS.read_text())
    rows = []
    for task in blob["tasks"]:
        tid = task["id"]
        pt = task["point"]
        if tid == "thermal-01-fermi-im-digamma":
            y = sympy.Integer(pt["y"])
            z = sympy.Rational(1, 2) + sympy.I * y
            residual = sympy.im(sympy.digamma(z)) - (sympy.pi / 2) * sympy.tanh(sympy.pi * y)
            val = complex(residual.evalf(32))
            zero = abs(val) < 1e-12
        elif tid == "thermal-03-digamma-reflection":
            z = sympy.Rational(1, 3)
            residual = (
                sympy.digamma(z)
                - sympy.digamma(1 - z)
                + sympy.pi * sympy.cot(sympy.pi * z)
            )
            val = complex(residual.evalf(32))
            zero = abs(val) < 1e-12
        elif tid == "sciml-phi-hermite-01":
            z = sympy.Integer(pt["z"])
            residual = z * ((sympy.exp(z) - 1) / z) - (sympy.exp(z) - 1)
            val = complex(sympy.simplify(residual).evalf(32))
            zero = residual == 0 or abs(val) < 1e-15
        elif tid == "mp-resolvent-dd-01":
            lam, mu, a = (sympy.Integer(pt[k]) for k in ("lam", "mu", "a"))
            residual = (1 / (lam - a) - 1 / (mu - a)) / (lam - mu) + 1 / (
                (lam - a) * (mu - a)
            )
            val = complex(sympy.simplify(residual))
            zero = residual == 0 or abs(val) < 1e-15
        else:
            val, zero = None, False
        rows.append(
            {
                "id": tid,
                "b0_zero": zero,
                "value": str(val),
                "baseline": "B0_sympy",
                "discovers_representation": False,
            }
        )
    report = {
        "n": len(rows),
        "n_zero": sum(1 for r in rows if r["b0_zero"]),
        "ai_unique_success": 0,
        "guo": False,
        "rows": rows,
        "note": "B0 residual ZERO is not representation discovery.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
