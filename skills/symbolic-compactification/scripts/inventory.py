#!/usr/bin/env python3
"""Inventory numbered TeX equations. Paper-agnostic. Stdlib only."""
from __future__ import annotations

import argparse
import json
import re
import string
from pathlib import Path

NEST = ("array", "pmatrix", "bmatrix", "cases", "tikzpicture", "tabular", "minipage")
ENVS = ("equation", "align", "gather", "multline")


def strip_comments(tex: str) -> str:
    out = []
    for ln in tex.splitlines():
        buf = []
        i = 0
        while i < len(ln):
            if ln[i] == "%" and (i == 0 or ln[i - 1] != "\\"):
                break
            buf.append(ln[i])
            i += 1
        out.append("".join(buf))
    return "\n".join(out)


def mask_nested(s: str) -> str:
    for env in NEST:
        pat = re.compile(rf"\\begin\{{{env}\}}.*?\\end\{{{env}\}}", re.S)
        s = pat.sub(lambda m: " " * len(m.group(0)), s)
    return s


def rows_in(src: str, where: str, letter: str | None = None) -> list[dict]:
    rows: list[dict] = []
    n = 0
    pat = re.compile(r"\\begin\{(" + "|".join(ENVS) + r")\}(.*?)\\end\{\1\}", re.S)
    for m in pat.finditer(src):
        env, inner = m.group(1), m.group(2)
        masked = mask_nested(inner)
        msegs = re.split(r"\\\\", masked)
        idx = 0
        for j, ms in enumerate(msegs):
            seg = inner[idx : idx + len(ms)]
            idx += len(ms) + (2 if j < len(msegs) - 1 else 0)
            if re.search(r"\\nonumber\b", ms):
                continue
            if not re.search(r"[A-Za-z0-9\\]", ms):
                continue
            n += 1
            lab = None
            lm = re.search(r"\\label\{([^}]+)\}", seg)
            if lm:
                lab = lm.group(1)
            public = f"({n})" if where == "main" else f"{letter}-{n}"
            rows.append(
                {
                    "id": f"{'M' if where == 'main' else letter}-{n}",
                    "public": public,
                    "section": where if where == "main" else f"appendix {letter}",
                    "env": env,
                    "tex_label": lab,
                    "cue": re.sub(r"\s+", " ", seg).strip()[:240],
                }
            )
    return rows


def inventory(tex_path: Path, arxiv: str | None = None) -> dict:
    tex = strip_comments(tex_path.read_text(encoding="utf-8", errors="replace"))
    parts = re.split(r"\\appendix\b", tex, maxsplit=1)
    main, app = parts[0], parts[1] if len(parts) > 1 else ""
    main_rows = rows_in(main, "main")
    letters = string.ascii_uppercase
    app_rows: list[dict] = []
    sec_pat = re.compile(r"\\section\{([^}]*)\}")
    starts = list(sec_pat.finditer(app))
    by_letter: dict[str, int] = {}
    for i, sm in enumerate(starts):
        title = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", sm.group(1))
        end = starts[i + 1].start() if i + 1 < len(starts) else len(app)
        letter = letters[i] if i < len(letters) else "?"
        chunk = app[sm.start() : end]
        rs = rows_in(chunk, "appendix", letter)
        for r in rs:
            r["appendix_title"] = title
        by_letter[letter] = len(rs)
        app_rows.extend(rs)
    total = len(main_rows) + len(app_rows)
    return {
        "source": str(tex_path),
        "arxiv": arxiv,
        "method": (
            "Outer numbered equation/align/gather/multline rows without "
            "\\nonumber. Nested array/tikzpicture/tabular breaks ignored."
        ),
        "v2": {
            "total": total,
            "main": len(main_rows),
            "appendix": len(app_rows),
            "by_appendix_letter": by_letter,
        },
        "equations": main_rows + app_rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Inventory numbered TeX equations")
    ap.add_argument("--tex", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--arxiv", default=None)
    args = ap.parse_args()
    data = inventory(args.tex, args.arxiv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    v = data["v2"]
    print("wrote", args.out)
    print("total", v["total"], "main", v["main"], "appendix", v["appendix"], v["by_appendix_letter"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
