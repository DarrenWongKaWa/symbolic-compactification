"""Regression gates for the portable-skill red-team findings.

These tests encode the intended *fixed* behaviour. A green run means the
reported bypasses are blocked, not that the whole engine is certified.
"""
from __future__ import annotations

import gzip
import importlib.util
import io
import json
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "symbolic-compactification" / "scripts"


def load_script(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"ssc_gate_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def check_mod():
    return load_script("check_audit")


@pytest.fixture(scope="module")
def inventory_mod():
    return load_script("inventory")


@pytest.fixture(scope="module")
def fetch_mod():
    return load_script("fetch_arxiv")


@pytest.fixture(scope="module")
def render_mod():
    return load_script("render")


def base_audit() -> dict:
    return {
        "paper": {
            "id": "synthetic",
            "title": "Synthetic boundary test",
            "source": "local",
            "authors": "Audit",
        },
        "inventory": {
            "equations": [
                {"id": "M-1", "public": "(1)", "section": "main", "cue": "sqrt(x**2)"},
                {"id": "M-2", "public": "(2)", "section": "main", "cue": "x"},
            ]
        },
        "claims": [],
        "edges": [
            {
                "id": "E-1",
                "from_eq": "(1)",
                "to_eq": "(2)",
                "transformation": "identity for all real x",
                "status": "GAP",
                "assumptions": [],
                "locator": "synthetic:1",
                "central": True,
            }
        ],
        "reviewer_obligations": [],
    }


def _errors(check_mod, mutate) -> list[str]:
    data = base_audit()
    mutate(data)
    return check_mod.check(data)


def test_c01_exact_without_receipt_is_rejected(check_mod):
    err = _errors(check_mod, lambda d: d["edges"][0].update(status="EXACT"))
    assert err, "EXACT without a bound engine receipt must not pass"


def test_c02_conditional_exact_without_assumptions_or_receipt_is_rejected(check_mod):
    err = _errors(
        check_mod,
        lambda d: d["edges"][0].update(status="EXACT_IF_ASSUMPTIONS"),
    )
    assert err


def test_c03_uppercase_asymptotic_cannot_be_exact(check_mod):
    err = _errors(
        check_mod,
        lambda d: d["edges"][0].update(
            status="EXACT", transformation="ASYMPTOTIC expansion"
        ),
    )
    assert err


def test_c04_remainder_claim_cannot_be_exact(check_mod):
    err = _errors(
        check_mod,
        lambda d: d.update(
            claims=[
                {
                    "id": "C1",
                    "status": "EXACT",
                    "statement": (
                        "The omitted remainder is O(Gamma) uniformly in momentum."
                    ),
                    "supporting_equations": ["(2)"],
                    "assumptions": [],
                    "unresolved": [],
                }
            ]
        ),
    )
    assert err


def test_c05_unknown_equation_numbers_rejected(check_mod):
    err = _errors(
        check_mod,
        lambda d: d["edges"][0].update(from_eq="(999)", to_eq="(888)"),
    )
    assert any("999" in e or "888" in e or "unknown" in e.lower() for e in err)


def test_c06_duplicate_edge_ids_rejected(check_mod):
    err = _errors(
        check_mod,
        lambda d: d["edges"].append(dict(d["edges"][0], status="NONZERO_RESIDUAL")),
    )
    assert any("duplicate" in e.lower() for e in err)


def test_c07_exact_claim_cannot_rest_on_nonzero_edge(check_mod):
    def mutate(d):
        d["edges"][0].update(status="NONZERO_RESIDUAL")
        d["claims"] = [
            {
                "id": "C1",
                "status": "EXACT",
                "statement": "Central result proven",
                "supporting_equations": ["(2)"],
                "unresolved": ["E-1"],
            }
        ]

    err = _errors(check_mod, mutate)
    assert err


def test_c08_fabricated_summary_rejected(check_mod):
    err = _errors(
        check_mod,
        lambda d: d.update(
            summary={
                "overall_state": "FULLY_VERIFIED",
                "machine_certified_edges": 999,
                "unresolved_load_bearing": 0,
            }
        ),
    )
    assert err


def test_c09_empty_submitted_ledger_rejected(check_mod):
    err = _errors(
        check_mod,
        lambda d: d.update(
            paper={},
            claims=[],
            edges=[],
            inventory={"equations": []},
        ),
    )
    assert err


def test_ctrl_lowercase_asymptotic_still_blocked(check_mod):
    err = _errors(
        check_mod,
        lambda d: d["edges"][0].update(
            status="EXACT", transformation="asymptotic expansion"
        ),
    )
    assert err


def test_ctrl_unknown_status_blocked(check_mod):
    err = _errors(
        check_mod, lambda d: d["edges"][0].__setitem__("status", "MADE_UP_STATUS")
    )
    assert err


def test_dummy_receipt_cannot_green_a_gap_claim(check_mod):
    data = base_audit()
    data["claims"] = [
        {
            "id": "C1",
            "status": "EXACT",
            "statement": "Central result proven",
            "supporting_equations": ["(1)", "(2)"],
            "unresolved": [],
        }
    ]
    data["certification"] = {
        "issuer": "scripts/certify.py",
        "receipts": {"dummy": {"verdict": "ZERO"}},
    }
    assert check_mod.check(data)


def test_xx_receipt_cannot_green_sqrt_edge(check_mod):
    pytest.importorskip("symbolic_compactification")
    ledger = load_script("ledger")
    verify = ledger.load_verify_equivalent()
    taut = verify(
        "x",
        "x",
        [{"name": "x", "real": True, "nonzero": False}],
    )
    assert taut.verdict == "ZERO"
    data = base_audit()
    data["edges"][0].update(status="EXACT")
    data["certification"] = {
        "issuer": "scripts/certify.py",
        "receipts": {
            "E-1": ledger.make_receipt(
                edge_id="E-1",
                lhs="x",
                rhs="x",
                assumptions=[],
                symbols=[{"name": "x", "real": True, "nonzero": False}],
                domain="",
                kind="",
                verdict="ZERO",
                residual="0",
                from_eq="(1)",
                to_eq="(2)",
            )
        },
    }
    err = check_mod.check(data)
    assert err, "a ZERO receipt for x=x must not certify sqrt(x**2)=x"


def test_certify_overwrites_model_exact_without_engine_payload():
    certify = load_script("certify")
    data = base_audit()
    data["edges"][0]["status"] = "EXACT"
    out = certify.certify(data)
    assert out["edges"][0]["status"] != "EXACT"
    assert out["edges"][0]["status"] in {"GAP", "NONZERO_RESIDUAL", "UNCERTIFIED"}


def test_compiled_identity_is_allowed_as_exact(check_mod):
    pytest.importorskip("symbolic_compactification")
    ledger = load_script("ledger")
    verify = ledger.load_verify_equivalent()
    assert verify is not None
    lhs = "x**2 + 2*x + 1"
    rhs = "(x + 1)**2"
    symbols = [{"name": "x", "real": True, "nonzero": False}]
    result = verify(lhs, rhs, symbols)
    assert result.verdict == "ZERO"
    data = base_audit()
    data["edges"][0].update(
        {
            "status": "EXACT",
            "lhs": lhs,
            "rhs": rhs,
            "symbols": symbols,
            "transformation": "factor",
        }
    )
    data["certification"] = {
        "issuer": "scripts/certify.py",
        "receipts": {
            "E-1": ledger.make_receipt(
                edge_id="E-1",
                lhs=lhs,
                rhs=rhs,
                assumptions=[],
                symbols=symbols,
                domain="",
                kind="",
                verdict=result.verdict,
                residual=result.residual,
                from_eq="(1)",
                to_eq="(2)",
                from_source_hash=ledger.equation_source_hash(data, "(1)"),
                to_source_hash=ledger.equation_source_hash(data, "(2)"),
            )
        },
    }
    data["summary"] = ledger.compute_summary(data)
    assert check_mod.check(data) == []


def test_inventory_source_change_invalidates_old_receipt(check_mod):
    pytest.importorskip("symbolic_compactification")
    ledger = load_script("ledger")
    verify = ledger.load_verify_equivalent()
    lhs = "x**2 + 2*x + 1"
    rhs = "(x + 1)**2"
    symbols = [{"name": "x", "real": True, "nonzero": False}]
    result = verify(lhs, rhs, symbols)
    data = base_audit()
    data["inventory"]["equations"][1]["tex"] = lhs
    data["inventory"]["equations"][1]["cue"] = lhs
    data["edges"][0].update(
        status="EXACT", lhs=lhs, rhs=rhs, symbols=symbols, transformation="factor"
    )
    data["certification"] = {
        "issuer": "scripts/certify.py",
        "receipts": {
            "E-1": ledger.make_receipt(
                edge_id="E-1",
                lhs=lhs,
                rhs=rhs,
                assumptions=[],
                symbols=symbols,
                domain="",
                kind="",
                verdict=result.verdict,
                residual=result.residual,
                from_eq="(1)",
                to_eq="(2)",
                from_source_hash=ledger.equation_source_hash(data, "(1)"),
                to_source_hash=ledger.equation_source_hash(data, "(2)"),
            )
        },
    }
    assert check_mod.check(data) == []
    data["inventory"]["equations"][1]["tex"] = "x**2 + 2*x"
    data["inventory"]["equations"][1]["cue"] = "x**2 + 2*x"
    data["inventory"]["equations"][1]["tex_sha256"] = "deadbeef"
    err = check_mod.check(data)
    assert any("source" in e.lower() for e in err)


def test_domain_change_invalidates_old_receipt(check_mod):
    pytest.importorskip("symbolic_compactification")
    ledger = load_script("ledger")
    verify = ledger.load_verify_equivalent()
    lhs = "x**2 + 2*x + 1"
    rhs = "(x + 1)**2"
    symbols = [{"name": "x", "real": True, "nonzero": False}]
    result = verify(lhs, rhs, symbols)
    data = base_audit()
    data["edges"][0].update(
        status="EXACT",
        lhs=lhs,
        rhs=rhs,
        symbols=symbols,
        domain="reals",
        kind="ALGEBRAIC_EQUIVALENCE",
    )
    data["certification"] = {
        "issuer": "scripts/certify.py",
        "receipts": {
            "E-1": ledger.make_receipt(
                edge_id="E-1",
                lhs=lhs,
                rhs=rhs,
                assumptions=[],
                symbols=symbols,
                domain="reals",
                kind="ALGEBRAIC_EQUIVALENCE",
                verdict=result.verdict,
                residual=result.residual,
                from_eq="(1)",
                to_eq="(2)",
                from_source_hash=ledger.equation_source_hash(data, "(1)"),
                to_source_hash=ledger.equation_source_hash(data, "(2)"),
            )
        },
    }
    assert check_mod.check(data) == []
    data["edges"][0]["domain"] = "complex"
    err = check_mod.check(data)
    assert any("domain" in e.lower() for e in err)


def test_textual_claim_cannot_inherit_exact_from_related_edge(check_mod):
    pytest.importorskip("symbolic_compactification")
    ledger = load_script("ledger")
    verify = ledger.load_verify_equivalent()
    lhs = "x**2 + 2*x + 1"
    rhs = "(x + 1)**2"
    symbols = [{"name": "x", "real": True, "nonzero": False}]
    result = verify(lhs, rhs, symbols)
    data = base_audit()
    data["edges"][0].update(
        status="EXACT", lhs=lhs, rhs=rhs, symbols=symbols, transformation="factor"
    )
    data["claims"] = [
        {
            "id": "C1",
            "status": "EXACT",
            "statement": "1 = 2",
            "supporting_equations": ["(2)"],
            "unresolved": [],
        }
    ]
    data["certification"] = {
        "issuer": "scripts/certify.py",
        "receipts": {
            "E-1": ledger.make_receipt(
                edge_id="E-1",
                lhs=lhs,
                rhs=rhs,
                assumptions=[],
                symbols=symbols,
                domain="",
                kind="",
                verdict=result.verdict,
                residual=result.residual,
                from_eq="(1)",
                to_eq="(2)",
                from_source_hash=ledger.equation_source_hash(data, "(1)"),
                to_source_hash=ledger.equation_source_hash(data, "(2)"),
            )
        },
    }
    data["summary"] = ledger.compute_summary(data)
    err = check_mod.check(data)
    assert any("textual" in e.lower() or "prose" in e.lower() for e in err)
    certify = load_script("certify")
    out = certify.certify(data)
    assert out["claims"][0]["status"] != "EXACT"


def test_render_check_refuses_unearned_exact(tmp_path, render_mod):
    data = base_audit()
    data["edges"][0]["status"] = "EXACT"
    audit = tmp_path / "audit.json"
    audit.write_text(json.dumps(data), encoding="utf-8")
    out = tmp_path / "out"
    import subprocess
    import sys

    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "render.py"),
            "--audit",
            str(audit),
            "--out",
            str(out),
            "--check",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "EVIDENCE_FAIL" in proc.stdout
    assert not (out / "audit.html").exists()


