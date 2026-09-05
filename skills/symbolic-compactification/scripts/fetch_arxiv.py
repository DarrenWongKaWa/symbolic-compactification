#!/usr/bin/env python3
"""Download an arXiv e-print (source tarball or pdf) into a directory. Stdlib only."""
from __future__ import annotations

import argparse
import tarfile
import urllib.request
from pathlib import Path

UA = "symbolic-compactification-skill/0.3.2 (scientific audit; +https://arxiv.org)"


def fetch(arxiv_id: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    aid = arxiv_id.replace("arxiv:", "").replace("https://arxiv.org/abs/", "").strip("/")
    url = f"https://arxiv.org/e-print/{aid}"
    blob = dest / "eprint"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        blob.write_bytes(resp.read())
    try:
        with tarfile.open(blob, mode="r:*") as tf:
            tf.extractall(dest / "src")
        return dest / "src"
    except tarfile.ReadError:
        pdf = dest / "paper.pdf"
        pdf.write_bytes(blob.read_bytes())
        return pdf


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, help="arXiv id, e.g. 2604.04520")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    path = fetch(args.id, args.out)
    print("fetched", args.id, "->", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
