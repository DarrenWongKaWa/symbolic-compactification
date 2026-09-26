#!/usr/bin/env python3
"""Score every results/arm_*.json against items.yaml and write SUMMARY.md.

Primary question per item: can the claim be used exactly as stated?
  truth TRUE                -> usable
  truth FALSE / CONDITIONAL -> not usable
FALSE and CONDITIONAL overlap by definition (a claim that needs an extra
hypothesis also fails for some admissible values), so the headline metrics
are binary. ABSTAIN (tool only) is neither right nor wrong; it lowers coverage.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ARM_NAMES = {"whiteboard": "Whiteboard agent (reasoning only)",
             "python": "Agent + Python (SymPy/mpmath)",
             "tool": "symbolic-compactification"}


def score(rows: list[dict], items: dict[str, dict]) -> dict:
    by_id = {r["id"]: r for r in rows}
    s = defaultdict(int)
    per_cat = defaultdict(lambda: defaultdict(int))
    wrong = []
    for key, item in items.items():
        truth, answer = item["truth"], by_id.get(key, {}).get("answer", "MISSING")
        cat = per_cat[item["category"]]
        cat["n"] += 1
        if answer in ("ABSTAIN", "MISSING"):
            s["abstain"] += 1
            cat["abstain"] += 1
            if truth == "TRUE":
                s["true_not_confirmed"] += 1
            continue
        s["answered"] += 1
        says_usable, is_usable = answer == "TRUE", truth == "TRUE"
        if says_usable == is_usable:
            s["binary_correct"] += 1
            cat["correct"] += 1
        else:
            wrong.append({"id": key, "truth": truth, "answer": answer,
                          "reason": by_id[key].get("reason") or by_id[key].get("reasons")})
        if says_usable and not is_usable:
            s["false_certification"] += 1
            cat["false_cert"] += 1
        if is_usable and not says_usable:
            s["wrong_rejection"] += 1
            s["true_not_confirmed"] += 1
        if answer == truth:
            s["exact_label"] += 1
    s["n"] = len(items)
    return {"summary": dict(s), "per_category": {k: dict(v) for k, v in per_cat.items()},
            "errors": wrong}


def main() -> None:
    items = {i["id"]: i for i in yaml.safe_load((HERE / "items.yaml").read_text())["items"]}
    results = {}
    for path in sorted((HERE / "results").glob("arm_*.json")):
        arm = path.stem.removeprefix("arm_")
        results[arm] = score(json.loads(path.read_text()), items)
    (HERE / "results" / "scores.json").write_text(json.dumps(results, indent=2) + "\n")
    n = len(items)
    lines = ["# Results", "",
             f"{n} items: {sum(i['truth'] == 'TRUE' for i in items.values())} usable as stated, "
             f"{sum(i['truth'] != 'TRUE' for i in items.values())} not (FALSE or CONDITIONAL).", "",
             "| Arm | Answered | Correct (usable?) | False certifications | True claims not confirmed | Exact 3-way label |",
             "|---|---:|---:|---:|---:|---:|"]
    for arm in ("whiteboard", "python", "tool"):
        if arm not in results:
            continue
        s = results[arm]["summary"]
        lines.append(f"| {ARM_NAMES.get(arm, arm)} | {s.get('answered', 0)}/{n} | "
                     f"{s.get('binary_correct', 0)}/{s.get('answered', 0)} | "
                     f"{s.get('false_certification', 0)} | {s.get('true_not_confirmed', 0)} | "
                     f"{s.get('exact_label', 0)}/{s.get('answered', 0)} |")
    lines += ["", "False certification: answered TRUE for a claim that is FALSE or CONDITIONAL.",
              "", "## Errors by arm", ""]
    for arm, res in results.items():
        lines.append(f"**{ARM_NAMES.get(arm, arm)}**")
        lines += [f"- {e['id']}: truth {e['truth']}, answered {e['answer']} — {e['reason']}"
                  for e in res["errors"]] or ["- none"]
        lines.append("")
    (HERE / "results" / "SUMMARY.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