def test_gap_fixture_without_machine_green_still_passes(check_mod):
    fixture = ROOT / "tests" / "fixtures" / "skill" / "mini_audit.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))
    assert check_mod.check(data) == []


def test_forged_zero_receipt_for_sqrt_x2_is_rejected_on_recompute(check_mod):
    data = base_audit()
    data["edges"][0].update(
        {
            "status": "EXACT",
            "lhs": "sqrt(x**2)",
            "rhs": "x",
            "symbols": [{"name": "x", "real": True, "nonzero": False}],
        }
    )
    payload = {
        "edge_id": "E-1",
        "lhs": "sqrt(x**2)",
        "rhs": "x",
        "assumptions": [],
        "symbols": [{"name": "x", "real": True, "nonzero": False}],
        "domain": "reals",
        "verdict": "ZERO",
        "residual": "0",
        "engine": {"name": "forged", "engine_version": "0", "package_version": "0"},
    }
    pytest.importorskip("symbolic_compactification")
    ledger = load_script("ledger")
    payload["input_hash"] = ledger.binding_hash(payload)
    data["certification"] = {
        "issuer": "scripts/certify.py",
        "receipts": {"E-1": payload},
    }
    err = check_mod.check(data)
    assert err, "a forged ZERO receipt must lose to independent recomputation"


