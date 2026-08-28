"""Build FROZEN_INPUTS.json from historical run files. No LLM. No rewrite."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "FROZEN_INPUTS.json"

P1_RUNS = ROOT / "research" / "grounded_proposer" / "runs"
P2_RUNS = ROOT / "research" / "representation_invention" / "llm" / "runs"
GUO_SRC = ROOT / "examples" / "long" / "Guo_Sigma_abc_dc_exact.txt"

# Families Track V may rescore. Historical files are hashed, never mutated.
INCLUDE = (
    "guo-sigma-abc__P1_A2__",
    "guo-sigma-abc__P2__",
    "CAL-G-confluence__",
    "dev-a-newton-first__P2__",
    "dev-a-hermite-two__P2__",
    "dev-a-repeated-node__P2__",
    "dev-b-piecewise-dd__P2__",
    "dev-b-special-fn__P2__",
    "test-a-newton-first__P2__",
    "test-a-hermite-two__P2__",
    "test-b-piecewise-dd__P2__",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _member_ids(h: dict) -> list[str]:
    ids = [str(x) for x in (h.get("member_ids") or [])]
    for m in h.get("member_maps") or []:
        if isinstance(m, dict) and m.get("source_node_id"):
            ids.append(str(m["source_node_id"]))
    for k in ("generic_member", "degenerate_member"):
        v = h.get(k)
        if v:
            ids.append(str(v))
    out: list[str] = []
    for i in ids:
        if i not in out:
            out.append(i)
    return out


def _hyp_record(h: dict, score: dict | None, i: int) -> dict[str, Any]:
    score = score or {}
    verdicts = score.get("verdicts") or []
    if score.get("n_zero"):
        prev = "ZERO" if not score.get("n_nonzero") and not score.get("n_unknown") else "MIXED"
    elif score.get("n_nonzero") and not score.get("n_zero"):
        prev = "NONZERO"
    elif score.get("n_unknown") and not score.get("n_zero") and not score.get("n_nonzero"):
        prev = "UNKNOWN"
    elif score.get("compile_status") in {"COMPILE_FAILURE", "not_wired", "skipped"}:
        prev = str(score.get("compile_status"))
    elif score.get("layer") == "OK":
        prev = "ZERO"
    else:
        prev = score.get("layer") or "UNSCORED"
    return {
        "index": i,
        "representation_type": h.get("representation_type"),
        "parse_status": h.get("parse_status"),
        "member_ids": _member_ids(h),
        "latent_object": (h.get("latent_object") or "")[:240],
        "reconstruction_rule": (h.get("reconstruction_rule") or "")[:240],
        "operators": [
            {"member_id": o.get("member_id") or o.get("member"), "kind": o.get("kind") or o.get("O")}
            for o in (h.get("operators") or [])
            if isinstance(o, dict)
        ],
        "n_proof_obligations": len(h.get("proof_obligations") or []),
        "previous_verdict": prev,
        "previous_layer": score.get("layer") or score.get("detail") or prev,
        "compile_status": score.get("compile_status"),
        "n_zero": score.get("n_zero"),
        "n_nonzero": score.get("n_nonzero"),
        "n_unknown": score.get("n_unknown"),
        "verdicts": verdicts,
        "dd_class": (score.get("dd_class") if isinstance(score, dict) else None),
    }


def freeze_file(path: Path, family: str) -> dict[str, Any]:
    raw = path.read_bytes()
    rec = json.loads(raw)
    hyps = rec.get("hypotheses") or []
    scores = rec.get("scores") or []
    summary = rec.get("summary") or {}
    src = rec.get("item_id") or ""
    src_hash = sha256_file(GUO_SRC) if src == "guo-sigma-abc" and GUO_SRC.is_file() else None
    rows = []
    for i, h in enumerate(hyps):
        if not isinstance(h, dict):
            continue
        sc = scores[i] if i < len(scores) and isinstance(scores[i], dict) else {}
        rows.append(_hyp_record(h, sc, i))
    return {
        "path": str(path.relative_to(ROOT)),
        "family": family,
        "sha256": sha256_bytes(raw),
        "nbytes": len(raw),
        "protocol": rec.get("protocol"),
        "condition": rec.get("condition"),
        "item_id": rec.get("item_id"),
        "seed": rec.get("seed"),
        "model": rec.get("model"),
        "parse_status": rec.get("parse_status"),
        "n_hypotheses": rec.get("n_hypotheses") or len(hyps),
        "n_ok": rec.get("n_ok"),
        "n_grounded": rec.get("n_grounded"),
        "n_zero": rec.get("n_zero") or summary.get("n_zero"),
        "n_nonzero": rec.get("n_nonzero") or summary.get("n_nonzero"),
        "n_unknown": rec.get("n_unknown") or summary.get("n_unknown"),
        "compile_status": rec.get("compile_status") or summary.get("compile_status"),
        "source_expression_hash": src_hash,
        "hypotheses": rows,
    }


def family_of(name: str) -> str | None:
    for prefix in INCLUDE:
        if name.startswith(prefix):
            if "guo" in prefix and "P1" in prefix:
                return "guo_p1"
            if "guo" in prefix and "P2" in prefix:
                return "guo_p2"
            if "newton" in prefix:
                return "newton"
            if "hermite" in prefix or "repeated" in prefix:
                return "hermite"
            if "piecewise" in prefix:
                return "piecewise_dd"
            if "special" in prefix:
                return "special_fn"
            if "CAL-G" in prefix:
                return "confluence_toy"
            return "other"
    return None


def build() -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for d in (P1_RUNS, P2_RUNS):
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.json")):
            fam = family_of(p.name)
            if fam is None:
                continue
            files.append(freeze_file(p, fam))
    n_hyps = sum(len(f["hypotheses"]) for f in files)
    return {
        "track": "V",
        "no_llm_calls": True,
        "authority": "91a401b",
        "n_files": len(files),
        "n_hypotheses": n_hyps,
        "files": files,
    }


def main() -> None:
    blob = build()
    OUT.write_text(json.dumps(blob, indent=2) + "\n")
    print("wrote", OUT, "files", blob["n_files"], "hyps", blob["n_hypotheses"])


if __name__ == "__main__":
    main()
