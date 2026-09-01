"""Guard public derivation-audit docs against forbidden product claims."""
from __future__ import annotations

from pathlib import Path

import pytest

from symbolic_compactification.audit.schema import FORBIDDEN_PUBLIC_CLAIMS

pytestmark = pytest.mark.derivation_audit_release_critical

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
AUDIT_DOC = ROOT / "docs" / "paper-audit.md"


def test_readme_and_derivation_audit_omit_forbidden_claims():
    readme = README.read_text(encoding="utf-8")
    audit = AUDIT_DOC.read_text(encoding="utf-8")
    blob = f"{readme}\n{audit}".lower()
    for claim in FORBIDDEN_PUBLIC_CLAIMS:
        assert claim.lower() not in blob, claim


def test_derivation_audit_contains_approved_machine_claim_fragment():
    text = AUDIT_DOC.read_text(encoding="utf-8")
    assert "Only obligations returning exact ZERO" in text