# --------------------------------------------------------------------------- #
# Inventory
# --------------------------------------------------------------------------- #


def _inventory_rows(inventory_mod, tex: str, extra: dict[str, str] | None = None):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        if extra:
            for name, body in extra.items():
                (root / name).write_text(body, encoding="utf-8")
        main = root / "main.tex"
        main.write_text(tex, encoding="utf-8")
        return inventory_mod.inventory(main)


def test_i01_multline_is_one_equation(inventory_mod):
    data = _inventory_rows(
        inventory_mod, r"\begin{multline} a+b \\ +c=d \end{multline}"
    )
    assert len(data["equations"]) == 1
    assert data["equations"][0]["public"] == "(1)"


def test_i02_equation_with_aligned_is_one_equation(inventory_mod):
    data = _inventory_rows(
        inventory_mod,
        r"\begin{equation}\begin{aligned} a&=b\\c&=d\end{aligned}\end{equation}",
    )
    assert len(data["equations"]) == 1


def test_i03_notag_row_is_not_counted(inventory_mod):
    data = _inventory_rows(
        inventory_mod, r"\begin{align} a&=b\notag\\c&=d\end{align}"
    )
    assert len(data["equations"]) == 1
    assert data["equations"][0]["public"] == "(1)"


def test_i04_explicit_tag_is_preserved(inventory_mod):
    data = _inventory_rows(
        inventory_mod, r"\begin{equation} a=b\tag{42}\end{equation}"
    )
    assert len(data["equations"]) == 1
    assert data["equations"][0]["public"] == "(42)"


