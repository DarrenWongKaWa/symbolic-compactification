#!/usr/bin/env python3
"""Check that the human-facing ledger is a projection, not a certificate.

No API. No engine. Compares hashes, required copy, and HTML row statuses
against frozen RESULTS.md on v0.3.0-alpha (scientific authority).
"""
from __future__ import annotations

import hashlib
import html as html_lib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS_GIT_PATH = "v0.3.0-alpha:examples/flagship/guo/RESULTS.md"
RESULTS_TREE = HERE.parent / "evidence" / "RESULTS.md"
FORBIDDEN = [
    "full derivation verified",
    "189 equations verified",
    "five papers fully verified",
    "the derivation holds",
    "full derivation audit",
    "189 verified",
    "proved zero",
    "needs judgment",
    "do not emit zero here",
]
REQUIRED = [
    "Presentation is not a certificate",
    "inventoried equations",
    "extracted relations",
    "executable obligations",
    "none of the submitted executable relations",
    "does not mean the paper has no incorrect steps",
    "Eq. (D-117) → Eq. (5)",
    "v0.3 targets obligation soundness",
    "Audit validity (transcription, relation extraction, assumption selection) remains partly human-mediated",
    "certifies A ⇒ R=0, not A itself",
    "local identity verified + declared rule",
    "not CAS evaluation of the global integral",
    "15 remainder rows + 2 UNKNOWN limit rows",
    "AUDIT_INCOMPLETE",
    "missing_declared_moves",
    "unsigned_must_review",
    "Silence from non-submission is not a pass",
]


