#!/usr/bin/env python3
"""Fail-closed first-screen check for an evidence-ledger HTML page.

The engineering layer emits Guo-like HTML. Workspace 0* is overlay only.
This script does not adjudicate mathematics.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def visible(page: str) -> str:
    return re.sub(r"<script\b[^>]*>.*?</script>", "", page, flags=re.S | re.I)


def header(page: str) -> str:
    vis = visible(page)
    parts = re.split(r'id="main"', vis, maxsplit=1)
    return parts[0]


def has_appendix_inventory(page: str) -> bool:
    vis = visible(page)
    if re.search(r"no appendix", vis, re.I):
        return False
    if re.search(r"<h2[^>]*>\s*Appendix map", vis, re.I):
        return True
    if re.search(r'id="map-sec"', vis) and re.search(r"class=\"lane\"", vis):
        return True
    if re.search(r"class=\"lane\"", vis) and re.search(r"Appendix [A-G]", vis):
        return True
    if re.search(r"main \d+ · appendix \d+", vis, re.I):
        return True
    return False


def check(page: str) -> list[str]:
    errors: list[str] = []
    vis = visible(page)
    head = header(page)
    map_details = re.search(r"<details\b[^>]*id=\"map-sec\"", page, re.I)
    map_section = re.search(r"<section\b[^>]*id=\"map-sec\"", page, re.I)
    map_any = 'id="map-sec"' in page
    appendix = has_appendix_inventory(page)

    if map_details:
        errors.append("Appendix map must be a visible <section>, not <details id=\"map-sec\">")
    if appendix:
        if not map_any:
            errors.append("appendix paper missing id=\"map-sec\"")
        elif 'id="map-sec"' not in head:
            errors.append("id=\"map-sec\" must sit on the first screen (before id=\"main\")")
        if map_any and not map_section:
            errors.append("id=\"map-sec\" must be a <section>")
        if map_section and not re.search(r'id="derivation-map"', page):
            errors.append("map-sec missing #derivation-map lanes")
        if map_section and not re.search(r'class="lane"', page):
            errors.append("map-sec has no .lane chips")
    if re.search(r"<details\b[^>]*id=\"map-sec\"", vis, re.I):
        errors.append("visible DOM still has details#map-sec")

    if re.search(r"0\*|ws-zero", page):
        errors.append("invalid 0* overlay must be absent from reviewer HTML")

    if "Presentation is not a certificate" not in page:
        errors.append("missing required copy: Presentation is not a certificate")
    if "inventoried equations" not in page:
        errors.append("missing inventoried equations cell")
    if 'id="obligation-table"' not in page:
        errors.append("missing #obligation-table")
    return errors


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("html", type=Path)
    args = p.parse_args()
    page = args.html.read_text(encoding="utf-8")
    errors = check(page)
    if errors:
        print("VERIFY_FAIL", args.html)
        for e in errors:
            print(" -", e)
        return 1
    print("VERIFY_OK", args.html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
