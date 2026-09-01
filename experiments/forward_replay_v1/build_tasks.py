#!/usr/bin/env python3
"""Build frozen tasks and masked context packages. Run once before proposers."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
HIDDEN = ROOT / "hidden"
CTX = ROOT / "contexts"
CTX.mkdir(exist_ok=True)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_target(name: str) -> str:
    return (HIDDEN / "targets" / name).read_text().strip()


TASKS = [
    {
        "task_id": "FR-01",
        "paper_source": "Guo et al., PRL 136, 206303 (2026), arXiv:2511.16422v2",
        "printed": "(D-59)->(D-60)",
        "edge_id": "D.K1A-regroup",
        "current_file": "K1A_expanded.txt",
        "target_file": "K1A_regrouped.txt",
        "expected_claim_type": "ALGEBRAIC_EQUIVALENCE",
        "verification_route": "python_sympy_exact_v1",
        "role": "recovery",
        "reason": "Direct algebraic regroup of a velocity kernel; Mode A ZERO in the public audit.",
        "allowed_notes": "Regroup the bilinear velocity kernel by factoring the common v1c and v1b channels. Do not invent new physical identities.",
        "allowed_identities": [],
    },
    {
        "task_id": "FR-02",
        "paper_source": "Guo et al., PRL 136, 206303 (2026), arXiv:2511.16422v2",
        "printed": "(D-60)->(D-61)",
        "edge_id": "D.TA-prefactor",
        "current_file": "TA_unreduced.txt",
        "target_file": "TA_reduced.txt",
        "expected_claim_type": "ALGEBRAIC_EQUIVALENCE",
        "verification_route": "python_sympy_exact_v1",
        "role": "recovery",
        "reason": "Prefactor simplification of T_A; local exact algebra.",
        "allowed_notes": "Simplify the overall prefactor (2*e12**2)/(8*e12) and collect the metric-velocity channels.",
        "allowed_identities": [],
    },
    {
        "task_id": "FR-03",
        "paper_source": "Guo et al., PRL 136, 206303 (2026), arXiv:2511.16422v2",
        "printed": "(D-71)->(D-72)",
        "edge_id": "D.C12-regroup",
        "current_file": "C12_expanded.txt",
        "target_file": "C12_regrouped.txt",
        "expected_claim_type": "ALGEBRAIC_EQUIVALENCE",
        "verification_route": "python_sympy_exact_v1",
        "role": "recovery",
        "reason": "Algebraic regroup of the C_{1,2} kernel.",
        "allowed_notes": "Regroup the four velocity-product groups by the common v1 and v2 channels.",
        "allowed_identities": [],
    },
    {
        "task_id": "FR-04",
        "paper_source": "Guo et al., PRL 136, 206303 (2026), arXiv:2511.16422v2",
        "printed": "(D-120)->(D-121)",
        "edge_id": "D.T0T1-regroup",
        "current_file": "T0T1_mixed.txt",
        "target_file": "T0T1_grouped.txt",
        "expected_claim_type": "ALGEBRAIC_EQUIVALENCE",
        "verification_route": "python_sympy_exact_v1",
        "role": "recovery",
        "reason": "Local regroup of T0+T1 after the IBP surface term is already local.",
        "allowed_notes": "Collect the 1/e12 prefactor and the (f1p, f2p) channels. No integration.",
        "allowed_identities": [],
    },
    {
        "task_id": "FR-05",
        "paper_source": "Guo et al., PRL 136, 206303 (2026), arXiv:2511.16422v2",
        "printed": "(D-74)",
        "edge_id": "D.A-antisym",
        "current_file": "A_pair.txt",
        "target_file": "A_pair_swapped.txt",
        "expected_claim_type": "ALGEBRAIC_EQUIVALENCE",
        "verification_route": "python_sympy_exact_v1",
        "role": "recovery",
        "reason": "Antisymmetric pair identity on Berry-connection products.",
        "allowed_notes": "Rewrite the A-pair using antisymmetry in the (12,21) band labels.",
        "allowed_identities": [],
    },
    {
        "task_id": "FR-06",
        "paper_source": "Guo et al., PRL 136, 206303 (2026), arXiv:2511.16422v2",
        "printed": "(D-66)->(D-67)",
        "edge_id": "D.TBgeo-eps21",
        "current_file": "TBgeo_e12.txt",
        "target_file": "TBgeo_e21.txt",
        "expected_claim_type": "ALGEBRAIC_EQUIVALENCE",
        "verification_route": "python_sympy_exact_v1",
        "role": "recovery",
        "reason": "Substitution-conditioned algebra: e21=-e12 is allowed context, not the target formula.",
        "allowed_notes": "Rewrite T_B,geo so the second band carries e21. You MAY use the declared identity e21 = -e12. You may not invent other band identities.",
        "allowed_identities": ["e21 = -e12"],
    },
    {
        "task_id": "FR-07",
        "paper_source": "Guo et al., PRL 136, 206303 (2026), arXiv:2511.16422v2",
        "printed": "(D-122)+(D-124)->(D-125)",
        "edge_id": "D.geo-T2-subst",
        "current_file": "geo_T2_plus_T0T1.txt",
        "target_file": "geo_fnp_subst.txt",
        "expected_claim_type": "ALGEBRAIC_EQUIVALENCE",
        "verification_route": "python_sympy_exact_v1",
        "role": "recovery",
        "reason": "Distribute f1p/f2p through the T0+T1+T2 combination.",
        "allowed_notes": "Distribute the common dagbc term onto f1p and f2p and keep the 1/e12 channel.",
        "allowed_identities": [],
    },
    {
        "task_id": "FR-08",
        "paper_source": "Guo et al., PRL 136, 206303 (2026), arXiv:2511.16422v2",
        "printed": "(D-126)->(D-127)",
        "edge_id": "D.compact-nbar",
        "current_file": "geo_eps21.txt",
        "target_file": "geo_nbar.txt",
        "expected_claim_type": "INDEX_RELABELING",
        "verification_route": "python_sympy_exact_v1",
        "role": "recovery",
        "reason": "Compact rewrite after the paper convention f_n' = 2 f_0,n'.",
        "allowed_notes": "You MAY use the declared convention f1p = 2*f01p and f2p = 2*f02p. Rewrite in the n-bar / f0 basis.",
        "allowed_identities": ["f1p = 2*f01p", "f2p = 2*f02p"],
    },
    {
        "task_id": "FR-NC-01",
        "paper_source": "Guo et al., PRL 136, 206303 (2026), arXiv:2511.16422v2",
        "printed": "(D-57) remainder control",
        "edge_id": "D.gamma-asymptotic",
        "current_file": "K1A_expanded.txt",
        "target_file": "zero.txt",
        "expected_claim_type": "ASYMPTOTIC_CLAIM",
        "verification_route": "python_sympy_exact_v1",
        "role": "negative_control",
        "reason": "Unsupported remainder-style collapse to 0 must not promote. Target 0 is NOT a recovery target; gold control is omitted.",
        "allowed_notes": "Do not treat a remainder as exact zero. If you propose 0, the evidence layer must refuse promotion.",
        "allowed_identities": [],
    },
]

MS_STEPS = [
    {"step": 0, "task_id": "FR-01"},
    {"step": 1, "task_id": "FR-02"},
    {"step": 2, "task_id": "FR-03"},
]


def write_context(task: dict) -> dict:
    tid = task["task_id"]
    d = CTX / tid
    d.mkdir(exist_ok=True)
    current = read_target(task["current_file"])
    (d / "current.txt").write_text(current + "\n")
    ident = "\n".join(f"- `{x}`" for x in task["allowed_identities"]) or "- none"
    notes = f"""# Masked forward task {tid}

