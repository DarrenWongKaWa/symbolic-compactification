#!/usr/bin/env python3
"""Download an arXiv e-print into a fresh directory. Stdlib only.

Identifies tar.gz, gzipped TeX, raw TeX, and PDF. Rejects HTML error pages,
path traversal, links, and special files. Each call replaces the previous
extraction rather than mixing trees.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path

UA = "symbolic-compactification-skill/0.3.4 (scientific audit; +https://arxiv.org)"
MAX_DOWNLOAD_BYTES = 32 * 1024 * 1024
MAX_MEMBER_BYTES = 8 * 1024 * 1024
MAX_TOTAL_UNPACK = 64 * 1024 * 1024
MAX_MEMBERS = 2000


class FetchError(RuntimeError):
    pass


class UnsafeArchive(FetchError):
    pass


def _bounded_read(resp, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = resp.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise FetchError(f"download exceeds {max_bytes} bytes")
        chunks.append(chunk)
    return b"".join(chunks)


def _looks_html(blob: bytes) -> bool:
    head = blob.lstrip().lower()[:200]
    return head.startswith(b"<!doctype html") or head.startswith(b"<html")


def _looks_pdf(blob: bytes) -> bool:
    return blob.startswith(b"%PDF-")


def _looks_gzip(blob: bytes) -> bool:
    return blob.startswith(b"\x1f\x8b")


def _looks_tex(blob: bytes) -> bool:
    text = blob.lstrip()[:4000]
    return b"\\documentclass" in text or b"\\begin{document}" in text


def _bounded_gunzip(blob: bytes, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    with gzip.GzipFile(fileobj=io.BytesIO(blob)) as gz:
        while True:
            chunk = gz.read(64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise FetchError("gunzip exceeds budget")
            chunks.append(chunk)
    return b"".join(chunks)


def _contained(root: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def _safe_member_path(dest: Path, name: str) -> Path:
    dest = dest.resolve()
    if not name or name.startswith("/") or name.startswith("\\"):
        raise UnsafeArchive(f"absolute archive path rejected: {name}")
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise UnsafeArchive(f"traversing archive path rejected: {name}")
    cursor = dest
    for part in path.parts:
        if part in ("", ".", ".."):
            raise UnsafeArchive(f"traversing archive path rejected: {name}")
        cursor = cursor / part
        if cursor.is_symlink():
            raise UnsafeArchive(f"symlink component rejected: {name}")
    target = cursor.resolve()
    if not _contained(dest, target):
        raise UnsafeArchive(f"archive member escapes dest: {name}")
    return target


def _extract_tar(blob: bytes, dest: Path) -> Path:
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    unpacked = 0
    members = 0
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as tf:
        for member in tf:
            members += 1
            if members > MAX_MEMBERS:
                raise UnsafeArchive("too many archive members")
            if member.issym() or member.islnk():
                raise UnsafeArchive(f"link rejected: {member.name}")
            if member.isdir():
                path = _safe_member_path(dest, member.name)
                path.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise UnsafeArchive(f"special archive member rejected: {member.name}")
            if member.size < 0 or member.size > MAX_MEMBER_BYTES:
                raise UnsafeArchive(f"member too large: {member.name}")
            unpacked += member.size
            if unpacked > MAX_TOTAL_UNPACK:
                raise UnsafeArchive("unpacked archive exceeds budget")
            path = _safe_member_path(dest, member.name)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.is_symlink() or path.parent.is_symlink():
                raise UnsafeArchive(f"symlink component rejected: {member.name}")
            resolved = path.resolve()
            if not _contained(dest, resolved):
                raise UnsafeArchive(f"archive member escapes dest: {member.name}")
            extracted = tf.extractfile(member)
            if extracted is None:
                raise UnsafeArchive(f"unreadable member: {member.name}")
            data = extracted.read(MAX_MEMBER_BYTES + 1)
            if len(data) > MAX_MEMBER_BYTES:
                raise UnsafeArchive(f"member too large: {member.name}")
            resolved.write_bytes(data)
    return dest


def _reset_dest(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink():
        raise FetchError("destination must not be a symlink")
    for name in ("src", "paper.pdf", "source.tex", "eprint", "fetch.json"):
        path = dest / name
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    for path in dest.glob("ssc-fetch-*"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    for path in dest.glob("*.tex"):
        if path.is_file() and not path.is_symlink():
            path.unlink()


def _write_meta(dest: Path, **fields: object) -> None:
    (dest / "fetch.json").write_text(
        json.dumps(fields, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def fetch(arxiv_id: str, dest: Path) -> Path:
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    aid = (
        arxiv_id.replace("arxiv:", "")
        .replace("https://arxiv.org/abs/", "")
        .replace("http://arxiv.org/abs/", "")
        .strip("/")
    )
    url = f"https://arxiv.org/e-print/{aid}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        final_url = getattr(resp, "geturl", lambda: url)()
        blob = _bounded_read(resp, MAX_DOWNLOAD_BYTES)
    digest = hashlib.sha256(blob).hexdigest()
    if _looks_html(blob):
        raise FetchError("server returned HTML, not an e-print")

    staging = Path(tempfile.mkdtemp(prefix="ssc-fetch-"))
    try:
        if _looks_pdf(blob):
            _reset_dest(dest)
            (dest / "eprint").write_bytes(blob)
            pdf = dest / "paper.pdf"
            pdf.write_bytes(blob)
            _write_meta(
                dest,
                arxiv_id=aid,
                final_url=final_url,
                content_sha256=digest,
                kind="pdf",
                extracted_to=str(pdf),
            )
            return pdf

        try:
            src = _extract_tar(blob, staging)
            _reset_dest(dest)
            (dest / "eprint").write_bytes(blob)
            final_src = dest / "src"
            shutil.move(str(src), str(final_src))
            _write_meta(
                dest,
                arxiv_id=aid,
                final_url=final_url,
                content_sha256=digest,
                kind="tar",
                extracted_to=str(final_src),
            )
            return final_src
        except tarfile.TarError:
            pass

        raw = blob
        if _looks_gzip(blob):
            raw = _bounded_gunzip(blob, MAX_TOTAL_UNPACK)
        if _looks_html(raw):
            raise FetchError("server returned HTML, not an e-print")
        if _looks_pdf(raw):
            _reset_dest(dest)
            (dest / "eprint").write_bytes(blob)
            pdf = dest / "paper.pdf"
            pdf.write_bytes(raw)
            _write_meta(
                dest,
                arxiv_id=aid,
                final_url=final_url,
                content_sha256=digest,
                kind="pdf.gz" if _looks_gzip(blob) else "pdf",
                extracted_to=str(pdf),
            )
            return pdf
        if _looks_tex(raw):
            _reset_dest(dest)
            (dest / "eprint").write_bytes(blob)
            src = dest / "src"
            src.mkdir(parents=True, exist_ok=True)
            tex = src / "main.tex"
            tex.write_bytes(raw)
            _write_meta(
                dest,
                arxiv_id=aid,
                final_url=final_url,
                content_sha256=digest,
                kind="tex.gz" if _looks_gzip(blob) else "tex",
                extracted_to=str(tex),
            )
            return src
        raise FetchError("unrecognized e-print payload")
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="arXiv id, e.g. 2604.04520")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        path = fetch(args.id, args.out)
    except FetchError as exc:
        print("FETCH_FAIL", exc)
        return 1
    print("fetched", args.id, "->", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