def test_i05_input_is_followed(inventory_mod):
    data = _inventory_rows(
        inventory_mod,
        r"\input{body.tex}",
        extra={"body.tex": r"\begin{equation}a=b\end{equation}"},
    )
    assert len(data["equations"]) == 1


def test_i06_subequations_use_letter_suffixes(inventory_mod):
    data = _inventory_rows(
        inventory_mod,
        r"\begin{subequations}\begin{align} a&=b\\c&=d\end{align}\end{subequations}",
    )
    publics = [row["public"] for row in data["equations"]]
    assert publics == ["(1a)", "(1b)"]


def test_i07_setcounter_is_honoured(inventory_mod):
    data = _inventory_rows(
        inventory_mod,
        r"\setcounter{equation}{9}\begin{equation}a=b\end{equation}",
    )
    assert len(data["equations"]) == 1
    assert data["equations"][0]["public"] == "(10)"


def test_i08_verbatim_is_not_inventory(inventory_mod):
    data = _inventory_rows(
        inventory_mod,
        "\\begin{verbatim}\n\\begin{equation}a=b\\end{equation}\n\\end{verbatim}",
    )
    assert data["equations"] == []


def test_i09_long_formulas_keep_full_tex(inventory_mod):
    prefix = "a=" + "x+" * 130
    a = _inventory_rows(inventory_mod, r"\begin{equation}" + prefix + "1" + r"\end{equation}")
    b = _inventory_rows(inventory_mod, r"\begin{equation}" + prefix + "2" + r"\end{equation}")
    assert a["equations"][0]["tex"] != b["equations"][0]["tex"]
    assert a["equations"][0]["tex_sha256"] != b["equations"][0]["tex_sha256"]


