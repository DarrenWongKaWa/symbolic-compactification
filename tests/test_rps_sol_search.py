from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from research.representation_program_search.search import (
    SearchPolicy,
    apply_action,
    enumerative_search,
    extract_candidate_pool,
    initial_state,
    legal_actions,
    load_public_case,
)
from research.representation_program_search.sol_search import (
    SOL_ARTIFACT_SCHEMA,
    SOL_AUTHORITY_COMMIT,
    SOL_AUTHORITY_MANIFEST_SHA256,
    SOL_LAYER,
    SOL_REPLAY_BACKENDS,
    authority_manifest,
    load_sol_projection,
    route_legal_child,
    replay_policy_payload,
    sol_conditioned_search,
    structural_container_metadata,
    validate_local_authority,
)


def _json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(path: Path, value: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _public_case(
    tmp_path: Path,
    expressions=("polygamma(0, x)", "polygamma(1, x)", "x + 1"),
):
    members = []
    for index, expression in enumerate(expressions, 1):
        member_id = f"A{index:03d}"
        relative = f"members/{member_id}.txt"
        members.append({
            "member_id": member_id,
            "path": relative,
            "sha256": _text(tmp_path / relative, expression),
        })
    symbols_hash = _json(tmp_path / "symbols.json", {"symbols": ["x", "y"]})
    _json(tmp_path / "proposer_view.json", {
        "assumptions": {
            "predicates": [{"predicate_id": "P_REAL", "status": "DECLARED"}],
        },
        "case_id": "SYNTHETIC_SOL_PUBLIC",
        "schema_version": "RPSProposerViewV1",
        "source_catalog": {
            "members": members,
            "symbols_path": "symbols.json",
            "symbols_sha256": symbols_hash,
        },
    })
    return load_public_case(tmp_path / "proposer_view.json")


def _binding(case) -> dict:
    return {
        "case_id": case.case_id,
        "proposer_view_sha256": case.proposer_view_sha256,
        "source_members": [
            {"member_id": item.member_id, "sha256": item.sha256}
            for item in sorted(case.members, key=lambda item: item.member_id)
        ],
    }


def _derivative_bundle() -> dict:
    left_srepr = "polygamma(Integer(0), Symbol('x', real=True))"
    right_srepr = "polygamma(Integer(1), Symbol('x', real=True))"
    nodes = []
    for node_id, text, srepr in (
        ("N0002", "polygamma(0, x)", left_srepr),
        ("N0003", "polygamma(1, x)", right_srepr),
    ):
        nodes.append({
            "free_symbols": ["x"],
            "functions": [],
            "indexed_symbols": [],
            "node_id": node_id,
            "ops": 1,
            "provenance": "sympy_ast",
            "source_span": None,
            "srepr": srepr,
            "structural_hash": hashlib.sha256(srepr.encode("utf-8")).hexdigest(),
            "text": text,
        })
    return {
        "backend_status": {
            "cadabra": "OPTIONAL / unavailable",
            "egglog": "OPTIONAL / unavailable",
            "form": "OPTIONAL / unavailable",
            "lgg": "AVAILABLE",
            "matchpy": "OPTIONAL / unavailable",
            "metatheory": "OPTIONAL / unavailable",
            "sympy": "AVAILABLE",
        },
        "canonical_variants": [],
        "expression_summary": {
            "raw_sha256": hashlib.sha256(
                b"polygamma(0, x) + polygamma(1, x)"
            ).hexdigest(),
            "text": "polygamma(0, x) + polygamma(1, x)",
        },
        "families": [],
        "nodes": nodes,
        "packets": [],
        "provenance": {
            "backends_run": ["sympy"],
            "context_keys": [],
            "layer": SOL_LAYER,
            "note": "observation only; no promotion; no scientific interpretation",
            "package": "0.3.0",
        },
        "relations": [{
            "assumptions": ["declared sympy.diff semantics"],
            "backend": "sympy",
            "backend_version": "1.14.0",
            "confidence_class": "deterministic",
            "evidence": "synthetic replay fixture of frozen derivative edge",
            "exactness_class": "EXACT_FACT",
            "relation_type": "DERIVATIVE_RELATED",
            "source_ids": ["N0002", "N0003"],
            "theory": None,
            "witness": "diff(polygamma(0, x),x) == polygamma(1, x)",
        }],
    }


def _artifact(path: Path, case, bundle: dict) -> tuple[Path, str]:
    bundle = json.loads(json.dumps(bundle))
    container = structural_container_metadata(case)
    bundle["expression_summary"]["raw_sha256"] = container["expression_sha256"]
    bundle["provenance"]["context_keys"] = ["rps_replay_policy"]
    bundle_sha256 = hashlib.sha256(
        json.dumps(
            bundle,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    payload = {
        "bundle": bundle,
        "case_binding": _binding(case),
        "replay_attestation": {
            "authority_manifest_sha256": SOL_AUTHORITY_MANIFEST_SHA256,
            "backend_provenance": {
                "backend_status": bundle["backend_status"],
                "backend_versions": {
                    name: "synthetic-fixture" for name in SOL_REPLAY_BACKENDS
                },
                "backends_run": bundle["provenance"]["backends_run"],
            },
            "bundle_sha256": bundle_sha256,
            "environment_versions": {
                "egglog": "synthetic-fixture",
                "lgg": "synthetic-fixture",
                "machine": "synthetic",
                "matchpy": "synthetic-fixture",
                "python_implementation": "synthetic",
                "python_version": "synthetic",
                "sympy": "synthetic-fixture",
                "system": "synthetic",
                "system_release": "synthetic",
            },
            "mode": "READ_ONLY_FROZEN_SOL_REPLAY",
            "public_case_sha256": case.proposer_view_sha256,
            "replay_policy": replay_policy_payload(),
            "structural_container": container,
        },
        "schema_version": SOL_ARTIFACT_SCHEMA,
        "sol_authority": {
            "commit": SOL_AUTHORITY_COMMIT,
            "layer": SOL_LAYER,
            **authority_manifest(),
        },
    }
    return path, _json(path, payload)


def _shared_latent_state(case):
    pool = extract_candidate_pool(case)
    policy = SearchPolicy()
    root = initial_state(case, grammar_id="G_FULL")
    shared = next(
        item for item in pool.latents
        if item.extraction == "PAIRWISE_ANTI_UNIFICATION"
        and set(item.public_origins) == {"A001", "A002"}
        and len(item.parameters) == 1
    )
    create = next(
        item for item in legal_actions(root, case, pool, policy)
        if item.action == "CREATE_LATENT"
        and item.payload["candidate_id"] == shared.candidate_id
    )
    return pool, policy, apply_action(root, create, case)


def test_projection_is_hash_and_public_source_bound(tmp_path):
    assert validate_local_authority(Path(__file__).resolve().parents[1]) == ()
    case = _public_case(tmp_path / "case")
    path, digest = _artifact(tmp_path / "sol.json", case, _derivative_bundle())
    projection = load_sol_projection(case, path, expected_sha256=digest)
    assert projection.status == "AVAILABLE"
    assert len(projection.relations) == 1
    relation = projection.relations[0]
    assert relation.relation_type == "DERIVATIVE_RELATED"
    assert relation.affected_member_ids == ("A001", "A002")
    assert relation.node_symbols == ("x",)
    assert relation.source_artifact_sha256 == digest
    assert relation.relation_id.startswith("SOLR_")


def test_projection_rejects_a_self_declared_but_wrong_authority_manifest(tmp_path):
    case = _public_case(tmp_path / "case")
    path, _digest = _artifact(tmp_path / "sol.json", case, _derivative_bundle())
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["sol_authority"]["source_files"][
        "src/symbolic_compactification/observations/api.py"
    ] = "0" * 64
    wrong_digest = _json(path, raw)
    projection = load_sol_projection(case, path, expected_sha256=wrong_digest)
    assert projection.status == "UNAVAILABLE"
    assert projection.reason_codes == ("SOL_AUTHORITY_INVALID",)


def test_projection_refuses_local_frozen_authority_drift(tmp_path, monkeypatch):
    case = _public_case(tmp_path / "case")
    path, digest = _artifact(tmp_path / "sol.json", case, _derivative_bundle())
    monkeypatch.setattr(
        "research.representation_program_search.sol_search.projection.validate_local_authority",
        lambda _root: (
            "SOL_AUTHORITY_SOURCE_DRIFT:src/symbolic_compactification/observations/api.py",
        ),
    )
    projection = load_sol_projection(case, path, expected_sha256=digest)
    assert projection.status == "UNAVAILABLE"
    assert projection.reason_codes[0].startswith("SOL_AUTHORITY_SOURCE_DRIFT")


def test_projection_fails_closed_on_hash_binding_and_hidden_fields(tmp_path):
    case = _public_case(tmp_path / "case")
    path, digest = _artifact(tmp_path / "sol.json", case, _derivative_bundle())
    mismatch = load_sol_projection(case, path, expected_sha256="0" * 64)
    assert mismatch.status == "UNAVAILABLE"
    assert mismatch.reason_codes == ("SOL_ARTIFACT_HASH_MISMATCH",)

    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["gold_program"] = {"operators": ["ADD_DERIVATIVE"]}
    leaking_digest = _json(path, raw)
    leaking = load_sol_projection(case, path, expected_sha256=leaking_digest)
    assert leaking.status == "UNAVAILABLE"
    assert leaking.reason_codes == ("SOL_FORBIDDEN_FIELD:gold_program",)


def test_projection_rejects_case_drift_node_drift_and_evaluator_paths(tmp_path):
    case = _public_case(tmp_path / "case")
    path, _digest = _artifact(tmp_path / "sol.json", case, _derivative_bundle())
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["case_binding"]["proposer_view_sha256"] = "0" * 64
    drift_digest = _json(path, raw)
    drift = load_sol_projection(case, path, expected_sha256=drift_digest)
    assert drift.status == "UNAVAILABLE"
    assert drift.reason_codes == ("SOL_CASE_BINDING_MISMATCH",)

    node_drift_bundle = _derivative_bundle()
    node_drift_bundle["nodes"][0]["srepr"] += "_drift"
    path, node_digest = _artifact(tmp_path / "sol.json", case, node_drift_bundle)
    node_drift = load_sol_projection(case, path, expected_sha256=node_digest)
    assert node_drift.status == "UNAVAILABLE"
    assert node_drift.reason_codes[0].startswith("SOL_NODE_HASH_MISMATCH")

    forbidden_path, forbidden_digest = _artifact(
        case.package_root / "reference" / "sol.json",
        case,
        _derivative_bundle(),
    )
    forbidden = load_sol_projection(
        case, forbidden_path, expected_sha256=forbidden_digest
    )
    assert forbidden.status == "UNAVAILABLE"
    assert forbidden.reason_codes == ("SOL_ARTIFACT_PATH_FORBIDDEN",)


def test_projection_rejects_extra_replay_attestation_fields(tmp_path):
    case = _public_case(tmp_path / "case")
    path, _digest = _artifact(tmp_path / "sol.json", case, _derivative_bundle())
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["replay_attestation"]["target_hint"] = "not allowed"
    tampered_digest = _json(path, raw)
    projection = load_sol_projection(case, path, expected_sha256=tampered_digest)
    assert projection.status == "UNAVAILABLE"
    assert projection.reason_codes == ("SOL_REPLAY_ATTESTATION_INVALID",)


@pytest.mark.parametrize(
    ("section", "field", "value", "reason"),
    [
        ("replay_policy", "timeout_seconds", 13.0, "SOL_REPLAY_ATTESTATION_INVALID"),
        ("structural_container", "construction", "changed", "SOL_REPLAY_ATTESTATION_INVALID"),
        ("backend_provenance", "backends_run", [], "SOL_BACKEND_PROVENANCE_INVALID"),
        ("backend_provenance", "extra", "leak", "SOL_BACKEND_PROVENANCE_INVALID"),
        ("environment_versions", "extra", "leak", "SOL_ENVIRONMENT_VERSIONS_INVALID"),
        ("environment_versions", "sympy", "tampered", "SOL_ENVIRONMENT_VERSIONS_INVALID"),
    ],
)
def test_projection_validates_every_replay_attestation_section_exactly(
    tmp_path, section, field, value, reason,
):
    case = _public_case(tmp_path / "case")
    path, _digest = _artifact(tmp_path / "sol.json", case, _derivative_bundle())
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["replay_attestation"][section][field] = value
    tampered_digest = _json(path, raw)
    projection = load_sol_projection(case, path, expected_sha256=tampered_digest)
    assert projection.status == "UNAVAILABLE"
    assert projection.reason_codes == (reason,)


def test_aggregate_or_unowned_sol_is_explicitly_ineligible(tmp_path):
    case = _public_case(tmp_path / "case")
    bundle = _derivative_bundle()
    # A relation without source nodes is an aggregate diagnostic, not an
    # action-addressable public relation.
    bundle["relations"] = [{
        "source_ids": [],
        "relation_type": "KNOWN_REWRITE_EQUIVALENT",
        "backend": "sympy",
        "exactness_class": "EXACT_FACT",
        "evidence": "synthetic aggregate control",
        "assumptions": [],
        "confidence_class": "deterministic",
        "witness": None,
        "theory": None,
        "backend_version": "synthetic-control",
    }]
    path, digest = _artifact(tmp_path / "sol.json", case, bundle)
    projection = load_sol_projection(case, path, expected_sha256=digest)
    assert projection.status == "NO_ELIGIBLE_SOL"
    assert projection.reason_codes == ("NO_PUBLIC_SOURCE_BOUND_RELATIONS",)
    result = sol_conditioned_search(
        case, budget=10, artifact_path=path, artifact_sha256=digest
    )
    assert result.search_result is None
    assert result.to_dict()["states_expanded"] == 0
    assert result.to_dict()["sol_status"] == "NO_ELIGIBLE_SOL"


def test_source_bound_but_unroutable_sol_is_no_eligible_sol(tmp_path):
    case = _public_case(tmp_path / "case")
    bundle = _derivative_bundle()
    bundle["relations"][0]["relation_type"] = "SAME_BRANCH_DEPENDENCY"
    bundle["relations"][0]["exactness_class"] = "DESCRIPTIVE_FACT"
    path, digest = _artifact(tmp_path / "sol.json", case, bundle)
    projection = load_sol_projection(case, path, expected_sha256=digest)
    assert projection.status == "NO_ELIGIBLE_SOL"
    assert projection.relations == ()


def test_s3_uses_exact_m2_pool_frontier_and_budget_without_verifier(tmp_path, monkeypatch):
    case = _public_case(tmp_path / "case")
    path, digest = _artifact(tmp_path / "sol.json", case, _derivative_bundle())
    monkeypatch.setattr(
        "symbolic_compactification.verify_equivalent",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("verifier called")),
    )
    s1 = enumerative_search(case, budget=10)
    s3 = sol_conditioned_search(
        case, budget=10, artifact_path=path, artifact_sha256=digest
    )
    assert s3.search_result is not None
    assert s3.search_result.states_expanded == 10
    assert s3.candidate_pool_hash == s1.candidate_pool.canonical_hash
    assert (
        s3.search_result.expansion_trace[0].legal_child_hashes
        == s1.expansion_trace[0].legal_child_hashes
    )
    assert s3.search_result.ordering_uses_verifier_outcomes is False
    assert s3.llm_tokens == 0
    assert s3.private_reasoning_recorded is False


def test_s3_is_deterministic_and_audits_every_used_relation(tmp_path):
    case = _public_case(tmp_path / "case")
    path, digest = _artifact(tmp_path / "sol.json", case, _derivative_bundle())
    first = sol_conditioned_search(
        case, budget=10, artifact_path=path, artifact_sha256=digest
    )
    replay = sol_conditioned_search(
        case, budget=10, artifact_path=path, artifact_sha256=digest
    )
    assert first.semantic_trace_hash == replay.semantic_trace_hash
    assert first.search_result is not None and replay.search_result is not None
    assert [item.canonical_hash for item in first.search_result.expanded_states] == [
        item.canonical_hash for item in replay.search_result.expanded_states
    ]
    used = [
        contribution
        for decision in first.routing_decisions
        for contribution in decision.contributions
    ]
    assert used
    assert all(item.source_artifact_sha256 == digest for item in used)
    assert all(item.action_hash and item.affected_state_hash for item in used)


def test_derivative_sol_routes_operator_group_and_repeated_node_hypotheses(tmp_path):
    case = _public_case(tmp_path / "case")
    path, digest = _artifact(tmp_path / "sol.json", case, _derivative_bundle())
    projection = load_sol_projection(case, path, expected_sha256=digest)
    pool, policy, latent_state = _shared_latent_state(case)

    derivative = next(
        item for item in legal_actions(latent_state, case, pool, policy)
        if item.action == "ADD_DERIVATIVE" and item.payload["input"] is None
    )
    derivative_child = apply_action(latent_state, derivative, case)
    derivative_route = route_legal_child(
        projection,
        parent=latent_state,
        action=derivative,
        child=derivative_child,
        candidate_pool=pool,
        parent_priority=0,
    )
    assert {item.rule_id for item in derivative_route.contributions} == {
        "SOL_DERIVATIVE_OPERATOR"
    }

    repeated = next(
        item for item in legal_actions(latent_state, case, pool, policy)
        if item.action == "ADD_REPEATED_NODE" and item.payload["nodes"] == ("x", "x")
    )
    repeated_state = apply_action(latent_state, repeated, case)
    repeated_route = route_legal_child(
        projection,
        parent=latent_state,
        action=repeated,
        child=repeated_state,
        candidate_pool=pool,
        parent_priority=0,
    )
    assert {item.rule_id for item in repeated_route.contributions} == {
        "SOL_DERIVATIVE_REPEATED_NODE"
    }

    hermite = next(
        item for item in legal_actions(repeated_state, case, pool, policy)
        if item.action == "ADD_HERMITE_DD"
    )
    hermite_state = apply_action(repeated_state, hermite, case)
    hermite_route = route_legal_child(
        projection,
        parent=repeated_state,
        action=hermite,
        child=hermite_state,
        candidate_pool=pool,
        parent_priority=repeated_route.child_priority,
    )
    assert {item.rule_id for item in hermite_route.contributions} == {
        "SOL_DERIVATIVE_HERMITE"
    }

    assign = next(
        item for item in legal_actions(latent_state, case, pool, policy)
        if item.action == "ADD_MEMBER"
        and item.payload.get("member_id") == "A001"
        and "latent_id" in item.payload
    )
    assigned = apply_action(latent_state, assign, case)
    group = next(
        item for item in legal_actions(assigned, case, pool, policy)
        if item.action == "GROUP_MEMBERS"
        and set(item.payload["member_ids"]) == {"A001", "A002"}
    )
    grouped = apply_action(assigned, group, case)
    group_route = route_legal_child(
        projection,
        parent=assigned,
        action=group,
        child=grouped,
        candidate_pool=pool,
        parent_priority=0,
    )
    assert {item.rule_id for item in group_route.contributions} == {
        "SOL_MEMBER_GROUP"
    }


def test_misleading_candidate_relation_is_an_explicit_anchoring_control(tmp_path):
    case = _public_case(tmp_path / "case")
    bundle = _derivative_bundle()
    bundle["relations"][0]["relation_type"] = "RECURRENCE_CANDIDATE"
    bundle["relations"][0]["exactness_class"] = "CANDIDATE_RELATION"
    bundle["relations"][0]["evidence"] = "synthetic misleading SOL control"
    path, digest = _artifact(tmp_path / "sol.json", case, bundle)
    projection = load_sol_projection(case, path, expected_sha256=digest)
    pool, policy, latent_state = _shared_latent_state(case)
    derivative = next(
        item for item in legal_actions(latent_state, case, pool, policy)
        if item.action == "ADD_DERIVATIVE" and item.payload["input"] is None
    )
    recurrence = next(
        item for item in legal_actions(latent_state, case, pool, policy)
        if item.action == "ADD_RECURRENCE"
    )
    derivative_route = route_legal_child(
        projection,
        parent=latent_state,
        action=derivative,
        child=apply_action(latent_state, derivative, case),
        candidate_pool=pool,
        parent_priority=0,
    )
    recurrence_route = route_legal_child(
        projection,
        parent=latent_state,
        action=recurrence,
        child=apply_action(latent_state, recurrence, case),
        candidate_pool=pool,
        parent_priority=0,
    )
    assert derivative_route.incremental_priority == 0
    assert recurrence_route.incremental_priority == 12
    assert recurrence_route.child_priority > derivative_route.child_priority
    assert recurrence_route.contributions[0].rule_id == "SOL_RECURRENCE_OPERATOR"


@pytest.mark.parametrize("budget", [11, 49])
def test_s3_rejects_nonfrozen_state_budgets(tmp_path, budget):
    case = _public_case(tmp_path / "case")
    path, digest = _artifact(tmp_path / "sol.json", case, _derivative_bundle())
    with pytest.raises(Exception, match="STATE_BUDGET_NOT_FROZEN"):
        sol_conditioned_search(
            case, budget=budget, artifact_path=path, artifact_sha256=digest
        )


def test_s3_modules_do_not_import_sol_execution_verifier_or_evaluator_loaders():
    root = Path("research/representation_program_search/sol_search")
    imported: set[str] = set()
    names: set[str] = set()
    sol_api_importers: set[str] = set()
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
                names.update(alias.name for alias in node.names)
                if node.module == "symbolic_compactification.observations.api":
                    sol_api_importers.add(path.name)
            elif isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
    assert sol_api_importers == {"replay.py"}
    assert "symbolic_compactification.verifier" not in imported
    assert "research.representation_program_search.program_ir.loader" not in imported
    assert "observe" in names
    assert "verify_equivalent" not in names
    assert "load_case_package" not in names
