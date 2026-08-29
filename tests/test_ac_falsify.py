"""Parameter witnesses disqualify underspecified AC contracts. Guo is sealed."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.assumption_complete_representation.audit.falsify.catalog import (  # noqa: E402
    CLEAN,
    DISQUALIFIED,
    GAP,
    GUO_ANALOGUE,
    HEADLINE_CLEAN,
    SKIPPED_REJECTED,
)
from research.assumption_complete_representation.audit.falsify.scan import (  # noqa: E402
    METHOD,
    SCREENING_PATH,
    WITNESSES_PATH,
    load_screening,
    probe_is_singular,
    run_scan,
)

AC = ROOT / "research" / "assumption_complete_representation"
FALSIFY = AC / "audit" / "falsify"
README = FALSIFY / "README.md"

DISQUALIFIED_IDS = (
    "ac-r04-lindhard-occupation-dd",
    "ac-r05-lehmann-spectral-master",
    "ac-r06-matsubara-pole-family",
    "ac-r07-lippmann-schwinger-iepsilon",
    "thermal-07-green-spectral-hilbert",
)


def _by_id(report: dict) -> dict[str, dict]:
    return {c["case_id"]: c for c in report["cases"]}


def test_screening_pool_is_forty_and_guo_not_admitted():
    blob = load_screening()
    assert blob["n_candidates"] == 40
    assert blob["n_keepers"] == 22
    assert blob["n_skeptic_flagged"] == 15
    assert blob["n_miner_rejected"] == 3
    assert blob["guo_admitted"] is False
    assert SCREENING_PATH.is_file()


def test_scan_counts():
    report = run_scan()
    pool = report["pool"]
    assert report["method"] == METHOD
    assert report["headline_clean"] == HEADLINE_CLEAN
    assert pool["n_scanned"] == 37
    assert pool["n_clean"] == 31
    assert pool["n_disqualified"] == 5
    assert pool["n_gap_only"] == 1
    assert pool["n_skipped_rejected"] == 3
    assert pool["n_skipped_guo"] == 0
    assert pool["disqualified_ids"] == list(DISQUALIFIED_IDS)
    assert pool["headline_clean_status"] == CLEAN
    assert report["probe_failures"] == []
    assert GUO_ANALOGUE["used_as_candidate"] is False
    assert GUO_ANALOGUE["atoms_loaded"] is False


def test_headline_dlmf_is_clean():
    rec = _by_id(run_scan())[HEADLINE_CLEAN]
    assert rec["status"] == CLEAN
    assert rec["disqualifies"] is False
    assert rec["witnesses"] == []
    assert rec["why_clean"]
    finite = rec["probes"]["finite"]
    assert finite
    assert all(p["sympy"]["confirmed"] for p in finite)
    y0 = next(p for p in finite if p["assignment"] == {"y": 0})
    assert y0["sympy"]["singular"] is False


def test_dlmf_z_not_integer_blocks_poles():
    rec = _by_id(run_scan())["thermal-03-digamma-reflection"]
    assert rec["status"] == CLEAN
    blocked = rec["probes"]["blocked"]
    assert blocked
    assert all(p["declared_blocks"] for p in blocked)
    assert all(p["sympy"]["singular"] and p["sympy"]["confirmed"] for p in blocked)
    finite = rec["probes"]["finite"]
    assert finite[0]["sympy"]["value"] == "0"


def test_trigamma_positive_integer_is_finite():
    rec = _by_id(run_scan())["thermal-05-trigamma-double-pole"]
    assert rec["status"] == CLEAN
    finite = rec["probes"]["finite"]
    z1 = next(p for p in finite if p["assignment"] == {"z": 1})
    assert z1["sympy"]["singular"] is False
    blocked = rec["probes"]["blocked"]
    assert any(p["assignment"] == {"z": 0} and p["sympy"]["singular"] for p in blocked)


def test_disqualified_witnesses_are_zoo():
    report = run_scan()
    by = _by_id(report)
    for cid in DISQUALIFIED_IDS:
        rec = by[cid]
        assert rec["status"] == DISQUALIFIED
        assert rec["disqualifies"] is True
        assert rec["witnesses"]
        for w in rec["witnesses"]:
            assert w["sympy"]["singular"] is True
            assert w["sympy"]["confirmed"] is True
            assert w["sympy"]["value"] == "zoo"
            assert w["kind"] in {"pole", "cut", "division_by_zero"}


def test_direct_probes_match_catalog():
    hbar0 = probe_is_singular(
        "1/(hbar*(omega + I*delta) + (hbar**2/(2*m))*((k+q)**2 - k**2))",
        {"hbar": 0, "m": 1, "delta": 1, "omega": 1, "k": 1, "q": 1},
    )
    assert hbar0["singular"] is True
    eps0 = probe_is_singular(
        "1/(E - E_beta + I*epsilon)",
        {"E": 0, "E_beta": 0, "epsilon": 0},
    )
    assert eps0["singular"] is True
    nB = probe_is_singular("1/(exp(beta*xi) - 1)", {"beta": 1, "xi": 0})
    assert nB["singular"] is True
    half = probe_is_singular("polygamma(0, Rational(1,2) + I*y)", {"y": 0})
    assert half["singular"] is False


def test_rejected_and_guo_are_not_scanned_as_candidates():
    by = _by_id(run_scan())
    for cid in (
        "ac-r08-kubo-frequency-underspecified",
        "ac-t-rej-index-rename",
        "thermal-08-matsubara-newton-dd-underspecified",
    ):
        assert by[cid]["status"] == SKIPPED_REJECTED
        assert by[cid]["witnesses"] == []
    scanned = [c["case_id"] for c in run_scan()["cases"] if c["status"] != SKIPPED_REJECTED]
    assert all("guo" not in cid.lower() for cid in scanned)


def test_sokhotski_is_gap_not_interior_witness():
    rec = _by_id(run_scan())["ac-r02-sokhotski-plemelj-boundary"]
    assert rec["status"] == GAP
    assert rec["disqualifies"] is False
    assert rec["gaps"]


def test_witnesses_json_matches_scan():
    assert WITNESSES_PATH.is_file()
    disk = json.loads(WITNESSES_PATH.read_text(encoding="utf-8"))
    live = run_scan()
    assert disk["method"] == live["method"]
    assert disk["pool"] == live["pool"]
    assert disk["headline_clean"] == HEADLINE_CLEAN
    assert disk["guo_analogue"]["atoms_loaded"] is False
    assert [c["case_id"] for c in disk["cases"]] == [c["case_id"] for c in live["cases"]]
    assert [c["status"] for c in disk["cases"]] == [c["status"] for c in live["cases"]]


def test_guo_atoms_file_not_read_by_falsifier():
    text = (FALSIFY / "scan.py").read_text(encoding="utf-8")
    cat = (FALSIFY / "catalog.py").read_text(encoding="utf-8")
    assert "FROZEN_G0016_ATOMS" not in text
    assert "FROZEN_G0016_ATOMS" not in cat
    assert "open(" not in text or "G0016" not in text
    assert GUO_ANALOGUE["atoms_loaded"] is False
    assert GUO_ANALOGUE["used_as_candidate"] is False
    readme = README.read_text(encoding="utf-8")
    assert "does **not** load" in readme
    assert "G0016" in readme


def test_readme_states_clean_case_and_guo_seal():
    text = README.read_text(encoding="utf-8")
    assert "thermal-01-fermi-im-digamma" in text
    assert "DLMF" in text
    assert "DISQUALIFIED" in text
    assert "G0016" in text
    assert "FROZEN_G0016_ATOMS.json" in text
    assert "does **not** load" in text or "does not load" in text.lower()
    assert HEADLINE_CLEAN in text