def test_ctrl_simple_equation_count(inventory_mod):
    data = _inventory_rows(inventory_mod, r"\begin{equation}a=b\end{equation}")
    assert len(data["equations"]) == 1
    assert data["equations"][0]["public"] == "(1)"


def test_inventory_marks_partial_coverage_on_unresolved_include(inventory_mod):
    data = _inventory_rows(inventory_mod, r"\input{missing-file.tex}")
    assert data["coverage"]["status"] == "partial"
    assert data["coverage"]["files_missing"]


# --------------------------------------------------------------------------- #
# Fetch / extract
# --------------------------------------------------------------------------- #


def _fetch_bytes(fetch_mod, payload: bytes, dest: Path):
    with patch.object(
        fetch_mod.urllib.request, "urlopen", return_value=io.BytesIO(payload)
    ):
        return fetch_mod.fetch("2604.04520v1", dest)


def test_f01_archive_traversal_stays_inside_dest(fetch_mod, tmp_path):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        info = tarfile.TarInfo("../../ESCAPED_CANARY.txt")
        data = b"harmless local audit canary\n"
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    dest = tmp_path / "manuscript"
    with pytest.raises(Exception):
        _fetch_bytes(fetch_mod, buf.getvalue(), dest)
    assert not (tmp_path / "ESCAPED_CANARY.txt").exists()
    assert not (dest / "ESCAPED_CANARY.txt").exists()