Scientific objective: propose the next algebraic form of the current expression.

Allowed declared identities:
{ident}

Instruction:
{task['allowed_notes']}

Constraints:
- Output K=4 candidate next expressions in the same symbol alphabet.
- Do not use integrals, limits, or undeclared positivity.
- Do not consult the published paper, arXiv source, or evidence tables.
- The next published formula is hidden.

Current expression:
See current.txt
"""
    (d / "notes.md").write_text(notes)
    (d / "objective.txt").write_text(
        "Propose candidate next transformations of current.txt under the allowed identities.\n"
    )
    meta = {
        "task_id": tid,
        "role": task["role"],
        "expected_claim_type": task["expected_claim_type"],
        "printed": task["printed"],
        "current_sha256": sha(d / "current.txt"),
        "notes_sha256": sha(d / "notes.md"),
    }
    (d / "context_meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def main() -> None:
    frozen = {
        "schema_version": "ForwardReplayTaskSetV1",
        "product_tag": "derivation-audit-v0.2.1-alpha",
        "product_commit": "783ec64c0bb4ffd0b4b6ad33f33ead96dba49087",
        "evidence_commit": "69ad474a43ebea55cb2e524934d982e518db026b",
        "paper": "Guo et al., Phys. Rev. Lett. 136, 206303 (2026), arXiv:2511.16422v2",
        "n_recovery_tasks": sum(1 for t in TASKS if t["role"] == "recovery"),
        "n_negative_controls": sum(1 for t in TASKS if t["role"] == "negative_control"),
        "multi_step": {
            "rollout_id": "MS-01",
            "description": "Three public Guo algebraic steps as a forward session (K1A regroup, TA prefactor, C12 regroup). Intermediate paper steps between these printed numbers exist; the session tests promote/refuse, not paper adjacency.",
            "steps": MS_STEPS,
        },
        "tasks": [],
    }
    for task in TASKS:
        meta = write_context(task)
        hidden_target = HIDDEN / "targets" / task["target_file"]
        entry = {
            "task_id": task["task_id"],
            "paper_source": task["paper_source"],
            "printed_equation_source": task["printed"],
            "public_edge_id": task["edge_id"],
            "current_state_file": task["current_file"],
            "hidden_target_file": task["target_file"],
            "hidden_target_sha256": sha(hidden_target),
            "allowed_context": ["contexts/" + task["task_id"] + "/"],
            "excluded_context": [
                "hidden/targets/" + task["target_file"],
                "examples/real_papers/",
                "reports/",
                "VALIDATION_REPORT.md",
                "TABLE_EVIDENCE.md",
            ],
            "expected_claim_type": task["expected_claim_type"],
            "verification_route": task["verification_route"],
            "role": task["role"],
            "reason_for_selection": task["reason"],
            "allowed_identities": task["allowed_identities"],
            "context_sha256": meta["current_sha256"],
        }
        frozen["tasks"].append(entry)
    out = ROOT / "TASKS_FROZEN.yaml"
    out.write_text(yaml.safe_dump(frozen, sort_keys=False))
    print(f"wrote {out} n={len(frozen['tasks'])}")


if __name__ == "__main__":
    main()
