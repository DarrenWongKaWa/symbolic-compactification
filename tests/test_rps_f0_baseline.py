from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research.representation_program_search.freeform_baseline import (
    F0_AUTHORITY_COMMIT,
    F0RunContractError,
    build_f0_prompt,
    evaluate_f0,
    run_f0,
    validate_f0_authority,
)
from research.representation_program_search.freeform_baseline.prompt import F0ContractError
from research.representation_program_search.search import load_public_case
from research.representation_program_search.search.llm_contract import (
    DeepSeekSearchConfig,
)


def _json(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _case(tmp_path: Path):
    members = []
    for index, expression in enumerate(("x + 1\n", "x**2 + 1\n"), 1):
        path = tmp_path / "members" / f"M{index}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expression, encoding="utf-8")
        members.append({
            "member_id": f"OPAQUE_{index}",
            "path": path.relative_to(tmp_path).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    symbols_sha = _json(tmp_path / "symbols.json", {"symbols": ["x"]})
    assumptions_sha = _json(tmp_path / "assumptions.json", {
        "predicates": [{
            "predicate_id": "P1", "statement": "x is real", "status": "DECLARED",
        }],
        "status": "COMPLETE",
    })
    _json(tmp_path / "proposer_view.json", {
        "assumptions": {"path": "assumptions.json", "sha256": assumptions_sha},
        "case_id": "F0_PUBLIC_CASE",
        "schema_version": "RPSProposerViewV1",
        "source_catalog": {
            "members": members,
            "symbols_path": "symbols.json",
            "symbols_sha256": symbols_sha,
        },
    })
    return load_public_case(tmp_path / "proposer_view.json")


def test_authority_matches_closed_experiment():
    root = Path(__file__).resolve().parents[1]
    assert F0_AUTHORITY_COMMIT == "0cdde49"
    assert validate_f0_authority(root) == ()


def test_prompt_uses_frozen_p0_and_deterministic_grounded_ids(tmp_path):
    prompt = build_f0_prompt(_case(tmp_path))
    payload = prompt.to_dict()
    assert prompt.condition == "P0" and prompt.result_condition == "F0"
    assert prompt.source_id_map == {"OPAQUE_1": "G0001", "OPAQUE_2": "G0002"}
    user = prompt.messages[1]["content"]
    assert "CONDITION: P0_RAW" in user
    assert "G0001" in user and "G0002" in user
    assert "x + 1" in user and "x**2 + 1" in user
    assert "STRUCTURAL OBSERVATION PACKETS" not in user
    assert payload["private_reasoning_requested"] is False


def test_prompt_never_reads_reference_or_verification(tmp_path, monkeypatch):
    case = _case(tmp_path)
    (tmp_path / "reference").mkdir()
    (tmp_path / "reference" / "program.json").write_text("gold", encoding="utf-8")
    original = Path.read_bytes

    def guarded(path, *args, **kwargs):
        if tmp_path in path.parents:
            assert "reference" not in path.parts
            assert "verification" not in path.parts
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    build_f0_prompt(case)


def test_authority_drift_fails_closed(tmp_path, monkeypatch):
    case = _case(tmp_path / "case")
    monkeypatch.setattr(
        "research.representation_program_search.freeform_baseline.prompt.validate_f0_authority",
        lambda _root: ("F0_AUTHORITY_DRIFT:x",),
    )
    with pytest.raises(F0ContractError, match="F0_AUTHORITY_DRIFT"):
        build_f0_prompt(case)


def _usage():
    return {
        "prompt_tokens": 100,
        "completion_tokens": 40,
        "total_tokens": 140,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 100,
        "completion_tokens_details": {"reasoning_tokens": 20},
    }


def _hypothesis(**extra):
    value = {
        "representation_type": "parameterized_family",
        "latent_object": "F(t)=t+1",
        "member_maps": [{"source_node_id": "G0001", "role": "instance"}],
        "operators": [{"member": "G0001", "O": "specialize"}],
        "reconstruction_rule": "G0001 = F(x)",
        "required_assumptions": ["x is real"],
        "proof_obligations": ["G0001 = F(x)"],
    }
    value.update(extra)
    return value


class _Transport:
    def __init__(self, content, *, before_call=None, error=None, message=None):
        self.content = content
        self.before_call = before_call
        self.error = error
        self.message = message
        self.calls = []

    def complete(self, request):
        self.calls.append(request)
        if self.before_call is not None:
            self.before_call()
        if self.error is not None:
            raise self.error
        return {
            "id": "request-f0",
            "model": "deepseek-v4-pro",
            "usage": _usage(),
            "choices": [{
                "finish_reason": "stop",
                "message": (
                    self.message
                    if self.message is not None
                    else {"content": self.content}
                ),
            }],
        }


def test_f0_runner_records_header_before_call_and_only_final_output(tmp_path):
    output = tmp_path / "run"
    content = json.dumps({
        "abstain": False,
        "abstain_reason": "",
        "hypotheses": [_hypothesis()],
    })
    transport = _Transport(
        content,
        before_call=lambda: (output / "run_header.json").read_bytes(),
    )

    result = run_f0(
        _case(tmp_path / "case"),
        transport=transport,
        output_directory=output,
        config=DeepSeekSearchConfig(seed_label="seed-3"),
    )

    assert result.f0_run_available is True
    assert result.provider_call_valid is True
    assert result.seed == 3 and result.seed_label == "seed-3"
    assert result.parse_status == "OK"
    assert result.final_content == content
    assert result.private_reasoning_accessed is False
    assert result.private_reasoning_persisted is False
    assert transport.calls[0]["messages"][1]["content"].startswith("CONDITION: P0_RAW")
    header = json.loads((output / "run_header.json").read_text())
    recorded = json.loads((output / "result.json").read_text())
    assert header["run_header_sha256"] == result.run_header_sha256
    assert recorded["final_content_sha256"] == hashlib.sha256(content.encode()).hexdigest()
    assert "reasoning_content" not in json.dumps(recorded)


def test_f0_malformed_final_json_is_available_method_failure(tmp_path):
    result = run_f0(
        _case(tmp_path / "case"),
        transport=_Transport("not json"),
        output_directory=tmp_path / "run",
    )
    assert result.f0_run_available is True
    assert result.parse_status == "PARSE_FAILURE"
    assert result.provider_error_code is None


def test_f0_api_failure_is_unavailable_without_fallback_or_content(tmp_path):
    result = run_f0(
        _case(tmp_path / "case"),
        transport=_Transport("", error=RuntimeError("secret provider text")),
        output_directory=tmp_path / "run",
    )
    assert result.f0_run_available is False
    assert result.provider_error_code == "API_FAILURE:RuntimeError"
    assert result.final_content is None
    assert "secret provider text" not in (tmp_path / "run/result.json").read_text()


def test_f0_rejects_private_reasoning_copied_into_final_json(tmp_path):
    content = json.dumps({
        "abstain": False,
        "hypotheses": [_hypothesis(reasoning_content="SENSITIVE_BODY_X9")],
    })
    result = run_f0(
        _case(tmp_path / "case"),
        transport=_Transport(content),
        output_directory=tmp_path / "run",
    )
    assert result.f0_run_available is False
    assert result.provider_error_code == "RESPONSE_PRIVATE_REASONING_FIELD_FORBIDDEN"
    assert result.final_content is None
    assert "SENSITIVE_BODY_X9" not in (tmp_path / "run/result.json").read_text()


def test_f0_never_reads_provider_reasoning_attribute(tmp_path):
    class _Message:
        content = json.dumps({"abstain": True, "hypotheses": []})

        @property
        def reasoning_content(self):
            raise AssertionError("private reasoning was accessed")

    result = run_f0(
        _case(tmp_path / "case"),
        transport=_Transport("", message=_Message()),
        output_directory=tmp_path / "run",
    )
    assert result.f0_run_available is True
    assert result.parse_status == "ABSTAIN"


def test_f0_refuses_to_overwrite_existing_evidence(tmp_path):
    output = tmp_path / "run"
    output.mkdir()
    (output / "existing.json").write_text("{}\n")
    with pytest.raises(F0RunContractError, match="F0_OUTPUT_DIRECTORY_NOT_EMPTY"):
        run_f0(
            _case(tmp_path / "case"),
            transport=_Transport("{}"),
            output_directory=output,
        )


def _specialization_case(tmp_path: Path):
    members = []
    for index, expression in enumerate(("x + 1\n", "y + 1\n"), 1):
        path = tmp_path / "members" / f"M{index}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expression, encoding="utf-8")
        members.append({
            "member_id": f"OPAQUE_{index}",
            "path": path.relative_to(tmp_path).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    symbols_sha = _json(tmp_path / "symbols.json", {"symbols": ["x", "y"]})
    assumptions_sha = _json(tmp_path / "assumptions.json", {
        "predicates": [
            {"predicate_id": "P_X", "status": "DECLARED"},
            {"predicate_id": "P_Y", "status": "DECLARED"},
        ],
        "status": "COMPLETE",
    })
    _json(tmp_path / "proposer_view.json", {
        "assumptions": {"path": "assumptions.json", "sha256": assumptions_sha},
        "case_id": "F0_SPECIALIZATION_CASE",
        "schema_version": "RPSProposerViewV1",
        "source_catalog": {
            "members": members,
            "symbols_path": "symbols.json",
            "symbols_sha256": symbols_sha,
        },
    })
    return load_public_case(tmp_path / "proposer_view.json")


def test_f0_evaluator_session_replays_legacy_and_certifies_strict_specialization(tmp_path):
    case = _specialization_case(tmp_path / "case")
    content = json.dumps({
        "abstain": False,
        "abstain_reason": "",
        "hypotheses": [{
            "representation_type": "parameterized_family",
            "latent_object": "F(t)=t+1",
            "variables": ["t"],
            "member_maps": [
                {"source_node_id": "G0001", "role": "instance"},
                {"source_node_id": "G0002", "role": "instance"},
            ],
            "operators": [
                {"member": "G0001", "O": "specialize"},
                {"member": "G0002", "O": "specialize"},
            ],
            "instance_maps": [
                {"member": "G0001", "theta": {"t": "x"}},
                {"member": "G0002", "theta": {"t": "y"}},
            ],
            "reconstruction_rule": "G0001=F(x); G0002=F(y)",
            "required_assumptions": ["P_X", "P_Y"],
            "proof_obligations": [
                "G0001 = F(x)",
                "G0002 = F(y)",
                "G0001 - G0002 = F(x) - F(y)",
            ],
        }],
    })
    run = run_f0(
        case,
        transport=_Transport(content),
        output_directory=tmp_path / "run",
    )
    evaluated = evaluate_f0(
        run,
        case,
        legacy_hidden={
            "ladder_n": 1,
            "nontrivial": True,
            "representation_family": ["parameterized_family"],
        },
        output_directory=tmp_path / "evaluation",
        leakage_status="CLEARED",
        assumption_clearance="CLEARED",
    )
    assert evaluated["legacy"]["any_operational_success"] is True
    assert evaluated["program"]["any_program_success"] is True
    assert evaluated["program"]["items"][0]["disposition"] == "PROGRAM_SUCCESS"
    legacy_obligations = evaluated["legacy"]["items"][0]["compile"]["obligations"]
    assert [item["verdict"] for item in legacy_obligations] == ["ZERO", "ZERO", "ZERO"]
    assert all(item["evidence"]["run_id"] for item in legacy_obligations)


def test_f0_typed_translation_fails_closed_on_freeform_operator(tmp_path):
    case = _specialization_case(tmp_path / "case")
    hypothesis = _hypothesis(
        member_maps=[
            {"source_node_id": "G0001", "role": "instance"},
            {"source_node_id": "G0002", "role": "instance"},
        ],
        operators=[
            {"member": "G0001", "O": "other_explicit"},
            {"member": "G0002", "O": "other_explicit"},
        ],
        instance_maps=[
            {"member": "G0001", "theta": {"t": "x"}},
            {"member": "G0002", "theta": {"t": "y"}},
        ],
        required_assumptions=["P_X", "P_Y"],
        proof_obligations=["G0001 = F(x)"],
    )
    content = json.dumps({"abstain": False, "hypotheses": [hypothesis]})
    run = run_f0(
        case,
        transport=_Transport(content),
        output_directory=tmp_path / "run",
    )
    evaluated = evaluate_f0(
        run,
        case,
        legacy_hidden={"nontrivial": True, "representation_family": []},
        output_directory=tmp_path / "evaluation",
        leakage_status="CLEARED",
        assumption_clearance="CLEARED",
    )
    typed = evaluated["program"]["items"][0]
    assert typed["disposition"] == "FREEFORM_UNCOMPARABLE"
    assert typed["failure_code"] == "FREEFORM_OPERATOR_UNTRANSLATABLE"
