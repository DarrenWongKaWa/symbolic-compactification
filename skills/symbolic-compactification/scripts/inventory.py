#!/usr/bin/env python3
"""Inventory numbered TeX equations. Paper-agnostic. Stdlib only.

Stores the full original formula, location, and content hash. The short
cue is a display field only. Unsupported structure is reported as partial
coverage instead of a fake complete count.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import string
from pathlib import Path

NEST = (
    "array",
    "pmatrix",
    "bmatrix",
    "cases",
    "tikzpicture",
    "tabular",
    "minipage",
    "aligned",
    "gathered",
    "split",
)
SINGLE_ENVS = ("equation", "multline")
MULTI_ENVS = ("align", "gather", "flalign", "eqnarray")
ALIGNAT_ENVS = ("alignat", "flalignat", "gatherat")
ALL_EQ_ENVS = SINGLE_ENVS + MULTI_ENVS + ALIGNAT_ENVS
VERBATIM_ENVS = ("verbatim", "lstlisting", "minted", "comment")
INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")
SETCOUNTER_RE = re.compile(r"\\setcounter\s*\{equation\}\s*\{(-?\d+)\}")
ADDTOCOUNTER_RE = re.compile(r"\\addtocounter\s*\{equation\}\s*\{(-?\d+)\}")
STEPCOUNTER_RE = re.compile(r"\\(?:ref)?stepcounter\s*\{equation\}")
BEGIN_RE = re.compile(r"\\begin\{([A-Za-z*]+)\}")
TAG_RE = re.compile(r"\\tag\*?\{([^}]*)\}")
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
PREVIEW_LIMIT = 240
MAX_INCLUDE_DEPTH = 8
MAX_INCLUDE_FILES = 40
MAX_SOURCE_BYTES = 8_388_608


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def strip_comments(tex: str) -> str:
    out = []
    for line in tex.splitlines():
        buf = []
        i = 0
        while i < len(line):
            if line[i] == "%" and (i == 0 or line[i - 1] != "\\"):
                break
            buf.append(line[i])
            i += 1
        out.append("".join(buf))
    return "\n".join(out)


def mask_envs(src: str, envs: tuple[str, ...]) -> str:
    text = src
    for env in envs:
        begin = f"\\begin{{{env}}}"
        end = f"\\end{{{env}}}"
        out = []
        i = 0
        while i < len(text):
            start = text.find(begin, i)
            if start < 0:
                out.append(text[i:])
                break
            out.append(text[i:start])
            close = text.find(end, start + len(begin))
            if close < 0:
                out.append(" " * (len(text) - start))
                i = len(text)
                break
            span = close + len(end) - start
            out.append(" " * span)
            i = close + len(end)
        text = "".join(out)
    text = re.sub(
        r"\\verb\*?([^\s])(.*?)\1",
        lambda m: " " * len(m.group(0)),
        text,
        flags=re.S,
    )
    return text


def _safe_include(path: Path, root: Path) -> Path | None:
    try:
        resolved = path.resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    if resolved.is_symlink() or not resolved.is_file():
        return None
    return resolved


def expand_inputs(
    tex: str,
    base_dir: Path,
    root: Path,
    warnings: list[str],
    missing: list[str],
    seen: set[Path],
    files_read: list[str],
    depth: int = 0,
) -> str:
    if depth > MAX_INCLUDE_DEPTH:
        warnings.append("include depth exceeded")
        return tex

    def repl(match: re.Match) -> str:
        if len(seen) >= MAX_INCLUDE_FILES:
            warnings.append("too many included files")
            return match.group(0)
        rel = match.group(1).strip()
        candidate = base_dir / rel
        if candidate.suffix == "":
            candidate = candidate.with_suffix(".tex")
        resolved = _safe_include(candidate, root)
        if resolved is None:
            missing.append(rel)
            warnings.append(f"include not read: {rel}")
            return match.group(0)
        if resolved in seen:
            warnings.append(f"cyclic include skipped: {rel}")
            return ""
        seen.add(resolved)
        files_read.append(str(resolved))
        raw = resolved.read_bytes()
        if len(raw) > MAX_SOURCE_BYTES:
            warnings.append(f"include too large: {rel}")
            return match.group(0)
        body = strip_comments(raw.decode("utf-8", errors="replace"))
        return expand_inputs(
            body, resolved.parent, root, warnings, missing, seen, files_read, depth + 1
        )

    return INPUT_RE.sub(repl, tex)


def _find_end(src: str, env: str, inner_start: int) -> tuple[int, int] | None:
    begin = f"\\begin{{{env}}}"
    end = f"\\end{{{env}}}"
    depth = 1
    i = inner_start
    while depth:
        b = src.find(begin, i)
        e = src.find(end, i)
        if e < 0:
            return None
        if b >= 0 and b < e:
            depth += 1
            i = b + len(begin)
        else:
            depth -= 1
            if depth == 0:
                return e, e + len(end)
            i = e + len(end)
    return None


def _skip_begin_options(src: str, i: int) -> int:
    while i < len(src) and src[i].isspace():
        i += 1
    if i < len(src) and src[i] == "[":
        close = src.find("]", i)
        i = len(src) if close < 0 else close + 1
    while i < len(src) and src[i].isspace():
        i += 1
    if i < len(src) and src[i] == "{":
        close = src.find("}", i)
        i = len(src) if close < 0 else close + 1
    return i


def mask_nested(src: str) -> str:
    return mask_envs(src, NEST)


def _row_suppressed(segment: str) -> bool:
    return bool(re.search(r"\\(?:nonumber|notag)\b", segment))


def _tag_public(segment: str) -> str | None:
    match = TAG_RE.search(segment)
    if not match:
        return None
    tag = match.group(1).strip()
    if tag.startswith("(") and tag.endswith(")"):
        return tag
    return f"({tag})"


def _label(segment: str) -> str | None:
    match = LABEL_RE.search(segment)
    return match.group(1) if match else None


def _line_of(src: str, index: int) -> int:
    return src[:index].count("\n") + 1


def _make_row(
    *,
    public: str,
    env: str,
    tex: str,
    where: str,
    letter: str | None,
    seq: int,
    start: int,
    end: int,
    src: str,
    source_file: str,
) -> dict:
    collapsed = re.sub(r"\s+", " ", tex).strip()
    ident = f"{'M' if where == 'main' else letter}-{seq}"
    return {
        "id": ident,
        "public": public,
        "section": where if where == "main" else f"appendix {letter}",
        "env": env,
        "tex_label": _label(tex),
        "tex": tex.strip(),
        "tex_sha256": sha256_text(tex.strip()),
        "cue": collapsed[:PREVIEW_LIMIT],
        "source_file": source_file,
        "line_start": _line_of(src, start),
        "line_end": _line_of(src, max(start, end - 1)),
    }


def _split_rows(inner: str) -> list[str]:
    masked = mask_nested(inner)
    parts = re.split(r"\\\\", masked)
    rows = []
    idx = 0
    for j, masked_seg in enumerate(parts):
        seg = inner[idx : idx + len(masked_seg)]
        idx += len(masked_seg) + (2 if j < len(parts) - 1 else 0)
        rows.append(seg)
    return rows


def _consume_counters(chunk: str, counter: int) -> int:
    for match in SETCOUNTER_RE.finditer(chunk):
        counter = int(match.group(1))
    for match in ADDTOCOUNTER_RE.finditer(chunk):
        counter += int(match.group(1))
    counter += len(STEPCOUNTER_RE.findall(chunk))
    return counter


def _collect_env_rows(
    env: str,
    inner: str,
    *,
    counter: int,
    sub_parent: int | None,
    sub_index: list[int],
    where: str,
    letter: str | None,
    seq: list[int],
    start: int,
    src: str,
    source_file: str,
) -> tuple[list[dict], int]:
    rows: list[dict] = []
    base_env = env.rstrip("*")
    if env.endswith("*"):
        return rows, counter

    def public_for(segment: str, next_counter: int) -> tuple[str, int]:
        tagged = _tag_public(segment)
        if tagged:
            return tagged, next_counter
        if sub_parent is not None:
            letter_s = string.ascii_lowercase[sub_index[0]]
            sub_index[0] += 1
            return f"({sub_parent}{letter_s})", next_counter
        if where != "main" and letter:
            return f"{letter}-{next_counter}", next_counter
        return f"({next_counter})", next_counter

    if base_env in SINGLE_ENVS:
        if _row_suppressed(inner):
            return rows, counter
        if sub_parent is None and not TAG_RE.search(inner):
            counter += 1
        seq[0] += 1
        public, counter = public_for(inner, counter)
        rows.append(
            _make_row(
                public=public,
                env=env,
                tex=inner,
                where=where,
                letter=letter,
                seq=seq[0],
                start=start,
                end=start + len(inner),
                src=src,
                source_file=source_file,
            )
        )
        return rows, counter

    for seg in _split_rows(inner):
        if not re.search(r"[A-Za-z0-9\\]", mask_nested(seg)):
            continue
        if _row_suppressed(seg):
            continue
        if sub_parent is None and not TAG_RE.search(seg):
            counter += 1
        seq[0] += 1
        public, counter = public_for(seg, counter)
        rows.append(
            _make_row(
                public=public,
                env=env,
                tex=seg,
                where=where,
                letter=letter,
                seq=seq[0],
                start=start,
                end=start + len(inner),
                src=src,
                source_file=source_file,
            )
        )
    return rows, counter


def rows_in(
    src: str,
    where: str,
    letter: str | None = None,
    *,
    source_file: str = "",
    start_counter: int = 0,
) -> tuple[list[dict], int, list[str]]:
    rows: list[dict] = []
    warnings: list[str] = []
    counter = start_counter
    seq = [0]
    i = 0
    while i < len(src):
        match = BEGIN_RE.search(src, i)
        if not match:
            counter = _consume_counters(src[i:], counter)
            break
        counter = _consume_counters(src[i : match.start()], counter)
        env = match.group(1)
        base = env.rstrip("*")
        if env != "subequations" and base not in ALL_EQ_ENVS:
            i = match.end()
            continue
        inner_start = _skip_begin_options(src, match.end())
        ended = _find_end(src, env, inner_start)
        if ended is None:
            warnings.append(f"unclosed environment {env}")
            break
        end_inner, end_abs = ended
        inner = src[inner_start:end_inner]
        if env == "subequations":
            counter += 1
            parent = counter
            child_seq = [0]
            sub_rows, _, sub_warn = rows_in(
                inner,
                where,
                letter,
                source_file=source_file,
                start_counter=0,
            )
            warnings.extend(sub_warn)
            letters = string.ascii_lowercase
            rebuilt = []
            for j, row in enumerate(sub_rows):
                row = dict(row)
                suffix = letters[j] if j < len(letters) else f"z{j}"
                row["public"] = f"({parent}{suffix})"
                seq[0] += 1
                prefix = "M" if where == "main" else letter
                row["id"] = f"{prefix}-{seq[0]}"
                rebuilt.append(row)
            rows.extend(rebuilt)
            i = end_abs
            continue
        if base in ALL_EQ_ENVS:
            env_rows, counter = _collect_env_rows(
                env,
                inner,
                counter=counter,
                sub_parent=None,
                sub_index=[0],
                where=where,
                letter=letter,
                seq=seq,
                start=inner_start,
                src=src,
                source_file=source_file,
            )
            rows.extend(env_rows)
            i = end_abs
            continue
        i = match.end()
    return rows, counter, warnings


def inventory(tex_path: Path, arxiv: str | None = None) -> dict:
    root = tex_path.parent.resolve()
    raw = tex_path.read_bytes()
    warnings: list[str] = []
    missing: list[str] = []
    files_read = [str(tex_path)]
    if len(raw) > MAX_SOURCE_BYTES:
        warnings.append("main file truncated: exceeds size budget")
        raw = raw[:MAX_SOURCE_BYTES]
    tex = strip_comments(raw.decode("utf-8", errors="replace"))
    tex = mask_envs(tex, VERBATIM_ENVS)
    seen: set[Path] = {tex_path.resolve()}
    tex = expand_inputs(tex, tex_path.parent, root, warnings, missing, seen, files_read)
    tex = mask_envs(tex, VERBATIM_ENVS)
    if re.search(r"\\begin\{(verbatim|lstlisting|minted|comment)\}", tex):
        warnings.append("unclosed verbatim-like environment; inventory is partial")
    if re.search(r"\\numberwithin\s*\{equation\}", tex):
        warnings.append("\\numberwithin is not interpreted; numbering may be partial")
    if re.search(r"\\eqno\b|\\begin\{IEEEeqnarray", tex):
        warnings.append("unparsed numbering construct; inventory is partial")
    parts = re.split(r"\\appendix\b", tex, maxsplit=1)
    main, app = parts[0], parts[1] if len(parts) > 1 else ""
    main_rows, _, main_warn = rows_in(main, "main", source_file=str(tex_path), start_counter=0)
    warnings.extend(main_warn)
    letters = string.ascii_uppercase
    app_rows: list[dict] = []
    sec_pat = re.compile(r"\\section\{([^}]*)\}")
    starts = list(sec_pat.finditer(app))
    by_letter: dict[str, int] = {}
    if app and not starts:
        rs, _, w = rows_in(app, "appendix", "A", source_file=str(tex_path), start_counter=0)
        warnings.extend(w)
        app_rows.extend(rs)
        by_letter["A"] = len(rs)
    for i, sm in enumerate(starts):
        title = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", sm.group(1))
        end = starts[i + 1].start() if i + 1 < len(starts) else len(app)
        letter = letters[i] if i < len(letters) else "?"
        chunk = app[sm.start() : end]
        rs, _, w = rows_in(
            chunk, "appendix", letter, source_file=str(tex_path), start_counter=0
        )
        warnings.extend(w)
        for row in rs:
            row["appendix_title"] = title
        by_letter[letter] = len(rs)
        app_rows.extend(rs)
    equations = main_rows + app_rows
    total = len(equations)
    coverage_status = "complete" if not warnings and not missing else "partial"
    return {
        "source": str(tex_path),
        "arxiv": arxiv,
        "method": (
            "Numbered outer equation/align/gather/multline rows. "
            "Honours \\notag/\\nonumber/\\tag/\\setcounter, subequations, "
            "and bounded \\input. Nested aligned/array breaks are not numbers. "
            "Verbatim is masked. Preview cue is not the mathematical source."
        ),
        "v2": {
            "total": total,
            "main": len(main_rows),
            "appendix": len(app_rows),
            "by_appendix_letter": by_letter,
        },
        "coverage": {
            "status": coverage_status,
            "warnings": warnings,
            "files_read": files_read,
            "files_missing": missing,
            "uncovered": missing,
        },
        "equations": equations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory numbered TeX equations")
    parser.add_argument("--tex", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--arxiv", default=None)
    args = parser.parse_args()
    data = inventory(args.tex, args.arxiv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    v = data["v2"]
    print("wrote", args.out)
    print("total", v["total"], "main", v["main"], "appendix", v["appendix"], v["by_appendix_letter"])
    if data["coverage"]["status"] != "complete":
        print("coverage", data["coverage"]["status"], data["coverage"]["warnings"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
