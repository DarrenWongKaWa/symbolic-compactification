"""CSV/MD summaries. No secrets."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "RESULTS_DEV.csv"
COST_PATH = HERE / "TOKEN_COSTS.csv"

COLUMNS = [
    "stage", "item_id", "category", "polarity", "condition", "seed", "model",
    "parse_status", "n_hypotheses", "type_hit", "targeting_hit", "certified",
    "abstain", "unnecessary", "quality", "success", "false_abstraction",
    "representation_change", "d_attempted", "d_certified",
    "n_zero", "n_nonzero", "n_unknown",
    "prompt_tokens", "completion_tokens", "reasoning_tokens", "latency_s",
    "error",
]

# Off-peak list prices (USD / 1M tokens), for bookkeeping only.
PRICE = {
    "deepseek-v4-pro": {"in": 0.66, "out": 1.98},
    "deepseek-v4-flash": {"in": 0.22, "out": 0.66},
}


def _row(rec: dict) -> dict:
    ev = rec.get("eval") or {}
    usage = rec.get("usage") or {}
    return {
        "stage": rec.get("stage"),
        "item_id": rec.get("item_id") or ev.get("id"),
        "category": rec.get("category") or ev.get("category"),
        "polarity": rec.get("polarity") or ev.get("polarity"),
        "condition": rec.get("condition"),
        "seed": rec.get("seed"),
        "model": rec.get("model"),
        "parse_status": rec.get("parse_status") or ev.get("parse_status"),
        "n_hypotheses": rec.get("n_hypotheses") if rec.get("n_hypotheses") is not None else ev.get("n_hypotheses"),
        "type_hit": ev.get("type_hit"),
        "targeting_hit": ev.get("targeting_hit"),
        "certified": ev.get("certified"),
        "abstain": ev.get("abstain"),
        "unnecessary": ev.get("unnecessary"),
        "quality": ev.get("quality"),
        "success": ev.get("success"),
        "false_abstraction": ev.get("false_abstraction"),
        "representation_change": ev.get("representation_change"),
        "d_attempted": "|".join(ev.get("d_attempted") or []),
        "d_certified": "|".join(ev.get("d_certified") or []),
        "n_zero": ev.get("n_zero"),
        "n_nonzero": ev.get("n_nonzero"),
        "n_unknown": ev.get("n_unknown"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "reasoning_tokens": usage.get("reasoning_tokens"),
        "latency_s": rec.get("latency_s"),
        "error": rec.get("error"),
    }


def append_row(rec: dict, path: Path = CSV_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.is_file()
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if new:
            w.writeheader()
        w.writerow(_row(rec))


def load_csv(path: Path = CSV_PATH) -> list[dict]:
    if not path.is_file():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def _truth(v) -> bool:
    return str(v).lower() in {"1", "true", "yes"}


def summarize(rows: Iterable[dict], *, condition: str | None = None) -> dict[str, Any]:
    rows = [r for r in rows if r]
    if condition:
        rows = [r for r in rows if r.get("condition") == condition]
    n = len(rows) or 1
    def rate(pred):
        return round(sum(1 for r in rows if pred(r)) / n, 4)
    pt = sum(int(r["prompt_tokens"] or 0) for r in rows)
    ct = sum(int(r["completion_tokens"] or 0) for r in rows)
    rt = sum(int(r["reasoning_tokens"] or 0) for r in rows)
    model = (list(rows)[0].get("model") if rows else "") or "deepseek-v4-pro"
    price = PRICE.get(model, PRICE["deepseek-v4-pro"])
    usd = (pt / 1e6) * price["in"] + (ct / 1e6) * price["out"]
    return {
        "n": len(rows) if rows else 0,
        "correct_hypothesis_rate": rate(lambda r: _truth(r.get("type_hit")) and _truth(r.get("targeting_hit"))),
        "certified_rate": rate(lambda r: _truth(r.get("certified"))),
        "success_rate": rate(lambda r: _truth(r.get("success"))),
        "false_abstraction_rate": rate(lambda r: _truth(r.get("false_abstraction"))),
        "abstention_rate": rate(lambda r: _truth(r.get("abstain"))),
        "parse_failure_rate": rate(lambda r: r.get("parse_status") == "PARSE_FAILURE"),
        "unnecessary_rate": rate(lambda r: _truth(r.get("unnecessary"))),
        "representation_change_rate": rate(lambda r: _truth(r.get("representation_change"))),
        "nonzero_rate": rate(lambda r: int(r.get("n_nonzero") or 0) > 0),
        "unknown_rate": rate(lambda r: int(r.get("n_unknown") or 0) > 0),
        "prompt_tokens": pt,
        "completion_tokens": ct,
        "reasoning_tokens": rt,
        "est_usd_offpeak": round(usd, 4),
    }


def decision_case(raw: dict, sol: dict) -> tuple[str, str]:
    """Compare RAW (A0/L0) vs SOL (A2/L2) summaries."""
    r_ok = raw.get("correct_hypothesis_rate") or 0
    s_ok = sol.get("correct_hypothesis_rate") or 0
    r_cert = raw.get("certified_rate") or 0
    s_cert = sol.get("certified_rate") or 0
    r_rep = raw.get("representation_change_rate") or 0
    s_rep = sol.get("representation_change_rate") or 0
    if abs(s_ok - r_ok) < 0.08 and abs(s_cert - r_cert) < 0.08:
        return "A", "RAW ≈ SOL on correct/certified rates"
    if s_rep + 0.05 < r_rep and s_ok >= r_ok:
        return "D", "SOL helps local structure but reduces representation-change proposals (anchoring)"
    if s_rep > r_rep + 0.1 and s_ok > r_ok:
        return "C", "SOL improves representation-change tasks"
    if s_ok > r_ok + 0.1 and s_cert <= r_cert + 0.05:
        return "B", "SOL helps type/targeting more than certification (D3/D4 local)"
    if (raw.get("correct_hypothesis_rate") or 0) > 0.3 and (raw.get("certified_rate") or 0) < 0.05:
        return "E", "hypotheses exist but constructor/verifier cannot certify"
    if r_ok < 0.1 and s_ok < 0.1:
        return "F", "both RAW and SOL fail on hard abstraction"
    if s_ok > r_ok:
        return "B", "SOL > RAW on hypothesis quality, limited certified gain"
    return "A", "no material SOL advantage"


def write_token_costs(rows: list[dict]) -> None:
    COST_PATH.parent.mkdir(parents=True, exist_ok=True)
    fields = ["model", "condition", "prompt_tokens", "completion_tokens",
              "reasoning_tokens", "est_usd_offpeak", "n"]
    by = defaultdict(list)
    for r in rows:
        by[(r.get("model"), r.get("condition"))].append(r)
    with COST_PATH.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for (model, cond), rs in sorted(by.items()):
            s = summarize(rs)
            w.writerow({
                "model": model, "condition": cond, "n": s["n"],
                "prompt_tokens": s["prompt_tokens"],
                "completion_tokens": s["completion_tokens"],
                "reasoning_tokens": s["reasoning_tokens"],
                "est_usd_offpeak": s["est_usd_offpeak"],
            })
