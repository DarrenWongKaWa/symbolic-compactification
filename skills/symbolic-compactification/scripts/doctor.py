#!/usr/bin/env python3
"""Environment self-check for the portable skill.

full_verification  — engine importable and identity/counterexample pass
reconstruction_only — scripts run, but machine Exact is illegal
broken              — stop; do not emit a success report
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def _probe() -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "mode": "broken",
        "engine": None,
        "self_check": {},
        "notes": [],
    }
    try:
        import symbolic_compactification
        from symbolic_compactification.models import ENGINE_VERSION, PACKAGE_VERSION
        from symbolic_compactification.verifier import verify_equivalent
    except ImportError as exc:
        report["mode"] = "reconstruction_only"
        report["notes"].append(
            f"engine not importable ({exc}). Reconstruction is allowed; "
            "machine Exact is not."
        )
        return report

    report["engine"] = {
        "package": getattr(symbolic_compactification, "__version__", PACKAGE_VERSION),
        "engine_version": ENGINE_VERSION,
    }
    identity = verify_equivalent(
        "x**2 + 2*x + 1",
        "(x + 1)**2",
        [{"name": "x", "real": True, "nonzero": False}],
    )
    counter = verify_equivalent(
        "sqrt(x**2)",
        "x",
        [{"name": "x", "real": True, "nonzero": False}],
    )
    report["self_check"] = {
        "identity": identity.verdict,
        "counterexample": counter.verdict,
    }
    if identity.verdict != "ZERO":
        report["notes"].append("identity self-check did not return ZERO")
        report["mode"] = "broken"
        return report
    if counter.verdict == "ZERO":
        report["notes"].append(
            "sqrt(x**2)=x over the reals returned ZERO; engine self-check failed"
        )
        report["mode"] = "broken"
        return report
    report["mode"] = "full_verification"
    report["notes"].append(
        "Engine present. Propose candidates; only this doctor/engine path may issue Exact."
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = _probe()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("mode:", report["mode"])
        print("python:", report["python"])
        if report.get("engine"):
            print("engine:", report["engine"])
        if report.get("self_check"):
            print("self_check:", report["self_check"])
        for note in report["notes"]:
            print("-", note)
    if report["mode"] == "full_verification":
        return 0
    if report["mode"] == "reconstruction_only":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
