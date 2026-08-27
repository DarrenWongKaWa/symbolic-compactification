"""Preprocessing must not emit gold/interpretation slogans."""
from __future__ import annotations

import json

from symbolic_compactification.observations.ir import FORBIDDEN_INTERPRETATION


def assert_no_interpretation(payload) -> None:
    blob = json.dumps(payload, default=str)
    low = blob.lower()
    for tok in FORBIDDEN_INTERPRETATION:
        if tok.lower() in low:
            raise RuntimeError(f"observation interpretation leak: {tok}")
