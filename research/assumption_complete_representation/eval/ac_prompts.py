"""Frozen P0–P4 prompt assembly. No per-task patches."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve().parents[1]
PROMPT_DIR = HERE / "prompts"

COND_FILE = {
    "P0": "P0_RAW.txt",
    "P1": "P1_BASIC.txt",
    "P2": "P2_SOL.txt",
    "P3": "P3_GROUNDED.txt",
    "P4": "P4_DD_HERMITE.txt",
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def load_system() -> str:
    return (PROMPT_DIR / "SYSTEM_V1.txt").read_text()


def load_condition(condition: str) -> str:
    name = COND_FILE[condition.upper()]
    return (PROMPT_DIR / name).read_text()


def render_catalog(entries: list[dict]) -> str:
    lines = [
        "SOURCE CATALOG — cite these source_node_id values only.",
        "IDs are local to this task. Do not invent aliases.",
        "",
    ]
    for e in entries:
        lines.append(f"{e['source_node_id']}  kind={e.get('kind') or 'expr'}")
        lines.append(f"  text: {e['text']}")
    return "\n".join(lines)


def render_basic(summary: dict) -> str:
    keys = (
        "ops", "n_ops", "count_ops", "free_symbols", "functions",
        "n_piecewise", "n_branches", "indexed_names", "n_indexed",
        "n_sums", "raw_chars",
    )
    lines = []
    for k in keys:
        if k in summary:
            lines.append(f"- {k}: {summary[k]}")
    for k, v in summary.items():
        if k in keys:
            continue
        if isinstance(v, (int, float, str, list)) and k != "text":
            lines.append(f"- {k}: {v}")
    return "\n".join(lines) if lines else "(empty)"


def build_user_prompt(
    pack: dict,
    condition: str,
    *,
    basic_summary: Optional[dict] = None,
    sol_text: Optional[str] = None,
) -> str:
    cond = condition.upper()
    extra = load_condition(cond)
    ctx = pack.get("scientific_context") or []
    parts = [
        extra.strip(),
        "",
        f"PUBLIC_TASK_ID: {pack.get('public_id') or 'Txx'}",
        "Do not use an external name for this task.",
        "",
        "DECLARED SYMBOLS:",
        repr([s.get("name") if isinstance(s, dict) else s for s in (pack.get("symbols") or [])]),
        "DECLARED FUNCTIONS:",
        repr(list(pack.get("functions") or [])),
        "ASSUMPTION CONTRACT (use only these; do not add undeclared domains):",
        "\n".join(f"- {a}" for a in (pack.get("assumptions") or [])),
        "",
        "SCIENTIFIC CONTEXT:",
        "\n".join(f"- {c}" for c in ctx) if ctx else "(none)",
        "",
        render_catalog(pack.get("catalog") or []),
        "",
        "SOURCE EXPRESSIONS / CURRENT:",
        pack.get("current") or "",
    ]
    if cond == "P1" and basic_summary:
        parts.extend([
            "",
            "BASIC STRUCTURAL SUMMARY (inventory, not an interpretation):",
            render_basic(basic_summary),
        ])
    if cond == "P2":
        parts.extend([
            "",
            "STRUCTURAL OBSERVATION PACKETS:",
            "These are relations reported by existing symbolic backends.",
            "They are observations, not scientific names, and not proofs.",
            sol_text or "(no packets)",
        ])
    parts.extend(["", "Respond with JSON only."])
    return "\n".join(parts)


def messages_for(
    pack: dict,
    condition: str,
    *,
    basic_summary: Optional[dict] = None,
    sol_text: Optional[str] = None,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    system = load_system()
    user = build_user_prompt(
        pack, condition, basic_summary=basic_summary, sol_text=sol_text,
    )
    msgs = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    hashes = {
        "system_sha256": sha256_text(system),
        "condition_sha256": sha256_text(load_condition(condition.upper())),
        "user_sha256": sha256_text(user),
        "prompt_sha256": sha256_text(system + "\n---\n" + user),
        "input_sha256": sha256_text(json.dumps({
            "public_id": pack.get("public_id"),
            "catalog": pack.get("catalog"),
            "current": pack.get("current"),
            "assumptions": pack.get("assumptions"),
            "condition": condition.upper(),
        }, sort_keys=True)),
    }
    return msgs, hashes