def norm_eq(s: str) -> str:
    s = html_lib.unescape(s)
    s = s.replace("→", "->").replace("⟶", "->").replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_results_md() -> tuple[str, str | None]:
    """Frozen table lives in-tree. The v0.3.0-alpha path is optional history."""
    if RESULTS_TREE.is_file():
        return RESULTS_TREE.read_text(encoding="utf-8"), None
    proc = subprocess.run(
        ["git", "show", RESULTS_GIT_PATH],
        cwd=HERE,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip() or f"git show failed ({proc.returncode})"
        return "", err
    return proc.stdout, None


def parse_results_table(md: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    in_table = False
    for line in md.splitlines():
        if line.startswith("| Eq. relation"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        if re.match(r"^\|[\s\-:|]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 7:
            continue
        pairs.append((norm_eq(cells[0]), cells[-1]))
    return pairs


def parse_html_ledger(page: str) -> list[tuple[str, str]]:
    m = re.search(
        r'<table[^>]*id="obligation-table"[^>]*>.*?<tbody>(.*?)</tbody>',
        page,
        flags=re.S | re.I,
    )
    if not m:
        return []
    rows: list[tuple[str, str]] = []
    for tr in re.finditer(r"<tr\b([^>]*)>(.*?)</tr>", m.group(1), flags=re.S | re.I):
        attrs, inner = tr.group(1), tr.group(2)
        sm = re.search(r'data-status="([^"]+)"', attrs)
        status = sm.group(1) if sm else ""
        tm = re.search(r"<td>\s*<a[^>]*>(.*?)</a>", inner, flags=re.S | re.I)
        if not tm:
            continue
        eq = re.sub(r"<[^>]+>", "", tm.group(1))
        rows.append((norm_eq(eq), status))
    return rows


def extract_card(page: str) -> str:
    m = re.search(
        r'<article\b[^>]*id="rel-R007"[^>]*>.*?</article>',
        page,
        flags=re.S | re.I,
    )
    return m.group(0) if m else ""


def main() -> int:
    data = HERE / "report-data.json"
    html_path = HERE.parent / "output" / "index.html"
    rec = HERE.parent / "expected" / "PRESENTATION_SHA256.txt"
    digest = hashlib.sha256(data.read_bytes()).hexdigest()
    recorded = rec.read_text()
    page = html_path.read_text()
    visible = re.sub(
        r'<script\b[^>]*>.*?</script>',
        "",
        page,
        flags=re.S | re.I,
    )
    errors: list[str] = []
    if digest not in recorded:
        errors.append(f"PRESENTATION_SHA256.txt missing {digest}")
    m = re.search(r'data-sha256="([0-9a-f]{64})"', page)
    if not m or m.group(1) != digest:
        errors.append("index.html data-sha256 does not match report-data.json")
    if page.count("<tr class=") != 146:
        errors.append(f"expected 146 ledger rows, got {page.count('<tr class=')}")
    if "Eq. (D-117)" not in page or "row-R007" not in page:
        errors.append("missing D-117 ledger row")
    obl = re.search(
        r'<table[^>]*id="obligation-table"[^>]*>.*?<tbody>(.*?)</tbody>',
        page,
        flags=re.S | re.I,
    )
    if obl:
        gap_n = len(re.findall(r'data-deviation="encoding_gap"', obl.group(1)))
        judge_n = len(re.findall(r'data-deviation="needs_judgment"', obl.group(1)))
        must_n = len(re.findall(r'data-queue="must_review"', obl.group(1)))
        if gap_n != 4:
            errors.append(f"obligation-table encoding_gap: expected 4, got {gap_n}")
        if judge_n != 30:
            errors.append(f"obligation-table needs_judgment: expected 30, got {judge_n}")
        if must_n != 4:
            errors.append(f"obligation-table must_review: expected 4, got {must_n}")
        if re.search(r'id="row-R024"[^>]*data-deviation="encoding_gap"', obl.group(1)):
            errors.append("C-27 definition must not be an encoding gap")
        if re.search(r'id="row-R024"[^>]*data-hue="orange"', obl.group(1)):
            errors.append("C-27 must be blue def, not orange")
    if re.search(r'data-status="NEEDS_JUDGMENT"', page):
        errors.append("Needs judgment header pill must be removed")
    if "Must review" not in page:
        errors.append("missing Must review heading")
    if "Judged 64" not in page:
        errors.append("missing judged 64 line")
    if re.search(r"0\*|ws-zero", page):
        errors.append("invalid 0* overlay must be absent from reviewer HTML")
    if page.count("sign-btn") < 8:
        errors.append("expected Sign buttons on must-review and obligation You columns")
    if re.search(r'<td class="you-cell">sign</td>', page):
        errors.append("You column must be the Sign button, not a second sign chip")
    for tr in re.finditer(r'<tr[^>]*data-you="sign"[^>]*>(.*?)</tr>', page, flags=re.S):
        if "chip sign" in tr.group(1):
            errors.append("must-review Status must not also carry a sign chip")
            break
    if 'class="stack"' not in visible.split('id="main"')[0]:
        errors.append("first screen missing stacked colour bar")
    head0 = visible.split('id="main"')[0]
    if 'id="map-sec"' not in head0:
        errors.append("first screen missing Appendix map A–G (must not be a closed details)")
    if re.search(r'<details[^>]*id="map-sec"', page):
        errors.append("Appendix map must be a visible section, not details")
    if "Local algebra was not compiled" not in page and "Encoding gap" not in page:
        errors.append("encoding-gap copy missing")
    if "Green = checked 0" not in page:
        errors.append("missing colour legend")
    low = visible.lower()
    if re.search(r"\bverified\b", visible) and "local identity verified" not in visible.lower():
        pass
    if re.search(r"\bVerified\b", visible):
        errors.append("forbidden copy: Verified")
    for phrase in FORBIDDEN:
        if phrase in low:
            errors.append(f"forbidden copy: {phrase}")
    for phrase in REQUIRED:
        if phrase not in page:
            errors.append(f"missing required copy: {phrase}")
    noscript = re.sub(r"<script\b[^>]*>.*?</script>", "", page, flags=re.S | re.I)
    if noscript.count("<tr class=") != 146:
        errors.append("no-JS table lost rows")

    md, git_err = load_results_md()
    results_pairs: list[tuple[str, str]] = []
    html_set: set[tuple[str, str]] = set()
    results_set: set[tuple[str, str]] = set()
    if git_err:
        errors.append(f"cannot read {RESULTS_GIT_PATH}: {git_err}")
    else:
        results_pairs = parse_results_table(md)
        if len(results_pairs) != 146:
            errors.append(f"RESULTS table: expected 146 rows, got {len(results_pairs)}")
        html_pairs = parse_html_ledger(page)
        if len(html_pairs) != 146:
            errors.append(f"HTML ledger: expected 146 parsed rows, got {len(html_pairs)}")
        results_set = set(results_pairs)
        html_set = set(html_pairs)
        extra = sorted(html_set - results_set)
        if extra:
            preview = "; ".join(f"{eq} => {st}" for eq, st in extra[:8])
            errors.append(
                "HTML ledger row statuses are not a subset of RESULTS table "
                f"statuses (same eq relation): {preview}"
            )
        # Keep UNKNOWN limit rows unmerged in the table.
        for eq, st in results_pairs:
            if st == "UNKNOWN":
                html_st = {s for e, s in html_set if e == eq}
                if html_st != {"UNKNOWN"}:
                    errors.append(
                        f"RESULTS UNKNOWN row {eq} merged or missing in HTML "
                        f"(HTML statuses {sorted(html_st) or ['<absent>']})"
                    )
        expected_table = {
            "EXACT_ZERO": 32,
            "ZERO_UNDER_SUBSTITUTION": 21,
            "CERTIFIED_BY_RULE": 11,
            "UNKNOWN_REMAINDER": 15,
            "UNKNOWN": 2,
            "STRUCTURAL": 47,
            "UNSUPPORTED": 18,
            "NONZERO": 0,
        }
        html_counts = Counter(st for _, st in html_pairs)
        for status, n in expected_table.items():
            got = html_counts.get(status, 0)
            if got != n:
                errors.append(
                    f"HTML table count {status}: expected {n}, got {got} "
                    "(do not merge UNKNOWN limit rows into UNKNOWN_REMAINDER)"
                )

    payload = json.loads(data.read_text())
    r007 = next((r for r in payload.get("relations", []) if r.get("id") == "R007"), None)
    if not r007:
        errors.append("report-data.json missing R007 D-117")
    else:
        tex = (r007.get("direct") or {}).get("residual_tex") or ""
        cond = (r007.get("condition") or {}).get("tex") or ""
        if "f_n^{(4)}" not in tex.replace(" ", "") and "f_{n}^{(4)}" not in tex:
            errors.append("R007 residual missing f_n^{(4)}")
        if "2f_{0,n}" not in cond.replace(" ", ""):
            errors.append("R007 condition missing f_n^{(4)}=2f_{0,n}^{(4)}")

    # Integrity gate: selected-edge NONZERO=0 is not a product pass.
    head = noscript.split('id="main"')[0]
    if "AUDIT_INCOMPLETE" not in head:
        errors.append("first screen missing AUDIT_INCOMPLETE")
    if "missing_declared_moves" not in head:
        errors.append("first screen missing missing_declared_moves")
    if "unsigned_must_review" not in head:
        errors.append("first screen missing unsigned_must_review")
    hero = re.findall(r'<span class="n">([^<]+)</span>', head)
    if any("NONZERO" in h.upper() for h in hero):
        errors.append("hero metrics must not include NONZERO; that is not a product pass")
    if re.search(r"NONZERO\s*=\s*0", head) and "engine metric" not in head.lower() and "AUDIT_INCOMPLETE" not in head:
        errors.append("first screen NONZERO=0 without AUDIT_INCOMPLETE is a release fail")

    omit = HERE.parent / "expected" / "omit-declared-moves.html"
    if not omit.exists():
        errors.append("missing tests/omit-declared-moves.html integrity fixture")
    else:
        fix = omit.read_text()
        if "AUDIT_INCOMPLETE" not in fix:
            errors.append("omit-declared-moves fixture missing AUDIT_INCOMPLETE")
        if not re.search(r"missing_declared_moves[\s\S]{0,80}3", fix):
            errors.append("omit-declared-moves fixture must set missing_declared_moves = 3")
        if re.search(r'<span class="n">[^<]*NONZERO', fix, re.I):
            errors.append("omit-3 fixture must not hero NONZERO")

    if errors:
        print("VERIFY_FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("VERIFY_OK")
    print("report-data.json", digest)
    print("presentation is not certificate")
    print("HTML ledger ⊆ RESULTS", f"{len(html_set)}/{len(results_set)} keyed statuses")
    counts = Counter(st for _, st in results_pairs)
    print(
        "RESULTS table",
        "EXACT_ZERO", counts.get("EXACT_ZERO", 0),
        "ZERO_UNDER_SUBSTITUTION", counts.get("ZERO_UNDER_SUBSTITUTION", 0),
        "CERTIFIED_BY_RULE", counts.get("CERTIFIED_BY_RULE", 0),
        "UNKNOWN_REMAINDER", counts.get("UNKNOWN_REMAINDER", 0),
        "UNKNOWN", counts.get("UNKNOWN", 0),
        "STRUCTURAL", counts.get("STRUCTURAL", 0),
        "UNSUPPORTED", counts.get("UNSUPPORTED", 0),
        "NONZERO", counts.get("NONZERO", 0),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
