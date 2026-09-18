#!/usr/bin/env python3
"""Reconstruct numbered-equation inventory from Guo et al. arXiv:2511.16422v2.

Route A: TeX counter reconstruction from source_anchors/main.tex
Route B: printed tags from arXiv HTML (ltx_tag_equation / ltx_tag_equationgroup)

Does not assign verification outcomes. Does not invent derivation relations.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input"
TEX_PATH = INPUT / "source_anchors" / "main.tex"
HTML_PATH = INPUT / "source_anchors" / "arxiv_html_v2.html"
HTML_NUMS_PATH = INPUT / "source_anchors" / "html_printed_numbers.json"
OUT_YAML = INPUT / "EQUATION_INVENTORY.yaml"
OUT_JSON = INPUT / "source_anchors" / "numbering_crosscheck.json"

NUMBERED_ENVS = {
    "equation",
    "align",
    "alignat",
    "flalign",
    "gather",
    "multline",
    "eqnarray",
}
UNNUMBERED_ENVS = {
    "equation*",
    "align*",
    "alignat*",
    "flalign*",
    "gather*",
    "multline*",
    "eqnarray*",
    "displaymath",
}
NESTED_MATH = {
    "aligned",
    "alignedat",
    "split",
    "gathered",
    "cases",
    "matrix",
    "pmatrix",
    "bmatrix",
    "vmatrix",
    "Vmatrix",
    "array",
    "smallmatrix",
}

BEGIN_RE = re.compile(r"\\begin\{([A-Za-z*]+)\}")
END_RE = re.compile(r"\\end\{([A-Za-z*]+)\}")
SECTION_RE = re.compile(r"\\(section|subsection|subsubsection)\*?\{")
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
COMMENT_RE = re.compile(r"(^|[^\\])%.*$")


def strip_comments(line: str) -> str:
    return COMMENT_RE.sub(lambda m: m.group(1) if m.group(1) else "", line)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def html_printed_numbers(html: str) -> list[str]:
    pat = re.compile(
        r"ltx_tag_(equationgroup|equation)\s+ltx_align_right\">\(([^)]+)\)</span>"
    )
    return [num for _kind, num in pat.findall(html)]


def find_matching_end(lines: list[str], start_idx: int, env: str) -> int:
    depth = 0
    for i in range(start_idx, len(lines)):
        s = strip_comments(lines[i])
        depth += len(re.findall(rf"\\begin\{{{re.escape(env)}\}}", s))
        depth -= len(re.findall(rf"\\end\{{{re.escape(env)}\}}", s))
        if depth == 0:
            return i
    raise RuntimeError(f"unclosed {env} at line {start_idx + 1}")


def top_level_rows(block: str, env: str) -> list[str]:
    """Split an align/gather body into top-level rows (not inside nested envs)."""
    body = block
    body = re.sub(rf"\\begin\{{{env}\}}", "", body, count=1)
    body = re.sub(rf"\\end\{{{env}\}}\s*$", "", body)
    rows: list[str] = []
    buf: list[str] = []
    i = 0
    depth = 0
    while i < len(body):
        m_begin = BEGIN_RE.match(body, i)
        m_end = END_RE.match(body, i)
        if m_begin:
            depth += 1
            buf.append(m_begin.group(0))
            i = m_begin.end()
            continue
        if m_end:
            depth = max(0, depth - 1)
            buf.append(m_end.group(0))
            i = m_end.end()
            continue
        if body.startswith("\\\\", i) and depth == 0:
            rows.append("".join(buf))
            buf = []
            i += 2
            continue
        buf.append(body[i])
        i += 1
    tail = "".join(buf)
    if tail.strip():
        rows.append(tail)
    return rows


def preview_tex(tex: str, n: int = 160) -> str:
    t = re.sub(r"\s+", " ", tex).strip()
    return t[:n]


def snippet_from_tex(tex: str) -> str:
    t = re.sub(r"\\label\{[^}]+\}", "", tex)
    t = re.sub(r"\\begin\{[A-Za-z*]+\}", "", t)
    t = re.sub(r"\\end\{[A-Za-z*]+\}", "", t)
    t = re.sub(r"\s+", " ", t).strip(" &")
    return t[:120]


def reconstruct_tex(lines: list[str]) -> list[dict]:
    eqs: list[dict] = []
    appendix = False
    section_letter = None
    eq_counter = 0
    local_counter = 0
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        s = strip_comments(raw)
        if re.search(r"\\appendix\b", s):
            appendix = True
            i += 1
            continue
        if appendix and re.match(r"\\section\{", s.strip()):
            if section_letter is None:
                section_letter = "A"
            else:
                section_letter = chr(ord(section_letter) + 1)
            local_counter = 0  # local index only; global equation counter does not reset
            i += 1
            continue

        m = BEGIN_RE.search(s)
        if not m:
            i += 1
            continue
        env = m.group(1)
        if env in UNNUMBERED_ENVS or env in NESTED_MATH:
            # skip whole unnumbered/nested block if it starts here at top level
            if env in UNNUMBERED_ENVS:
                end = find_matching_end(lines, i, env)
                i = end + 1
                continue
            i += 1
            continue
        if env not in NUMBERED_ENVS:
            i += 1
            continue

        end = find_matching_end(lines, i, env)
        block = "".join(lines[i : end + 1])
        block_nc = "\n".join(strip_comments(x) for x in lines[i : end + 1])

        if env in {"equation", "multline"}:
            if r"\nonumber" in block_nc or r"\notag" in block_nc:
                i = end + 1
                continue
            eq_counter += 1
            local_counter += 1
            labels = LABEL_RE.findall(block_nc)
            if appendix and section_letter:
                printed = f"{section_letter}-{eq_counter}"
                loc = f"{section_letter}-{local_counter}"
                app = section_letter
            else:
                printed = str(eq_counter)
                loc = None
                app = "main"
            eqs.append(
                {
                    "public_printed_number": printed,
                    "appendix": app,
                    "appendix_local_index": loc,
                    "latex_labels": labels,
                    "source_file": "source_anchors/main.tex",
                    "source_line_start": i + 1,
                    "source_line_end": end + 1,
                    "environment": env,
                    "normalized_tex": block.strip(),
                    "preview": preview_tex(block),
                }
            )
        elif env in {"align", "alignat", "flalign", "gather", "eqnarray"}:
            rows = top_level_rows(block_nc, env)
            # If the only top-level row is a nested aligned/split, it is one numbered display.
            row_offset = 0
            for row in rows:
                if r"\nonumber" in row or r"\notag" in row:
                    row_offset += 1
                    continue
                if not re.sub(r"\s+", "", row):
                    row_offset += 1
                    continue
                eq_counter += 1
                local_counter += 1
                labels = LABEL_RE.findall(row)
                if not labels:
                    # labels may sit on the environment rather than the row
                    labels = LABEL_RE.findall(block_nc) if len(rows) == 1 else []
                if appendix and section_letter:
                    printed = f"{section_letter}-{eq_counter}"
                    loc = f"{section_letter}-{local_counter}"
                    app = section_letter
                else:
                    printed = str(eq_counter)
                    loc = None
                    app = "main"
                eqs.append(
                    {
                        "public_printed_number": printed,
                        "appendix": app,
                        "appendix_local_index": loc,
                        "latex_labels": labels,
                        "source_file": "source_anchors/main.tex",
                        "source_line_start": i + 1,
                        "source_line_end": end + 1,
                        "environment": env,
                        "align_row_index": row_offset,
                        "normalized_tex": row.strip(),
                        "preview": preview_tex(row if len(rows) > 1 else block),
                    }
                )
                row_offset += 1
        i = end + 1
    return eqs


def main() -> None:
    tex_text = TEX_PATH.read_text()
    lines = tex_text.splitlines(keepends=True)
    tex_eqs = reconstruct_tex(lines)
    if HTML_PATH.exists():
        html_nums = html_printed_numbers(HTML_PATH.read_text(errors="replace"))
        html_hash = sha256(HTML_PATH)
    else:
        html_nums = json.loads(HTML_NUMS_PATH.read_text())["printed"]
        html_hash = sha256(HTML_NUMS_PATH)
    tex_nums = [e["public_printed_number"] for e in tex_eqs]

    discrepancies = []
    if tex_nums != html_nums:
        discrepancies.append(
            {
                "kind": "sequence_mismatch",
                "tex_n": len(tex_nums),
                "html_n": len(html_nums),
                "first_diff": next(
                    (
                        (a, b, i)
                        for i, (a, b) in enumerate(zip(tex_nums, html_nums))
                        if a != b
                    ),
                    None,
                ),
                "tex_only": sorted(set(tex_nums) - set(html_nums)),
                "html_only": sorted(set(html_nums) - set(tex_nums)),
            }
        )

    dups = [k for k, v in Counter(tex_nums).items() if v != 1]
    if dups:
        discrepancies.append({"kind": "tex_duplicate_printed", "values": dups})
    dups_h = [k for k, v in Counter(html_nums).items() if v != 1]
    if dups_h:
        discrepancies.append({"kind": "html_duplicate_printed", "values": dups_h})

    by_app = Counter(e["appendix"] for e in tex_eqs)
    payload = {
        "schema_version": "FlagshipEquationInventoryV1",
        "paper": "Zhichao Guo et al., Phys. Rev. Lett. 136, 206303 (2026)",
        "arxiv": "2511.16422v2",
        "main_tex_sha256": sha256(TEX_PATH),
        "html_sha256": html_hash,
        "numbering_note": (
            "Printed numbers come from independent Route A (TeX counters) and "
            "Route B (arXiv HTML ltx_tag). After \\appendix, \\theequation is "
            "\\thesection-\\arabic{equation} and the equation counter is not reset. "
            "Appendix D therefore begins at printed Eq. (D-57)."
        ),
        "n_numbered_tex": len(tex_eqs),
        "n_numbered_html": len(html_nums),
        "coverage_match": tex_nums == html_nums,
        "by_section": dict(by_app),
        "discrepancies": discrepancies,
        "equations": tex_eqs,
    }

    # Write YAML without requiring PyYAML at inventory time.
    def yaml_escape(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    out = []
    out.append("schema_version: FlagshipEquationInventoryV1")
    out.append('paper: "Zhichao Guo et al., Phys. Rev. Lett. 136, 206303 (2026)"')
    out.append('arxiv: "2511.16422v2"')
    out.append(f"main_tex_sha256: {payload['main_tex_sha256']}")
    out.append(f"html_sha256: {payload['html_sha256']}")
    out.append("n_numbered_tex: {}".format(payload["n_numbered_tex"]))
    out.append("n_numbered_html: {}".format(payload["n_numbered_html"]))
    out.append("coverage_match: {}".format(str(payload["coverage_match"]).lower()))
    out.append("by_section:")
    for k, v in by_app.items():
        out.append(f"  {k}: {v}")
    out.append("discrepancies: {}".format("[]" if not discrepancies else ""))
    if discrepancies:
        out.append("  # see numbering_crosscheck.json")
    out.append("equations:")
    for e in tex_eqs:
        labels = e["latex_labels"]
        out.append(f"  - public_printed_number: \"{e['public_printed_number']}\"")
        out.append(f"    appendix: \"{e['appendix']}\"")
        loc = e["appendix_local_index"]
        out.append(f"    appendix_local_index: {('null' if loc is None else chr(34)+loc+chr(34))}")
        out.append(f"    latex_labels: {labels}")
        out.append(f"    source_file: {e['source_file']}")
        out.append(f"    source_line_start: {e['source_line_start']}")
        out.append(f"    source_line_end: {e['source_line_end']}")
        out.append(f"    environment: {e['environment']}")
        if "align_row_index" in e:
            out.append(f"    align_row_index: {e['align_row_index']}")
        out.append(f"    preview: \"{yaml_escape(e['preview'])}\"")
        # equation_role / relation_membership filled later
        out.append("    equation_role: UNKNOWN_ROLE")
        out.append("    relation_membership: []")
    OUT_YAML.write_text("\n".join(out) + "\n")
    OUT_JSON.write_text(
        json.dumps(
            {
                "tex_printed": tex_nums,
                "html_printed": html_nums,
                "match": tex_nums == html_nums,
                "discrepancies": discrepancies,
                "by_section": dict(by_app),
                "n_tex": len(tex_nums),
                "n_html": len(html_nums),
                "main_tex_sha256": payload["main_tex_sha256"],
                "html_sha256": payload["html_sha256"],
            },
            indent=2,
        )
        + "\n"
    )
    print("tex", len(tex_nums), "html", len(html_nums), "match", tex_nums == html_nums)
    if tex_nums != html_nums:
        print("discrepancies", discrepancies)
        print("tex extra", set(tex_nums) - set(html_nums))
        print("html extra", set(html_nums) - set(tex_nums))
        # show first 20 of each if lengths differ
        if len(tex_nums) != len(html_nums):
            print("tex nums", tex_nums)
    else:
        print("by_section", dict(by_app))


if __name__ == "__main__":
    main()
