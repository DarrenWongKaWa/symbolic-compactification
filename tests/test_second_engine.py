"""Opt-in independent second engine (Wolfram): unit + integration tests.

Unit tests never touch a real Wolfram installation: discovery, the process
runner and the check itself are monkeypatched, or a tiny fake
``wolframscript`` shell script is used.  Integration tests at the bottom run
only when a usable ``wolframscript`` is found and otherwise SKIP (never
fail) -- including when it is installed but not activated.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
from pathlib import Path

import pytest

import symbolic_compactification.cli as cli
from symbolic_compactification import (NONZERO, UNKNOWN, ZERO,
                                       VerificationResult, verify_equivalent,
                                       verify_hypothesis)
from symbolic_compactification import second_engine as se
from symbolic_compactification.research_api import (
    VERIFIER_ROUTE, VERIFIER_ROUTE_WITH_SECOND_ENGINE)

pytestmark = pytest.mark.release_critical

POSIX_ONLY = pytest.mark.skipif(os.name != "posix",
                                reason="fake wolframscript is a POSIX script")
FORWARD = Path(__file__).resolve().parents[1] / "examples/forward/exact-step"
DEFAULT_RESULT_KEYS = ["verdict", "residual", "simplified_residual", "evidence",
                       "counterexample", "probes_tried", "seconds", "verifier"]


def _check(engine_verdict, reason=None, version="15.0.1"):
    record = se._blank_record(reason=reason)
    record.update(engine_verdict=engine_verdict,
                  wolfram_version=version if engine_verdict else None)
    return record


def _primary(verdict):
    return VerificationResult(verdict=verdict, residual="r",
                              simplified_residual="s", evidence=[])


@pytest.fixture
def no_wolfram_process(monkeypatch):
    """Fail loudly if anything tries to launch a process."""
    def boom(*_args, **_kwargs):
        raise AssertionError("second engine must not run")
    monkeypatch.setattr(se, "run_wolframscript", boom)
    monkeypatch.setattr(se, "find_wolframscript", boom)


@pytest.fixture
def fake_runtime(monkeypatch):
    """Mocked discovery + runner; ``calls`` records every launch."""
    state = {"stdout": "SCSE|15.0.1|ZERO", "returncode": 0, "calls": []}

    def fake_find(environ=None):
        return "/fake/wolframscript", "known_location"

    def fake_run(executable, code, timeout_seconds):
        state["calls"].append((executable, code, timeout_seconds))
        if isinstance(state["stdout"], BaseException):
            raise state["stdout"]
        return state["returncode"], state["stdout"], ""

    monkeypatch.setattr(se, "find_wolframscript", fake_find)
    monkeypatch.setattr(se, "run_wolframscript", fake_run)
    return state


def _fake_script(path: Path, body: str) -> Path:
    path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


# --------------------------------------------------------------------------- #
# default behavior is unchanged
# --------------------------------------------------------------------------- #

def test_default_verify_never_runs_second_engine(no_wolfram_process):
    result = verify_equivalent("(x + 1)**2", "x**2 + 2*x + 1", ["x"])
    assert result.verdict == ZERO
    assert result.second_engine is None
    assert list(result.to_dict()) == DEFAULT_RESULT_KEYS
    assert not any(e.get("kind", "").startswith(("independent_second",
                                                 "second_engine"))
                   for e in result.evidence)


def test_default_cli_verify_output_has_no_second_engine(
        tmp_path, capsys, no_wolfram_process):
    (tmp_path / "a.txt").write_text("(x + 1)**2", encoding="utf-8")
    (tmp_path / "b.txt").write_text("x**2 + 2*x + 1", encoding="utf-8")
    (tmp_path / "s.json").write_text('["x"]', encoding="utf-8")
    args = ["verify", "--current", str(tmp_path / "a.txt"),
            "--candidate", str(tmp_path / "b.txt"),
            "--symbols", str(tmp_path / "s.json")]
    assert cli.main(args) == cli.EXIT_ZERO
    assert "second_engine" not in capsys.readouterr().out
    assert cli.main(args + ["--json"]) == cli.EXIT_ZERO
    payload = json.loads(capsys.readouterr().out)
    assert set(payload["result"]) == set(DEFAULT_RESULT_KEYS)


# --------------------------------------------------------------------------- #
# raw text -> Wolfram Language
# --------------------------------------------------------------------------- #

def test_symbols_are_renamed_so_user_text_never_reaches_wolfram():
    code = se.build_wolfram_code("N*D + Print", "Print + D*N",
                                 ["N", "D", "Print"])
    # declared names that are Wolfram builtins are renamed (sorted: D, N,
    # Print -> scv1, scv2, scv3); no user identifier reaches the kernel
    assert ("FullSimplify[(((scv2*scv1)+scv3))==((scv3+(scv1*scv2))),"
            "Element[{scv1,scv2,scv3},Reals]]") in code
    assert "Print" not in code


@pytest.mark.parametrize("source, expected", [
    ("atan2(y, x)", "ArcTan[scv1,scv2]"),            # argument order swapped
    ("log(x, 2)", "Log[2,scv1]"),                     # base first in Wolfram
    ("Rational(-1, 3)*x", "((-1/3)*scv1)"),
    ("polygamma(0, x)", "PolyGamma[0,scv1]"),
    ("x^2", "(scv1^2)"),
    ("Abs(conjugate(x))", "Abs[Conjugate[scv1]]"),
    ("exp(I*pi) + E", "(Exp[(I*Pi)]+E)"),
])
def test_function_heads_and_operators(source, expected):
    code = se.build_wolfram_code(source, "0", ["x", "y"])
    assert expected in code


def test_surrounding_and_inner_whitespace_is_accepted():
    code = se.build_wolfram_code("  (x +\n 1) ", "1 + x", ["x"])
    assert "FullSimplify[((scv1+1))==((1+scv1))," in code


def test_declared_functions_and_symbol_domains():
    code = se.build_wolfram_code(
        "f(x, z) + w", "0",
        ["x", {"name": "w", "real": False},
         {"name": "z", "real": True, "nonzero": True}],
        functions=["f"])
    # sorted names: w -> scv1 (complex), x -> scv2, z -> scv3 (nonzero)
    assert "((scf1[scv2,scv3]+scv1))==(0)" in code
    assert "Element[{scv2,scv3},Reals]&&scv3!=0]" in code   # w stays complex


@pytest.mark.parametrize("source", [
    "x + 0.5",                       # inexact literal
    "oo",                            # infinity
    "Sum(x, (x, 1, 3))",             # structural container
    "Piecewise((x, x > 0), (0, True))",
    "Eq(x, 1)",
])
def test_constructs_outside_the_grammar_are_unsupported(source):
    with pytest.raises(se.SecondEngineUnavailable) as excinfo:
        se.build_wolfram_code(source, "x", ["x"])
    assert excinfo.value.code in {"EXPRESSION_UNSUPPORTED",
                                  "EXPRESSION_REJECTED"}


@pytest.mark.parametrize("source", [
    "__import__('os').system('true')",
    'x"]; Run["true',
    "undeclared + x",
    "",
])
def test_strict_parser_gates_the_wolfram_input(source):
    with pytest.raises(se.SecondEngineUnavailable) as excinfo:
        se.build_wolfram_code(source, "x", ["x"])
    assert excinfo.value.code == "EXPRESSION_REJECTED"


def test_oversized_wolfram_input_is_refused(monkeypatch):
    monkeypatch.setattr(se, "MAX_WOLFRAM_CODE_CHARS", 50)
    with pytest.raises(se.SecondEngineUnavailable) as excinfo:
        se.build_wolfram_code("x + 1", "x + 1", ["x"])
    assert excinfo.value.code == "WOLFRAM_INPUT_TOO_LARGE"


# --------------------------------------------------------------------------- #
# verdict combination: never promote, fail closed on conflict
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("primary, engine, status", [
    (ZERO, ZERO, se.AGREE), (NONZERO, NONZERO, se.AGREE),
    (ZERO, NONZERO, se.DISAGREE), (NONZERO, ZERO, se.DISAGREE),
    (ZERO, UNKNOWN, se.INCONCLUSIVE), (UNKNOWN, ZERO, se.INCONCLUSIVE),
    (UNKNOWN, NONZERO, se.INCONCLUSIVE), (UNKNOWN, UNKNOWN, se.INCONCLUSIVE),
    (ZERO, None, se.UNAVAILABLE), (UNKNOWN, None, se.UNAVAILABLE),
])
def test_compare_verdicts(primary, engine, status):
    assert se.compare_verdicts(primary, engine) == status


@pytest.mark.parametrize("require", [False, True])
@pytest.mark.parametrize("engine", [ZERO, NONZERO, UNKNOWN, None])
@pytest.mark.parametrize("primary", [ZERO, NONZERO, UNKNOWN])
def test_second_engine_never_promotes(primary, engine, require):
    before = _primary(primary)
    after = se.apply_second_engine(before, _check(engine), require=require)
    assert before.verdict == primary and before.second_engine is None
    assert after.verdict in (primary, UNKNOWN)
    if after.verdict == ZERO:
        assert primary == ZERO and engine != NONZERO
        if require:
            assert engine == ZERO
    assert after.second_engine["final_verdict"] == after.verdict
    assert after.evidence[0]["kind"] == "independent_second_engine"


def test_disagreement_downgrades_zero_to_unknown():
    after = se.apply_second_engine(_primary(ZERO), _check(NONZERO))
    assert after.verdict == UNKNOWN
    assert after.second_engine["status"] == se.DISAGREE
    assert after.second_engine["fail_closed_reason"] == "SECOND_ENGINE_DISAGREES"
    assert {"kind": "second_engine_fail_closed", "primary_verdict": ZERO,
            "reason": "SECOND_ENGINE_DISAGREES"} in after.evidence


def test_disagreement_also_withholds_nonzero():
    after = se.apply_second_engine(_primary(NONZERO), _check(ZERO))
    assert after.verdict == UNKNOWN


def test_require_downgrades_unconfirmed_zero():
    unavailable = _check(None, reason="WOLFRAM_NOT_FOUND")
    kept = se.apply_second_engine(_primary(ZERO), unavailable)
    assert kept.verdict == ZERO and kept.second_engine["status"] == se.UNAVAILABLE
    required = se.apply_second_engine(_primary(ZERO), unavailable, require=True)
    assert required.verdict == UNKNOWN
    assert (required.second_engine["fail_closed_reason"]
            == "SECOND_ENGINE_CONFIRMATION_REQUIRED")
    confirmed = se.apply_second_engine(_primary(ZERO), _check(ZERO),
                                       require=True)
    assert confirmed.verdict == ZERO


# --------------------------------------------------------------------------- #
# the check with a mocked runtime
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("stdout, verdict, reason", [
    ("SCSE|15.0.1|ZERO\n", ZERO, None),
    ("SCSE|14.1.0|NONZERO", NONZERO, None),
    ("SCSE|14.1.0|UNDECIDED", UNKNOWN, "WOLFRAM_UNDECIDED"),
    ("SCSE|14.1.0|TIMEOUT", UNKNOWN, "WOLFRAM_TIME_CONSTRAINT"),
    ("Please activate your Wolfram Engine", None, "WOLFRAM_OUTPUT_UNRECOGNIZED"),
    ("Power::infy: ...\nSCSE|14.1.0|ZERO", None, "WOLFRAM_OUTPUT_UNRECOGNIZED"),
    ("SCSE|14.1.0|ZERO|extra", None, "WOLFRAM_OUTPUT_UNRECOGNIZED"),
])
def test_output_parsing_is_strict(fake_runtime, stdout, verdict, reason):
    fake_runtime["stdout"] = stdout
    record = se.wolfram_zero_check("x", "x", ["x"])
    assert record["engine_verdict"] == verdict
    assert record["reason"] == reason
    assert record["discovery"] == "known_location"
    assert len(record["wolfram_input_sha256"]) == 64


def test_process_failures_are_unavailable(fake_runtime):
    fake_runtime["returncode"] = 1
    assert se.wolfram_zero_check("x", "x", ["x"])["reason"] == \
        "WOLFRAM_PROCESS_FAILED"
    fake_runtime["returncode"] = 0
    fake_runtime["stdout"] = se.SecondEngineUnavailable("WOLFRAM_TIMEOUT")
    assert se.wolfram_zero_check("x", "x", ["x"])["reason"] == "WOLFRAM_TIMEOUT"
    fake_runtime["stdout"] = RuntimeError("unexpected")
    record = se.wolfram_zero_check("x", "x", ["x"])
    assert record["engine_verdict"] is None
    assert record["reason"] == "SECOND_ENGINE_INTERNAL_ERROR"


def test_unsupported_expression_never_launches(fake_runtime):
    record = se.wolfram_zero_check("x + 0.5", "x", ["x"])
    assert record["reason"] == "EXPRESSION_UNSUPPORTED"
    assert fake_runtime["calls"] == []


def test_invalid_timeout_is_unavailable(fake_runtime):
    for bad in (0, -1, True, "10"):
        assert se.wolfram_zero_check("x", "x", ["x"], timeout_seconds=bad)[
            "reason"] == "SECOND_ENGINE_TIMEOUT_INVALID"
    assert fake_runtime["calls"] == []


def test_verify_equivalent_records_second_engine(fake_runtime):
    fake_runtime["stdout"] = "SCSE|15.0.1|ZERO"
    result = verify_equivalent("(x + 1)**2", "x**2 + 2*x + 1", ["x"],
                               second_engine="wolfram")
    assert result.verdict == ZERO
    assert result.second_engine["status"] == se.AGREE
    assert result.to_dict()["second_engine"]["engine_verdict"] == ZERO
    assert result.evidence[-1] == {
        "kind": "independent_second_engine", "engine": "wolfram",
        "status": "agree", "engine_verdict": ZERO, "reason": None}
    executable, code, timeout = fake_runtime["calls"][0]
    assert executable == "/fake/wolframscript"
    assert timeout == se.DEFAULT_TIMEOUT_SECONDS
    assert "FullSimplify" in code


def test_verify_equivalent_disagreement_is_unknown(fake_runtime):
    fake_runtime["stdout"] = "SCSE|15.0.1|NONZERO"
    result = verify_equivalent("(x + 1)**2", "x**2 + 2*x + 1", ["x"],
                               second_engine="wolfram")
    assert result.verdict == UNKNOWN
    assert result.second_engine["primary_verdict"] == ZERO


def test_unknown_engine_name_is_unavailable_and_require_fails_closed(
        no_wolfram_process):
    result = verify_equivalent("x", "x", ["x"], second_engine="maple")
    assert result.verdict == ZERO
    assert result.second_engine["reason"] == "SECOND_ENGINE_UNSUPPORTED"
    strict = verify_equivalent("x", "x", ["x"], second_engine="maple",
                               require_second_engine=True)
    assert strict.verdict == UNKNOWN


def test_internal_failure_of_requested_check_is_unknown(monkeypatch):
    def broken(*_args, **_kwargs):
        raise RuntimeError("boom")
    monkeypatch.setattr(se, "verify_with_second_engine", broken)
    result = verify_equivalent("x", "x", ["x"], second_engine="wolfram")
    assert result.verdict == UNKNOWN
    assert result.evidence[0]["code"] == "SECOND_ENGINE_INTERNAL_ERROR"


def test_require_alone_implies_wolfram(fake_runtime):
    result = verify_equivalent("x", "x", ["x"], require_second_engine=True)
    assert result.second_engine["engine"] == "wolfram"
    assert result.second_engine["required"] is True
    assert result.verdict == ZERO


# --------------------------------------------------------------------------- #
# discovery
# --------------------------------------------------------------------------- #

@pytest.fixture
def no_known_locations(monkeypatch):
    monkeypatch.setattr(se, "_KNOWN_LOCATIONS", ())
    monkeypatch.setattr(se, "_KNOWN_LOCATION_GLOBS", ())


@POSIX_ONLY
def test_env_override_wins(tmp_path, no_known_locations):
    exe = _fake_script(tmp_path / "ws", "exit 0\n")
    found = se.find_wolframscript({se.WOLFRAMSCRIPT_ENV: str(exe), "PATH": ""})
    assert found == (str(exe), "env_override")


@pytest.mark.parametrize("value", ["relative/wolframscript",
                                   "/nonexistent/wolframscript"])
def test_invalid_env_override_never_falls_back(tmp_path, monkeypatch, value):
    exe = tmp_path / "wolframscript"
    exe.write_text("#!/bin/sh\n", encoding="utf-8")
    exe.chmod(0o755)
    monkeypatch.setattr(se, "_KNOWN_LOCATIONS", (str(exe),))
    with pytest.raises(se.SecondEngineUnavailable) as excinfo:
        se.find_wolframscript({se.WOLFRAMSCRIPT_ENV: value,
                               "PATH": str(tmp_path)})
    assert excinfo.value.code == "WOLFRAM_OVERRIDE_INVALID"


@POSIX_ONLY
def test_non_executable_override_is_invalid(tmp_path, no_known_locations):
    plain = tmp_path / "wolframscript"
    plain.write_text("#!/bin/sh\n", encoding="utf-8")
    plain.chmod(0o644)
    with pytest.raises(se.SecondEngineUnavailable):
        se.find_wolframscript({se.WOLFRAMSCRIPT_ENV: str(plain), "PATH": ""})


@POSIX_ONLY
def test_path_then_known_locations_then_not_found(tmp_path, monkeypatch,
                                                  no_known_locations):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    on_path = _fake_script(bindir / "wolframscript", "exit 0\n")
    assert se.find_wolframscript({"PATH": str(bindir)}) == (str(on_path), "path")

    known = _fake_script(tmp_path / "known-wolframscript", "exit 0\n")
    monkeypatch.setattr(se, "_KNOWN_LOCATIONS", (str(tmp_path / "missing"),
                                                 str(known)))
    assert se.find_wolframscript({"PATH": ""}) == (str(known), "known_location")

    monkeypatch.setattr(se, "_KNOWN_LOCATIONS", ())
    with pytest.raises(se.SecondEngineUnavailable) as excinfo:
        se.find_wolframscript({"PATH": ""})
    assert excinfo.value.code == "WOLFRAM_NOT_FOUND"
    assert se.wolfram_available({"PATH": ""}) is False


@POSIX_ONLY
def test_versioned_installs_prefer_newest(tmp_path, monkeypatch,
                                          no_known_locations):
    for version in ("9.0", "14.1", "13.3"):
        folder = tmp_path / version / "Executables"
        folder.mkdir(parents=True)
        _fake_script(folder / "wolframscript", "exit 0\n")
    monkeypatch.setattr(se, "_KNOWN_LOCATION_GLOBS",
                        (str(tmp_path / "*" / "Executables" / "wolframscript"),))
    found, how = se.find_wolframscript({"PATH": ""})
    assert how == "known_location" and "/14.1/" in found


def test_known_locations_cover_supported_installs():
    joined = "\n".join(se._KNOWN_LOCATIONS)
    for bundle in ("/Applications/Wolfram.app/", "/Applications/Wolfram Engine.app/",
                   "/Applications/Mathematica.app/"):
        assert bundle in joined


# --------------------------------------------------------------------------- #
# real subprocess path with a fake wolframscript (no Wolfram needed)
# --------------------------------------------------------------------------- #

@POSIX_ONLY
def test_code_is_one_argv_element_and_no_shell(tmp_path, monkeypatch):
    capture = tmp_path / "argv.txt"
    exe = _fake_script(
        tmp_path / "wolframscript",
        f'printf "%s" "$2" > "{capture}"\n'
        'test "$1" = "-code" || exit 9\n'
        'test "$#" -eq 2 || exit 8\n'
        'echo "SCSE|0.0|ZERO"\n')
    monkeypatch.setenv(se.WOLFRAMSCRIPT_ENV, str(exe))
    record = se.wolfram_zero_check("x*y", "y*x", ["x", "y"])
    assert record["engine_verdict"] == ZERO, record
    assert record["discovery"] == "env_override"
    sent = capture.read_text(encoding="utf-8")
    assert "$Aborted" in sent and '"SCSE"' in sent   # shell did not expand it
    assert se.hashlib.sha256(sent.encode()).hexdigest() == \
        record["wolfram_input_sha256"]


@POSIX_ONLY
def test_timeout_kills_the_owned_process_and_is_unavailable(tmp_path,
                                                             monkeypatch):
    exe = _fake_script(tmp_path / "wolframscript",
                       "sleep 30\necho 'SCSE|0.0|ZERO'\n")
    monkeypatch.setenv(se.WOLFRAMSCRIPT_ENV, str(exe))
    record = se.wolfram_zero_check("x", "x", ["x"], timeout_seconds=1)
    assert record["engine_verdict"] is None
    assert record["reason"] == "WOLFRAM_TIMEOUT"
    assert record["seconds"] < 10
    result = verify_equivalent("x", "x", ["x"])
    timed = se.apply_second_engine(result, record, require=True)
    assert timed.verdict == UNKNOWN


# --------------------------------------------------------------------------- #
# CLI and workspace provenance (mocked runtime)
# --------------------------------------------------------------------------- #

def _pair(tmp_path: Path, current: str, candidate: str) -> list[str]:
    (tmp_path / "a.txt").write_text(current, encoding="utf-8")
    (tmp_path / "b.txt").write_text(candidate, encoding="utf-8")
    (tmp_path / "s.json").write_text('["x"]', encoding="utf-8")
    return ["verify", "--current", str(tmp_path / "a.txt"),
            "--candidate", str(tmp_path / "b.txt"),
            "--symbols", str(tmp_path / "s.json")]


def test_cli_second_engine_json_and_exit_codes(tmp_path, capsys, fake_runtime):
    args = _pair(tmp_path, "(x + 1)**2", "x**2 + 2*x + 1")
    assert cli.main(args + ["--second-engine", "wolfram", "--json"]) == \
        cli.EXIT_ZERO
    payload = json.loads(capsys.readouterr().out)
    assert payload["result"]["second_engine"]["status"] == "agree"

    fake_runtime["stdout"] = "SCSE|15.0.1|NONZERO"
    assert cli.main(args + ["--second-engine", "wolfram"]) == cli.EXIT_UNKNOWN
    out = capsys.readouterr().out
    assert "verdict:             UNKNOWN" in out
    assert "second_engine:       wolfram disagree" in out
    assert "ZERO -> UNKNOWN (SECOND_ENGINE_DISAGREES)" in out

    fake_runtime["stdout"] = "SCSE|15.0.1|UNDECIDED"
    assert cli.main(args + ["--require-second-engine"]) == cli.EXIT_UNKNOWN
    assert "SECOND_ENGINE_CONFIRMATION_REQUIRED" in capsys.readouterr().out


def test_workspace_provenance_records_second_engine(tmp_path, fake_runtime):
    default_ws = tmp_path / "default"
    shutil.copytree(FORWARD, default_ws)
    plain = verify_hypothesis(default_ws)
    plain_provenance = json.loads(plain.provenance_path.read_text())
    assert plain_provenance["verifier_route"] == VERIFIER_ROUTE
    assert plain_provenance["warnings"] == []
    assert "second_engine" not in plain.result_path.read_text()
    assert fake_runtime["calls"] == []

    ws = tmp_path / "second"
    shutil.copytree(FORWARD, ws)
    fake_runtime["stdout"] = "SCSE|15.0.1|UNDECIDED"
    run = verify_hypothesis(ws, second_engine="wolfram")
    assert run.result == ZERO
    provenance = json.loads(run.provenance_path.read_text())
    assert provenance["verifier_route"] == VERIFIER_ROUTE_WITH_SECOND_ENGINE
    assert provenance["warnings"] == [
        "second_engine:wolfram:inconclusive:factorization-equivalence:"
        "WOLFRAM_UNDECIDED"]
    stored = json.loads(run.result_path.read_text())
    assert stored["verifier_route"] == VERIFIER_ROUTE_WITH_SECOND_ENGINE
    assert stored["obligations"][0]["verification"]["second_engine"][
        "status"] == "inconclusive"
    assert "Independent second engine" in run.report_path.read_text()

    strict_ws = tmp_path / "strict"
    shutil.copytree(FORWARD, strict_ws)
    strict = verify_hypothesis(strict_ws, require_second_engine=True)
    assert strict.result == UNKNOWN


def test_workspace_cli_prints_second_engine(tmp_path, capsys, fake_runtime):
    ws = tmp_path / "ws"
    shutil.copytree(FORWARD, ws)
    assert cli.main(["verify", str(ws), "--second-engine", "wolfram"]) == \
        cli.EXIT_ZERO
    assert "  second engine: wolfram agree" in capsys.readouterr().out
    plain = tmp_path / "plain"
    shutil.copytree(FORWARD, plain)
    assert cli.main(["verify", str(plain)]) == cli.EXIT_ZERO
    assert "second engine" not in capsys.readouterr().out


# --------------------------------------------------------------------------- #
# integration: real Wolfram (SKIPPED when missing or not activated)
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def real_wolfram():
    if not se.wolfram_available():
        pytest.skip("wolframscript not found (set "
                    f"{se.WOLFRAMSCRIPT_ENV} or install Wolfram Engine)")
    probe = se.wolfram_zero_check("x + 1", "1 + x", ["x"])
    if probe["engine_verdict"] != ZERO:
        pytest.skip("wolframscript found but not usable "
                    f"({probe['reason']}; activation/licensing?)")
    return probe


@pytest.mark.wolfram_integration
@pytest.mark.parametrize("current, candidate, symbols", [
    ("sin(x)**2 + cos(x)**2", "1", ["x"]),
    ("(x + 1)**2", "x**2 + 2*x + 1", ["x"]),
    ("cosh(x)**2 - sinh(x)**2", "1", ["x"]),
    ("sqrt(x**2)", "Abs(x)", ["x"]),
    ("tan(x)", "sin(x)/cos(x)", ["x"]),
])
def test_real_wolfram_confirms_known_zero(real_wolfram, current, candidate,
                                          symbols):
    result = verify_equivalent(current, candidate, symbols,
                               require_second_engine=True)
    assert result.second_engine["engine_verdict"] == ZERO, result.second_engine
    assert result.second_engine["status"] == se.AGREE
    assert result.verdict == ZERO


@pytest.mark.wolfram_integration
@pytest.mark.parametrize("current, candidate", [
    ("x", "x + 1"),
    ("(x + 1)**2", "x**2 + 2*x"),
])
def test_real_wolfram_confirms_known_nonzero(real_wolfram, current, candidate):
    result = verify_equivalent(current, candidate, ["x"],
                               second_engine="wolfram")
    assert result.verdict == NONZERO
    assert result.second_engine["engine_verdict"] == NONZERO
    assert result.second_engine["status"] == se.AGREE


@pytest.mark.wolfram_integration
def test_real_wolfram_partial_equality_is_inconclusive(real_wolfram):
    # sin(x) == cos(x) holds at isolated points: FullSimplify cannot say
    # False, so the second engine stays UNKNOWN; the primary NONZERO stands.
    result = verify_equivalent("sin(x)", "cos(x)", ["x"],
                               second_engine="wolfram")
    assert result.verdict == NONZERO
    assert result.second_engine["status"] == se.INCONCLUSIVE


@pytest.mark.wolfram_integration
def test_real_wolfram_cli(real_wolfram, tmp_path, capsys):
    args = _pair(tmp_path, "sin(x)**2 + cos(x)**2", "1")
    assert cli.main(args + ["--second-engine", "wolfram", "--json"]) == \
        cli.EXIT_ZERO
    second = json.loads(capsys.readouterr().out)["result"]["second_engine"]
    assert second["status"] == "agree"
    assert second["wolfram_version"]