def test_f02_html_error_page_is_not_saved_as_pdf(fetch_mod, tmp_path):
    dest = tmp_path / "html"
    dest.mkdir()
    kept = dest / "src"
    kept.mkdir()
    (kept / "old.tex").write_text("KEEP", encoding="utf-8")
    with pytest.raises(Exception):
        _fetch_bytes(
            fetch_mod,
            b"<!doctype html><html>Rate limit page</html>",
            dest,
        )
    assert not (dest / "paper.pdf").exists()
    assert (kept / "old.tex").read_text(encoding="utf-8") == "KEEP"


def test_f03_gzipped_tex_is_not_mislabeled_pdf(fetch_mod, tmp_path):
    payload = gzip.compress(
        br"\documentclass{article}\begin{document}source\end{document}"
    )
    dest = tmp_path / "gz"
    path = _fetch_bytes(fetch_mod, payload, dest)
    assert path.suffix != ".pdf" or path.read_bytes().startswith(b"%PDF-")
    tex_files = list(dest.rglob("*.tex"))
    assert tex_files, "gzipped TeX must be stored as TeX"
    assert not any(p.name == "paper.pdf" for p in dest.rglob("*") if p.is_file())


def test_f04_second_fetch_does_not_keep_stale_source(fetch_mod, tmp_path):
    def tar_payload(mapping):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tf:
            for name, content in mapping.items():
                info = tarfile.TarInfo(name)
                info.size = len(content)
                tf.addfile(info, io.BytesIO(content))
        return buf.getvalue()

    dest = tmp_path / "stale"
    _fetch_bytes(fetch_mod, tar_payload({"old.tex": b"OLD"}), dest)
    _fetch_bytes(fetch_mod, tar_payload({"new.tex": b"NEW"}), dest)
    names = sorted(p.name for p in (dest / "src").rglob("*") if p.is_file())
    assert names == ["new.tex"]


# --------------------------------------------------------------------------- #
# Render fidelity
# --------------------------------------------------------------------------- #


def test_r01_presentation_cannot_drop_central_nonzero_edge(render_mod):
    data = base_audit()
    data["edges"].append(
        dict(data["edges"][0], id="E-BAD", status="NONZERO_RESIDUAL", central=True)
    )
    data["presentation"] = {"central_edge_ids": ["E-1"]}
    ids = render_mod.central_edge_ids(data)
    assert "E-BAD" in ids


def test_r02_presentation_cannot_replace_claim_or_hide_assumptions(render_mod):
    data = base_audit()
    claim = {
        "id": "C1",
        "statement": "Only if x is positive",
        "status": "EXACT_IF_ASSUMPTIONS",
        "assumptions": ["x>0"],
    }
    data["presentation"] = {
        "claims": {"C1": {"line": "True for every real x", "assumptions": None}}
    }
    view = render_mod.claim_view(claim, data)
    assert view["line"] == "Only if x is positive"
    assert view["assumptions"] is not None
    assert "x>0" in view["assumptions"]


def test_cases_environment_keeps_row_breaks(render_mod):
    cue = r"\begin{cases} x & x>0 \\ -x & x\leq 0 \end{cases}"
    display = render_mod.display_cue(cue)
    assert r"\\" in display
    assert r"\begin{cases}" in display
    assert "tex-fallback" in display
    fallback = display[display.find('class="tex-fallback"') :]
    assert r"\\" in fallback
    assert r"\begin{cases}" in fallback
    assert "&amp;" in fallback or "&" in fallback


def test_r03_truncated_fraction_is_not_rewritten_into_another_equation(render_mod):
    cue = r"a=b+\frac{c}{"
    display = render_mod.display_cue(cue)
    assert "frac" in display
    assert "INCOMPLETE_SOURCE" in display or "tex-incomplete" in display
    assert display.count("a=b</") == 0


def test_r04_cited_rule_is_not_machine_discharged(render_mod):
    assert "CITED_RULE" not in render_mod.DISCHARGED
    assert "STRUCTURAL" not in render_mod.DISCHARGED
    assert "EXACT" in render_mod.DISCHARGED
