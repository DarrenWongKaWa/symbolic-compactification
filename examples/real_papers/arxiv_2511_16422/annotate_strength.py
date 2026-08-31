#!/usr/bin/env python3
"""Annotate machine TABLE_VERIFIED with researcher-declared strength.

Cannot create ZERO. Inclusion is copied from reports/verification_table.json
rows that already have table=TABLE_VERIFIED and result=ZERO.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STRENGTH_PATH = ROOT / "verification_strength.yaml"
TABLE_JSON = ROOT / "reports" / "verification_table.json"
OUT_MD = ROOT / "reports" / "TABLE_VERIFIED_STRENGTH.md"
PACKAGE_MD = ROOT / "reviewer-verification-package" / "TABLE_VERIFIED_STRENGTH.md"


def _load_yaml(path: Path) -> dict:
    try:
        import yaml  # type: ignore
    except ImportError:
        sys.exit("PyYAML is required (comes with symbolic-compactification)")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def main() -> int:
    overlay = _load_yaml(STRENGTH_PATH)
    if overlay.get("cannot_create_zero") is not True:
        print("strength overlay must set cannot_create_zero: true", file=sys.stderr)
        return 2
    if not TABLE_JSON.is_file():
        print(f"missing {TABLE_JSON}; run `ssc audit table` first", file=sys.stderr)
        return 2
    payload = json.loads(TABLE_JSON.read_text(encoding="utf-8"))
    verified = [
        row for row in payload.get("rows", [])
        if row.get("table") == "TABLE_VERIFIED"
        and row.get("result") == "ZERO"
        and row.get("status") == "ZERO"
        and row.get("may_appear_in_verified_table") is True
    ]
    direct = dict(overlay.get("direct_exact") or {})
    subst = dict(overlay.get("substitution_exact") or {})
    overlap = set(direct) & set(subst)
    if overlap:
        print(f"edge in both strength buckets: {sorted(overlap)}", file=sys.stderr)
        return 2
    declared = {**{k: ("DIRECT_EXACT", v) for k, v in direct.items()},
                **{k: ("SUBSTITUTION_EXACT", v) for k, v in subst.items()}}
    verified_ids = [row["edge_id"] for row in verified]
    missing = [eid for eid in verified_ids if eid not in declared]
    extra = sorted(set(declared) - set(verified_ids))
    if missing:
        print("verified ZERO edges missing strength: " + ", ".join(missing),
              file=sys.stderr)
        return 2
    if extra:
        print("strength overlay lists non-verified edges: " + ", ".join(extra),
              file=sys.stderr)
        return 2

    by_id = {row["edge_id"]: row for row in verified}
    n_direct = sum(1 for eid in verified_ids if declared[eid][0] == "DIRECT_EXACT")
    n_subst = sum(1 for eid in verified_ids if declared[eid][0] == "SUBSTITUTION_EXACT")

    lines = [
        "# Machine-verified identities (with verification strength)",
        "",
        "Generated from `reports/verification_table.json` plus",
        "`verification_strength.yaml`. This file **cannot create ZERO**.",
        "A row appears here only if the machine table already lists it as",
        "integrity-PASS engine ZERO.",
        "",
        f"**{len(verified_ids)} machine ZERO** = "
        f"**{n_direct} DIRECT_EXACT** + **{n_subst} SUBSTITUTION_EXACT**.",
        "",
        "18 executable equation-level identities were machine-verified as "
        "exact ZERO under the declared symbolic semantics. One asymptotic "
        "remainder claim remained UNKNOWN, and two global "
        "integration-by-parts steps remained NOT_LOWERED.",
        "",
        "## Strength legend",
        "",
        "| Strength | Meaning |",
        "| --- | --- |",
        "| `DIRECT_EXACT` | The displayed residual is an unsubstituted local identity. |",
        "| `SUBSTITUTION_EXACT` | Exact *given* a declared upstream identity written into the residual. Does not independently prove that identity. |",
        "| `CERTIFIED_BY_CHILDREN` | Split parent (never a ZERO row; none in this verified table). |",
        "",
        "`SUBSTITUTION_EXACT` means: given the declared upstream identity, "
        "the downstream transformation is exact. It does **not** mean the "
        "tool independently proved $\\epsilon_{21}=-\\epsilon_{12}$, "
        "$\\Omega_2=-\\Omega_1$, $f'=2f_0'$, or the metric-velocity theorem.",
        "",
        "## DIRECT_EXACT",
        "",
        "| Paper equation(s) | Transformation | Type | Strength | Result | Evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for eid in sorted(verified_ids):
        kind, meta = declared[eid]
        if kind != "DIRECT_EXACT":
            continue
        row = by_id[eid]
        lines.append(
            "| {eqs} | {claim} | `{typ}` | `{kind}` | `{res}` | `{art}` |".format(
                eqs=_cell(meta.get("paper_eqs") or eid),
                claim=_cell(row.get("claim") or ""),
                typ=row.get("edge_type") or "",
                kind=kind,
                res=row.get("result") or "",
                art=row.get("artifact_relpath") or "",
            )
        )
    lines.extend([
        "",
        "## SUBSTITUTION_EXACT",
        "",
        "| Paper equation(s) | Transformation | Substituted identity | Type | Strength | Result | Evidence |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ])
    for eid in sorted(verified_ids):
        kind, meta = declared[eid]
        if kind != "SUBSTITUTION_EXACT":
            continue
        row = by_id[eid]
        lines.append(
            "| {eqs} | {claim} | {sub} | `{typ}` | `{kind}` | `{res}` | `{art}` |".format(
                eqs=_cell(meta.get("paper_eqs") or eid),
                claim=_cell(row.get("claim") or ""),
                sub=_cell(meta.get("substitution") or ""),
                typ=row.get("edge_type") or "",
                kind=kind,
                res=row.get("result") or "",
                art=row.get("artifact_relpath") or "",
            )
        )
    lines.extend([
        "",
        "## Outside this table (soundness, not failure)",
        "",
        "See `TABLE_UNCERTIFIED.md`:",
        "",
        "- Eq. (D-57) full $\\Gamma$ expansion: `ASYMPTOTIC_CLAIM` / `UNKNOWN`",
        "- Eq. (D-114) → (D-119) global BZ IBP: `INTEGRAL_ARGUMENT` / `NOT_LOWERED`",
        "- Eq. (D-123) → (D-124) global BZ IBP: `INTEGRAL_ARGUMENT` / `NOT_LOWERED`",
        "",
        "The machine-authoritative residual table remains `TABLE_VERIFIED.md`.",
        "",
    ])
    text = "\n".join(lines)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(text, encoding="utf-8")
    if PACKAGE_MD.parent.is_dir():
        PACKAGE_MD.write_text(text, encoding="utf-8")
    ibp_rows = [
        row for row in payload.get("rows", [])
        if row.get("edge_type") == "BZ_PERIODIC_INTEGRATION_BY_PARTS"
    ]
    ibp_path = ROOT / "reports" / "TABLE_IBP.md"
    ibp_lines = [
        "# Brillouin-zone integration by parts",
        "",
        "These parents are **not** engine ZERO. SymPy did not evaluate a BZ integral.",
        "Certificate = local Leibniz `ZERO` + declared `BZ_TORUS_PERIODICITY` on",
        "`BRILLOUIN_ZONE_TORUS`. Missing periodicity would be `ASSUMPTION_REQUIRED`.",
        "",
        "| Paper step | Local identity | Global rule | Assumptions | Status |",
        "| --- | --- | --- | --- | --- |",
    ]
    paper = {
        "D.T0-ibp-global": "Eq. (D-114) → Eq. (D-119)",
        "D.T2-ibp-global": "Eq. (D-123) → Eq. (D-124)",
    }
    for row in sorted(ibp_rows, key=lambda item: item.get("edge_id") or ""):
        ibp_lines.append(
            "| {paper} | `D.leibniz-product-rule` ZERO | BZ periodic IBP | "
            "periodic smooth gauge-invariant integrand on BZ torus | `{status}` |".format(
                paper=paper.get(row.get("edge_id") or "", row.get("edge_id") or ""),
                status=row.get("status") or "",
            )
        )
    ibp_lines.append("")
    ibp_text = "\n".join(ibp_lines)
    ibp_path.write_text(ibp_text, encoding="utf-8")
    pkg_ibp = ROOT / "reviewer-verification-package" / "TABLE_IBP.md"
    if pkg_ibp.parent.is_dir():
        pkg_ibp.write_text(ibp_text, encoding="utf-8")
    print(f"wrote {OUT_MD.relative_to(ROOT)} ({n_direct} DIRECT_EXACT, {n_subst} SUBSTITUTION_EXACT)")
    print(f"wrote {ibp_path.relative_to(ROOT)} ({len(ibp_rows)} IBP parents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
