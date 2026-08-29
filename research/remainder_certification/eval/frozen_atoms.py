"""Remainder domain query on frozen G0016 atoms. Does not alter atom definitions."""
from __future__ import annotations

import json
from pathlib import Path

import sympy

from research.remainder_certification.affine import AffineNormalization, normalize_affine
from research.remainder_certification.polygamma import classify_polygamma_domain
from research.remainder_certification.schema import CERTIFIED, UNKNOWN

ROOT = Path(__file__).resolve().parents[3]
ATOM_MAP = ROOT / "research" / "coefficient_laurent" / "atoms" / "ATOM_MAP.json"
HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "FROZEN_G0016_ATOMS.json"

def _parse_srepr(text: str) -> sympy.Expr | None:
    ns = dict(sympy.__dict__)
    ns["Function"] = sympy.Function
    ns["Integer"] = sympy.Integer
    ns["Rational"] = sympy.Rational
    ns["Mul"] = sympy.Mul
    ns["Add"] = sympy.Add
    ns["Pow"] = sympy.Pow
    ns["Symbol"] = sympy.Symbol
    try:
        out = eval(text, {"__builtins__": {}}, ns)  # noqa: S307  # ATOM_MAP srepr only
    except Exception:
        return None
    return out if isinstance(out, sympy.Expr) else None


def run() -> dict:
    blob = json.loads(ATOM_MAP.read_text())
    primary = next(h for h in blob["hops"] if h.get("is_primary"))
    t = sympy.Dummy("t")
    eps = sympy.Function("epsilon")
    m = sympy.Symbol("m", real=True)
    n = sympy.Symbol("n", real=True)
    var = eps(m)
    point = eps(n)
    rows = []
    domain_cache: dict = {}
    for atom in primary["atoms"]:
        raw = _parse_srepr(atom["argument"])
        if raw is None:
            rows.append(
                {
                    "atom_id": atom["atom_id"],
                    "verdict": UNKNOWN,
                    "note": "unparsed argument",
                }
            )
            continue
        arg_t = raw.xreplace({var: point + t})
        aff = normalize_affine(arg_t, t)
        if not isinstance(aff, AffineNormalization):
            rows.append(
                {
                    "atom_id": atom["atom_id"],
                    "verdict": UNKNOWN,
                    "note": "affine UNSUPPORTED",
                    "argument": str(raw)[:160],
                }
            )
            continue
        try:
            k = int(sympy.Integer(_parse_srepr(str(atom.get("function_order") or "0")) or 0))
        except Exception:
            k = 0
        # k=0,1,2 share the Z_<=0 pole set; cache on (z0,c).
        cache_key = (str(aff.z0), str(aff.c))
        if cache_key not in domain_cache:
            domain_cache[cache_key] = classify_polygamma_domain(k, aff.z0, aff.c, t)
        report = domain_cache[cache_key]
        rows.append(
            {
                "atom_id": atom["atom_id"],
                "order": str(k),
                "z0": str(aff.z0),
                "c": str(aff.c),
                "verdict": report.verdict,
                "missing": list(report.missing_assumptions),
                "certified": report.verdict == CERTIFIED,
            }
        )
    n_cert = sum(1 for r in rows if r.get("certified"))
    report = {
        "hop_id": primary["hop_id"],
        "n_atoms": len(rows),
        "n_certified": n_cert,
        "n_assumption_required": sum(1 for r in rows if r.get("verdict") == "ASSUMPTION_REQUIRED"),
        "n_unknown": sum(1 for r in rows if r.get("verdict") == UNKNOWN),
        "n_nonanalytic": sum(1 for r in rows if r.get("verdict") == "NONANALYTIC"),
        "all_certified": n_cert == len(rows) and len(rows) == 14,
        "level_c_blocked": True,
        "rows": rows,
        "no_llm": True,
        "atoms_not_modified": True,
    }
    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n")
    return report


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("n_atoms", "n_certified", "n_assumption_required", "n_unknown", "n_nonanalytic", "all_certified", "level_c_blocked")}))
