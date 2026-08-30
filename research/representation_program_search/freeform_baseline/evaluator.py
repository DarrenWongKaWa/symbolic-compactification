"""Evaluator-side F0 replay and strict typed-program translation.

The frozen P0 proposer remains free-form.  This module is deliberately
separate from the runner so hidden legacy labels and exact verifier outcomes
cannot affect generation.  Every parseable legacy proof obligation is replayed
through a persisted symbolic-compactification session.  The historical scorer
then consumes those session verdicts rather than its old direct verifier.

Current ``PROGRAM_SUCCESS`` uses a narrower standard.  Only an unambiguous
all-member specialization program can be translated without interpreting
operator prose.  Everything else is ``FREEFORM_UNCOMPARABLE``.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping

import sympy

from symbolic_compactification import (
    adjudicate_candidate,
    init_session,
    load_expression,
    set_current,
)

from research.assumption_complete_representation.eval.ac_compile import (
    COMPILER_VERSION,
    _split_eq,
    expand_obligation,
    latent_head_var,
    parse_F,
)
from research.assumption_complete_representation.eval.ac_score import (
    SCORER_VERSION,
    proposed_depth,
    score_hypothesis,
)
from research.llm_abstraction.constructor import parse_flex, symbolic_core
from research.representation_program_search.program_ir import (
    LatentObject,
    MemberAssignment,
    Obligation,
    Operator,
    RepresentationProgram,
    canonical_json,
)
from research.representation_program_search.program_ir.model import thaw_json
from research.representation_program_search.search import PublicCase
from research.representation_program_search.search.scoring import (
    complexity_breakdown,
)
from research.representation_program_search.verifier_search import (
    VerifierFrontierNode,
    verifier_search,
)

from .prompt import _legacy_pack, build_f0_prompt
from .runner import F0RunResult

F0_EVALUATION_POLICY_VERSION = "RPSF0EvaluationPolicyV1"
F0_TYPED_TRANSLATOR_VERSION = "RPSF0SpecializationTranslatorV1"

_GID = re.compile(r"\bG\d{4}\b")
_SPECIALIZATION_OPERATORS = frozenset({"specialize", "substitute", "value"})


class F0EvaluationContractError(ValueError):
    """Stable fail-closed F0 evaluator error."""


def _hash_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _atomic_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    _atomic_bytes(
        path,
        (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
            "utf-8"
        ),
    )


def _prepare_output(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if any(path.iterdir()):
        raise F0EvaluationContractError("F0_EVALUATION_OUTPUT_NOT_EMPTY")


def _safe_code(exc: BaseException) -> str:
    return type(exc).__name__


def _sessioned_obligation(
    text: str,
    *,
    ordinal: int,
    hypothesis_index: int,
    pack: Mapping[str, Any],
    case: PublicCase,
    latent: Any,
    latent_head: str,
    latent_variable: str,
    output_root: Path,
) -> dict[str, Any]:
    pair = _split_eq(text)
    if pair is None:
        return {
            "note": "prose_obligation",
            "text": text,
            "verdict": "UNKNOWN",
        }
    lhs, rhs = pair
    lhs_expanded = expand_obligation(
        lhs, dict(pack), latent, latent_head, latent_variable
    )
    rhs_expanded = expand_obligation(
        rhs, dict(pack), latent, latent_head, latent_variable
    )
    symbols = list(pack.get("symbols") or [])
    functions = list(pack.get("functions") or [])
    lhs_expr = parse_flex(symbolic_core(lhs_expanded), symbols, functions)
    rhs_expr = parse_flex(symbolic_core(rhs_expanded), symbols, functions)
    if lhs_expr is None or rhs_expr is None:
        return {
            "expanded": f"{lhs_expanded} = {rhs_expanded}",
            "note": "unparseable_obligation",
            "text": text,
            "verdict": "UNKNOWN",
        }

    artifact = output_root / "legacy" / f"hypothesis_{hypothesis_index:02d}" / (
        f"obligation_{ordinal:03d}"
    )
    current_path = artifact / "input" / "current.txt"
    candidate_path = artifact / "input" / "candidate.txt"
    _atomic_bytes(current_path, (sympy.sstr(lhs_expr) + "\n").encode("utf-8"))
    _atomic_bytes(candidate_path, (sympy.sstr(rhs_expr) + "\n").encode("utf-8"))
    verdict = "UNKNOWN"
    evidence: dict[str, Any] = {}
    try:
        current = load_expression(
            current_path,
            case.symbols,
            functions=case.functions or None,
        )
        candidate = load_expression(
            candidate_path,
            case.symbols,
            functions=case.functions or None,
        )
        meta = {
            "condition": "F0_LEGACY_OPERATIONAL",
            "hypothesis_index": hypothesis_index,
            "obligation_ordinal": ordinal,
            "policy_version": F0_EVALUATION_POLICY_VERSION,
        }
        session = init_session(str(artifact / "verification"), meta=meta)
        set_current(session, current, meta=meta)
        outcome = adjudicate_candidate(session, candidate, meta=meta)
        verdict = outcome.result.verdict
        evidence = {
            "candidate_sha256": candidate.sha256,
            "current_sha256": current.sha256,
            "promoted": outcome.promoted,
            "run_id": session.run_id,
            "run_path": str(Path("verification") / "runs" / session.run_id),
            "step_path": str(
                Path("verification")
                / "runs"
                / session.run_id
                / "steps"
                / outcome.step_path.name
            ),
        }
    except Exception as exc:
        evidence = {"failure_code": _safe_code(exc)}
        verdict = "UNKNOWN"

    return {
        "evidence": evidence,
        "expanded": f"{lhs_expanded} = {rhs_expanded}",
        # Preserve the frozen scorer's classification token; the separate
        # field proves that the verdict came from the current session path.
        "note": "parsed_eq",
        "verification_path": "SESSION_REPLAY",
        "source_member_ids": sorted(set(_GID.findall(text))),
        "text": text,
        "verdict": verdict,
    }


def _sessioned_legacy_compile(
    hypothesis: Mapping[str, Any],
    *,
    hypothesis_index: int,
    pack: Mapping[str, Any],
    case: PublicCase,
    output_root: Path,
) -> dict[str, Any]:
    if hypothesis.get("parse_status") != "OK":
        return {
            "F_parsed": False,
            "certified": False,
            "compile_status": "C_FAIL",
            "compiler_version": COMPILER_VERSION,
            "n_nonzero": 0,
            "n_unknown": 0,
            "n_zero": 0,
            "note": hypothesis.get("parse_error") or "parse_failure",
            "obligations": [],
            "session_replay_policy": F0_EVALUATION_POLICY_VERSION,
        }
    latent_text = str(hypothesis.get("latent_object") or "")
    latent_head, latent_variable = latent_head_var(latent_text)
    variables = hypothesis.get("variables") or []
    if variables:
        first = variables[0]
        latent_variable = (
            str(first.get("name") or latent_variable)
            if isinstance(first, Mapping)
            else str(first)
        )
    latent = parse_F(
        latent_text,
        list(pack.get("symbols") or []),
        list(pack.get("functions") or []),
    )
    obligations = [
        _sessioned_obligation(
            text,
            ordinal=ordinal,
            hypothesis_index=hypothesis_index,
            pack=pack,
            case=case,
            latent=latent,
            latent_head=latent_head,
            latent_variable=latent_variable,
            output_root=output_root,
        )
        for ordinal, value in enumerate(
            hypothesis.get("proof_obligations") or [], start=1
        )
        if isinstance(value, str)
        for text in (value,)
    ]
    real = [item for item in obligations if item.get("note") != "prose_obligation"]
    n_zero = sum(item["verdict"] == "ZERO" for item in real)
    n_nonzero = sum(item["verdict"] == "NONZERO" for item in real)
    n_unknown = sum(item["verdict"] == "UNKNOWN" for item in real)
    compile_status = "C_OK" if real else "C_FAIL"
    return {
        "F_parsed": latent is not None,
        "F_srepr": str(latent) if latent is not None else "",
        "certified": (
            compile_status == "C_OK"
            and n_zero > 0
            and n_nonzero == 0
            and n_unknown == 0
        ),
        "compile_status": compile_status,
        "compiler_version": COMPILER_VERSION,
        "constructable": bool(latent is not None or real),
        "n_nonzero": n_nonzero,
        "n_unknown": n_unknown,
        "n_zero": n_zero,
        "note": "",
        "obligations": obligations,
        "session_replay_policy": F0_EVALUATION_POLICY_VERSION,
    }


def _legacy_evaluation(
    result: F0RunResult,
    *,
    case: PublicCase,
    hidden: Mapping[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    pack, _id_map = _legacy_pack(case)
    scored: list[dict[str, Any]] = []
    for index, hypothesis in enumerate(
        result.parsed.get("hypotheses") or [], start=1
    ):
        compiled = _sessioned_legacy_compile(
            hypothesis,
            hypothesis_index=index,
            pack=pack,
            case=case,
            output_root=output_root,
        )
        score = score_hypothesis(dict(hypothesis), pack, dict(hidden), compiled)
        scored.append({
            "compile": compiled,
            "hypothesis_index": index,
            "score": score,
        })
    successes = [item for item in scored if item["score"]["operational_success"]]
    return {
        "any_operational_success": bool(successes),
        "best_hypothesis_index": (
            successes[0]["hypothesis_index"] if successes else None
        ),
        "hidden_authority_sha256": _hash_json(dict(hidden)),
        "items": scored,
        "legacy_condition": "F0_LEGACY_OPERATIONAL",
        "legacy_semantics": "FROZEN_SCORER_WITH_SESSION_REPLAYED_OBLIGATIONS",
        "scorer_version": SCORER_VERSION,
    }


def _assumption_ids(
    hypothesis: Mapping[str, Any], case: PublicCase
) -> tuple[tuple[str, ...] | None, str | None]:
    assumptions = thaw_json(case.assumptions)
    predicates = (
        assumptions.get("predicates", [])
        if isinstance(assumptions, Mapping)
        else assumptions
    )
    if not isinstance(predicates, list):
        return None, "ASSUMPTION_CONTRACT_SHAPE_UNSUPPORTED"
    lookup: dict[str, str] = {}
    for predicate in predicates:
        if not isinstance(predicate, Mapping):
            continue
        predicate_id = predicate.get("predicate_id")
        if isinstance(predicate_id, str) and predicate_id:
            lookup[predicate_id] = predicate_id
            lookup[canonical_json(predicate)] = predicate_id
    selected: list[str] = []
    for item in hypothesis.get("required_assumptions") or []:
        if not isinstance(item, str) or item not in lookup:
            return None, "ASSUMPTION_NOT_EXACTLY_MAPPED"
        selected.append(lookup[item])
    return tuple(sorted(set(selected))), None


def _strict_specialization_program(
    hypothesis: Mapping[str, Any], case: PublicCase
) -> tuple[RepresentationProgram | None, str | None]:
    if hypothesis.get("parse_status") != "OK":
        return None, "HYPOTHESIS_PARSE_FAILURE"
    prompt = build_f0_prompt(case)
    inverse_ids = {legacy: source for source, legacy in prompt.source_id_map.items()}
    member_maps = hypothesis.get("member_maps") or []
    if not all(isinstance(item, Mapping) for item in member_maps):
        return None, "MEMBER_MAP_INVALID"
    mapped_legacy = [str(item.get("source_node_id") or "") for item in member_maps]
    if (
        len(mapped_legacy) != len(set(mapped_legacy))
        or set(mapped_legacy) != set(inverse_ids)
    ):
        return None, "ALL_MEMBER_COVERAGE_REQUIRED"

    operator_rows = hypothesis.get("operators") or []
    if not all(isinstance(item, Mapping) for item in operator_rows):
        return None, "OPERATOR_ROW_INVALID"
    operators_by_member: dict[str, str] = {}
    for item in operator_rows:
        member = str(item.get("member") or "")
        operator = str(item.get("O") or "").strip().lower()
        if (
            member not in inverse_ids
            or member in operators_by_member
            or operator not in _SPECIALIZATION_OPERATORS
        ):
            return None, "FREEFORM_OPERATOR_UNTRANSLATABLE"
        operators_by_member[member] = operator
    if set(operators_by_member) != set(inverse_ids):
        return None, "ONE_OPERATOR_PER_MEMBER_REQUIRED"

    instance_rows = hypothesis.get("instance_maps") or []
    if not all(isinstance(item, Mapping) for item in instance_rows):
        return None, "INSTANCE_MAP_INVALID"
    instances: dict[str, Mapping[str, Any]] = {}
    for item in instance_rows:
        member = str(item.get("member") or "")
        theta = item.get("theta")
        if (
            member not in inverse_ids
            or member in instances
            or not isinstance(theta, Mapping)
        ):
            return None, "INSTANCE_MAP_INVALID"
        instances[member] = theta
    if set(instances) != set(inverse_ids):
        return None, "ONE_INSTANCE_MAP_PER_MEMBER_REQUIRED"

    pack, _id_map = _legacy_pack(case)
    latent_text = str(hypothesis.get("latent_object") or "")
    _head, default_variable = latent_head_var(latent_text)
    variables = hypothesis.get("variables") or []
    if len(variables) > 1:
        return None, "ONLY_UNARY_SPECIALIZATION_TRANSLATABLE"
    parameter = default_variable
    if variables:
        value = variables[0]
        parameter = (
            str(value.get("name") or "")
            if isinstance(value, Mapping)
            else str(value)
        )
    if not parameter:
        return None, "LATENT_PARAMETER_MISSING"
    latent_expr = parse_F(
        latent_text,
        list(pack.get("symbols") or []),
        list(pack.get("functions") or []),
    )
    if latent_expr is None:
        return None, "LATENT_EXPRESSION_UNPARSEABLE"

    assumptions_used, assumption_failure = _assumption_ids(hypothesis, case)
    if assumption_failure is not None or assumptions_used is None:
        return None, assumption_failure

    ir_operators: list[Operator] = []
    assignments: list[MemberAssignment] = []
    obligations: list[Obligation] = []
    instance_payload: dict[str, Any] = {}
    for index, legacy_id in enumerate(sorted(inverse_ids), start=1):
        values = instances[legacy_id]
        if set(values) != {parameter}:
            return None, "INSTANCE_PARAMETER_SET_MISMATCH"
        node = values[parameter]
        if not isinstance(node, str) or not node:
            return None, "INSTANCE_VALUE_INVALID"
        source_id = inverse_ids[legacy_id]
        operator_id = f"F0_OP_{index:04d}"
        output = f"F0_OUT_{index:04d}"
        ir_operators.append(Operator(
            operator_id=operator_id,
            operator="VALUE",
            output=output,
            latent_id="F0_LATENT",
            arguments={"node": node},
        ))
        assignments.append(MemberAssignment(source_id, output, (operator_id,)))
        obligations.append(Obligation(f"F0_OBL_{index:04d}", source_id, output))
        instance_payload[source_id] = {"F0_LATENT": {parameter: node}}

    depth = proposed_depth(dict(hypothesis))
    return RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=case.source_members,
        latent_objects=(LatentObject(
            latent_id="F0_LATENT",
            form="FUNCTION_1",
            parameters=(parameter,),
            expression=sympy.sstr(latent_expr),
        ),),
        node_structures=(),
        operators=tuple(ir_operators),
        member_assignments=tuple(assignments),
        assumptions_used=assumptions_used,
        assumption_statuses=case.assumption_statuses,
        obligations=tuple(obligations),
        instance_maps=instance_payload,
        unexplained_members=(),
        representation_depth=(f"R{depth}" if depth is not None else None),
    ), None


def _typed_evaluation(
    result: F0RunResult,
    *,
    case: PublicCase,
    output_root: Path,
    leakage_status: str,
    assumption_clearance: str,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for index, hypothesis in enumerate(
        result.parsed.get("hypotheses") or [], start=1
    ):
        program, failure = _strict_specialization_program(hypothesis, case)
        if program is None:
            rows.append({
                "disposition": "FREEFORM_UNCOMPARABLE",
                "failure_code": failure,
                "hypothesis_index": index,
                "program_success": False,
                "translator_version": F0_TYPED_TRANSLATOR_VERSION,
            })
            continue
        node = VerifierFrontierNode.from_program(
            program,
            case.compile_context("G_FULL"),
            complexity=complexity_breakdown(program).total,
            depth=len(program.operators),
            public_priority=(index,),
            leakage_status=leakage_status,
            assumption_clearance=assumption_clearance,
            label=f"F0_HYPOTHESIS_{index:02d}",
        )
        verification_root = output_root / "typed" / f"hypothesis_{index:02d}"
        verification = verifier_search(
            (node,),
            output_root=verification_root,
            budget=10,
            condition="F0",
            llm_tokens_used=result.usage.total_tokens or 0,
            expander=None,
        )
        success = verification.first_success_index is not None
        rows.append({
            "disposition": (
                "PROGRAM_SUCCESS" if success else "TYPED_PROGRAM_NOT_CERTIFIED"
            ),
            "failure_code": None,
            "hypothesis_index": index,
            "program_id": node.program_id,
            "program_success": success,
            "translator_version": F0_TYPED_TRANSLATOR_VERSION,
            "verifier_result": verification.to_dict(),
        })
    successes = [item for item in rows if item["program_success"]]
    return {
        "any_program_success": bool(successes),
        "best_hypothesis_index": (
            successes[0]["hypothesis_index"] if successes else None
        ),
        "items": rows,
        "program_success_semantics": "STRICT_M1_TRANSLATION_PLUS_SESSION_ZERO",
        "translator_version": F0_TYPED_TRANSLATOR_VERSION,
    }


def evaluate_f0(
    result: F0RunResult,
    case: PublicCase,
    *,
    legacy_hidden: Mapping[str, Any],
    output_directory: str | Path,
    leakage_status: str = "UNKNOWN",
    assumption_clearance: str = "UNKNOWN",
) -> dict[str, Any]:
    """Evaluate one completed F0 run on separate legacy and current axes."""
    if result.case_id != case.case_id:
        raise F0EvaluationContractError("F0_EVALUATION_CASE_MISMATCH")
    prompt = build_f0_prompt(case)
    if result.prompt_sha256 != prompt.hashes["prompt_sha256"]:
        raise F0EvaluationContractError("F0_EVALUATION_PROMPT_DRIFT")
    if leakage_status not in {"CLEARED", "FOUND", "UNKNOWN"}:
        raise F0EvaluationContractError("F0_EVALUATION_LEAKAGE_STATUS_INVALID")
    if assumption_clearance not in {"CLEARED", "INCOMPLETE", "UNKNOWN"}:
        raise F0EvaluationContractError("F0_EVALUATION_ASSUMPTION_STATUS_INVALID")
    output = Path(output_directory)
    _prepare_output(output)
    if not result.f0_run_available:
        payload = {
            "case_id": case.case_id,
            "condition": "F0",
            "evaluation_status": "F0_UNAVAILABLE",
            "legacy": None,
            "policy_version": F0_EVALUATION_POLICY_VERSION,
            "program": None,
            "run_header_sha256": result.run_header_sha256,
        }
        _atomic_json(output / "evaluation.json", payload)
        return payload

    legacy = _legacy_evaluation(
        result,
        case=case,
        hidden=legacy_hidden,
        output_root=output,
    )
    typed = _typed_evaluation(
        result,
        case=case,
        output_root=output,
        leakage_status=leakage_status,
        assumption_clearance=assumption_clearance,
    )
    payload = {
        "case_id": case.case_id,
        "condition": "F0",
        "evaluation_status": "COMPLETE",
        "legacy": legacy,
        "policy_version": F0_EVALUATION_POLICY_VERSION,
        "program": typed,
        "proposer_view_sha256": case.proposer_view_sha256,
        "run_header_sha256": result.run_header_sha256,
    }
    payload["evaluation_sha256"] = _hash_json(payload)
    _atomic_json(output / "evaluation.json", payload)
    return payload
