#!/usr/bin/env python3
"""Count numbered outer align/gather/equation rows in Anan et al. TeX.

Nested array/tikzpicture/tabular line breaks are not equation numbers.
Unnumbered inline displays (Rice–Mele Hamiltonian) are not counted.
"""
from __future__ import annotations

import json
import re
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
                    "cue": re.sub(r"\s+", " ", seg).strip()[:160],
                }
            )
    return rows


def inventory(tex_path: Path) -> dict:
    tex = strip_comments(tex_path.read_text(encoding="utf-8"))
    parts = re.split(r"\\appendix\b", tex, maxsplit=1)
    main, app = parts[0], parts[1] if len(parts) > 1 else ""
    main_rows = rows_in(main, "main")
    letters = "ABCDE"
    app_rows: list[dict] = []
    sec_pat = re.compile(r"\\section\{([^}]*)\}")
    starts = list(sec_pat.finditer(app))
    by_letter: dict[str, int] = {}
    for i, sm in enumerate(starts):
        title = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", sm.group(1))
        title = re.sub(r"\\eqref\{[^}]+\}", "Eq.", title)
        end = starts[i + 1].start() if i + 1 < len(starts) else len(app)
        letter = letters[i] if i < len(letters) else "?"
        chunk = app[sm.start() : end]
        rs = rows_in(chunk, "appendix", letter)
        for r in rs:
            r["appendix_title"] = title
        by_letter[letter] = len(rs)
        app_rows.extend(rs)
    rice = "Rice--Mele model given by $\\mathcal{H}(k)=" in tex
    return {
        "source": "input/nonreciprocal.tex",
        "arxiv": "2604.04520",
        "method": (
            "Outer numbered equation/align/gather/multline rows without "
            "\\nonumber. Nested array/tikzpicture/tabular breaks ignored."
        ),
        "v1_claimed": {"total": 94, "main": 12, "appendix": 82},
        "v2": {
            "total": len(main_rows) + len(app_rows),
            "main": len(main_rows),
            "appendix": len(app_rows),
            "by_appendix_letter": by_letter,
        },
        "correction": (
            "V1 counted 12 main rows by splitting the S-matrix align on an "
            "inner array \\\\. Published numbering gives one number to that "
            "display, so main is 11 not 12. Appendix 82 is unchanged. "
            "Rice–Mele Hamiltonian is inline math, not a numbered equation."
        ),
        "unnumbered_notable": [
            {
                "kind": "inline_display",
                "what": "Rice–Mele Hamiltonian H(k)=t0 cos k σx + δt sin k σy + m σz",
                "locator": "main text, Model calculation section",
                "counted_as_numbered": False,
            }
        ],
        "rice_mele_inline_present": rice,
        "equations": main_rows + app_rows,
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    data = inventory(root / "input" / "nonreciprocal.tex")
    out = root / "input" / "inventory.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    v = data["v2"]
    print("wrote", out)
    print("v2 total", v["total"], "main", v["main"], "appendix", v["appendix"], v["by_appendix_letter"])
    print(data["correction"])
