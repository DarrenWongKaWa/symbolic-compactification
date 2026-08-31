"""Optional static HTML report for derivation-audit records."""
from __future__ import annotations

from symbolic_compactification.audit.evidence import AuditRun
from symbolic_compactification.audit.html import generate_html_report
from symbolic_compactification.audit.schema import (
    ALGEBRAIC_EQUIVALENCE,
    NONZERO,
    ZERO,
    AuditRecord,
    may_appear_in_verified_table,
)
from symbolic_compactification.audit.workspace import initialize_audit_workspace

_HASH_A = "a" * 64
_HASH_B = "b" * 64
_HASH_C = "c" * 64
_HASH_D = "d" * 64
_HASH_E = "e" * 64

_ZERO_EDGE = "E001"
_NONZERO_EDGE = "E002"
_XSS_RESIDUAL = "<script>alert(1)</script>"


def _record(**overrides) -> AuditRecord:
    base = dict(
        audit_id="audit1",
        edge_id=_ZERO_EDGE,
        source_refs=("eq:a", "eq:b"),
        edge_type=ALGEBRAIC_EQUIVALENCE,
        status=ZERO,
        result=ZERO,
        source_snapshot_hash=_HASH_A,
        engine_version="0.3.0",
        runtime_seconds=0.01,
        lhs_hash=_HASH_B,
        rhs_hash=_HASH_C,
        residual_hash=_HASH_D,
        assumptions_hash=_HASH_E,
        obligation_hash=_HASH_A,
        verifier_route="python_sympy_exact_v1",
        executable=True,
        claim="a - b",
        residual_text="a - b",
        declared_assumptions=("x real",),
    )
    base.update(overrides)
    return AuditRecord(**base)


def _section(page: str, section_id: str) -> str:
    marker = f'id="{section_id}"'
    start = page.find(marker)
    assert start != -1, f"missing section {section_id!r}"
    open_tag = page.rfind("<section", 0, start)
    close = page.find("</section>", start)
    assert open_tag != -1 and close != -1
    return page[open_tag:close + len("</section>")]


def test_html_report_verified_section_excludes_nonzero_and_escapes_residual(tmp_path):
    workspace = initialize_audit_workspace(tmp_path / "html-audit")
    zero = _record()
    nonzero = _record(
        edge_id=_NONZERO_EDGE,
        status=NONZERO,
        result=NONZERO,
        residual_text=_XSS_RESIDUAL,
        claim="<script>pwn</script>",
        source_refs=("eq:x",),
    )
    assert may_appear_in_verified_table(zero)
    assert not may_appear_in_verified_table(nonzero)
    run = AuditRun(
        run_id="run-html-1",
        audit_id="audit1",
        directory=workspace.root / "runs" / "run-html-1",
        records=(zero, nonzero),
    )

    path = generate_html_report(workspace, run)
    assert path.name == "report.html"
    assert path.parent.name == "reports"
    assert path.is_file()
    page = path.read_text(encoding="utf-8")

    verified = _section(page, "machine-verified")
    nonzero_section = _section(page, "nonzero")
    assert _ZERO_EDGE in verified
    assert _NONZERO_EDGE not in verified
    assert _NONZERO_EDGE in nonzero_section
    assert _ZERO_EDGE not in nonzero_section

    assert _XSS_RESIDUAL not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert "&lt;script&gt;pwn&lt;/script&gt;" in page
    assert "<details>" in page
    assert "<pre>" in page


def test_html_report_empty_run_writes_valid_page(tmp_path):
    workspace = initialize_audit_workspace(tmp_path / "empty-html-audit")
    run = AuditRun(
        run_id="run-empty",
        audit_id="audit-empty",
        directory=workspace.root / "runs" / "run-empty",
        records=(),
    )
    path = generate_html_report(workspace, run)
    page = path.read_text(encoding="utf-8")
    assert page.lstrip().startswith("<!DOCTYPE html>")
    assert "<html" in page
    assert "</html>" in page
    assert 'id="machine-verified"' in page
    assert 'id="reproduction"' in page
    assert "symbolic-compactification audit verify" in page
    assert _ZERO_EDGE not in page
