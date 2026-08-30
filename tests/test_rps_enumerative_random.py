from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from research.representation_program_search.grammar_v1 import BUDGET_STATES
from research.representation_program_search.program_ir import (
    LatentObject,
    MemberAssignment,
    Obligation,
    Operator,
    RepresentationProgram,
    SourceMember,
)
from research.representation_program_search.search import (
    CANDIDATE_POLICY_VERSION,
    CandidatePool,
    LatentCandidate,
    LegalAction,
    ObligationEvidence,
    SearchContractError,
    SearchPolicy,
    SearchState,
    apply_action,
    complexity_breakdown,
    enumerative_search,
    expand_state,
    extract_candidate_pool,
    initial_state,
    legal_actions,
    load_public_case,
    random_search,
    score_program,
)


def _json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(path: Path, value: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _public_fixture(tmp_path: Path, *, members: int = 3) -> Path:
    expressions = ("x + 1", "y + 1", "x + y")[:members]
    catalog_members = []
    for index, expression in enumerate(expressions, 1):
        member_id = f"A{index:03d}"
        relative = f"members/{member_id}.txt"
        digest = _text(tmp_path / relative, expression)
        catalog_members.append({
            "member_id": member_id,
            "path": relative,
            "sha256": digest,
        })
    symbols_digest = _json(tmp_path / "symbols.json", {"symbols": ["x", "y"]})
    proposer = {
        "assumptions": {
            "predicates": [
                {"predicate_id": "P_REAL", "status": "DECLARED"},
            ],
        },
        "case_id": "SYNTHETIC_PUBLIC",
        "schema_version": "RPSProposerViewV1",
        "source_catalog": {
            "members": catalog_members,
            "symbols_path": "symbols.json",
            "symbols_sha256": symbols_digest,
        },
    }
    _json(tmp_path / "reference" / "program.json", {"not": "public"})
    _json(tmp_path / "verification" / "receipt.json", {"not": "public"})
    _json(tmp_path / "proposer_view.json", proposer)
    return tmp_path / "proposer_view.json"


def test_public_loader_reads_only_disclosed_hashed_artifacts(tmp_path, monkeypatch):
    view = _public_fixture(tmp_path)
    original_read_text = Path.read_text
    original_read_bytes = Path.read_bytes

    def guarded_text(path, *args, **kwargs):
        assert not ({"reference", "verification"} & set(path.parts))
        return original_read_text(path, *args, **kwargs)

    def guarded_bytes(path, *args, **kwargs):
        assert not ({"reference", "verification"} & set(path.parts))
        return original_read_bytes(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_text)
    monkeypatch.setattr(Path, "read_bytes", guarded_bytes)
    case = load_public_case(view)
    assert case.case_id == "SYNTHETIC_PUBLIC"
    assert case.namespace_provenance == "EXACT_PROPOSER_REFERENCE"
    assert case.accessed_paths == (
        "members/A001.txt",
        "members/A002.txt",
        "members/A003.txt",
        "proposer_view.json",
        "symbols.json",
    )
    assert all("reference" not in item and "verification" not in item for item in case.accessed_paths)


def test_public_loader_accepts_contract_level_complete_status(tmp_path):
    path = _public_fixture(tmp_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["assumptions"]["status"] = "COMPLETE"
    _json(path, raw)
    case = load_public_case(path)
    assert case.assumption_statuses == {"P_REAL": "DECLARED"}


@pytest.mark.parametrize("forbidden", ["status", "verdict", "gold_program", "audited_depth"])
def test_public_loader_rejects_evaluator_fields_at_any_depth(tmp_path, forbidden):
    path = _public_fixture(tmp_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["assumptions"][forbidden] = "hidden"
    _json(path, raw)
    with pytest.raises(SearchContractError, match="PUBLIC_FIELD_FORBIDDEN"):
        load_public_case(path)


def test_public_loader_rejects_reference_paths_escape_and_hash_mismatch(tmp_path):
    path = _public_fixture(tmp_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["source_catalog"]["members"][0]["path"] = "reference/program.json"
    raw["source_catalog"]["members"][0]["sha256"] = hashlib.sha256(
        (tmp_path / "reference/program.json").read_bytes()
    ).hexdigest()
    _json(path, raw)
    with pytest.raises(SearchContractError, match="PUBLIC_PATH_FORBIDDEN"):
        load_public_case(path)

    path = _public_fixture(tmp_path / "escape")
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["source_catalog"]["members"][0]["path"] = "../outside.txt"
    _text(tmp_path / "outside.txt", "x")
    raw["source_catalog"]["members"][0]["sha256"] = hashlib.sha256(
        (tmp_path / "outside.txt").read_bytes()
    ).hexdigest()
    _json(path, raw)
    with pytest.raises(SearchContractError, match="PUBLIC_PATH_ESCAPE"):
        load_public_case(path)

    path = _public_fixture(tmp_path / "bad_hash")
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["source_catalog"]["members"][0]["sha256"] = "0" * 64
    _json(path, raw)
    with pytest.raises(SearchContractError, match="PUBLIC_HASH_MISMATCH"):
        load_public_case(path)


def test_candidate_pool_is_finite_deterministic_and_explicitly_incomplete(tmp_path):
    case = load_public_case(_public_fixture(tmp_path))
    first = extract_candidate_pool(case)
    second = extract_candidate_pool(case)
    assert first == second
    assert first.canonical_hash == second.canonical_hash
    assert first.branching_incomplete is True
    assert "FINITE_SOURCE_DERIVATION_IS_NOT_GLOBAL_EXPRESSION_ENUMERATION" in first.incompleteness_reasons
    assert any(item.extraction == "PAIRWISE_ANTI_UNIFICATION" for item in first.latents)
    assert all(
        item.role == "TAUTOLOGY_CONTROL"
        for item in first.latents
        if item.extraction == "SOURCE_LITERAL"
    )


def test_state_hash_is_order_and_alpha_invariant_but_member_ids_are_exact():
    left = SearchState(
        latent_objects=(
            LatentObject("F1", "FUNCTION_1", ("u",), "u + 1"),
            LatentObject("F0", "FUNCTION_1", ("v",), "v**2"),
        ),
        unexplained_members=("A002", "A001"),
        grammar_id="G_FULL",
    )
    right = SearchState(
        latent_objects=(
            LatentObject("F0", "FUNCTION_1", ("q",), "q**2"),
            LatentObject("F1", "FUNCTION_1", ("p",), "p + 1"),
        ),
        unexplained_members=("A001", "A002"),
        grammar_id="G_FULL",
    )
    assert left.canonical_hash == right.canonical_hash
    assert replace(right, unexplained_members=("A001", "A003")).canonical_hash != left.canonical_hash


def test_enumerative_order_is_deterministic_and_nondecreasing_complexity(tmp_path):
    case = load_public_case(_public_fixture(tmp_path))
    first = enumerative_search(case, budget=50)
    second = enumerative_search(case, budget=50)
    first_hashes = [item.canonical_hash for item in first.expanded_states]
    assert first_hashes == [item.canonical_hash for item in second.expanded_states]
    complexities = [item.complexity for item in first.expanded_states]
    assert complexities == sorted(complexities)
    assert first.states_expanded == first.budget_requested == 50
    assert first.ordering_uses_verifier_outcomes is False
    assert first.generated_frontier_exhaustive is True
    assert first.global_expression_enumeration_claimed is False


def test_s0_and_s1_share_the_exact_generated_child_frontier(tmp_path):
    case = load_public_case(_public_fixture(tmp_path))
    pool = extract_candidate_pool(case)
    policy = SearchPolicy()
    root = initial_state(case, grammar_id="G_FULL")
    expansion = expand_state(root, case, pool, policy)
    expected = tuple(item.canonical_hash for item in expansion.children)
    assert tuple(
        apply_action(root, action, case).canonical_hash
        for action in expansion.actions
    ) == expected
    enumerative = enumerative_search(
        case, budget=10, candidate_pool=pool, policy=policy
    )
    random = random_search(
        case, budget=10, seed=23, candidate_pool=pool, policy=policy
    )
    assert enumerative.expansion_trace[0].legal_child_hashes == expected
    assert random.expansion_trace[0].legal_child_hashes == expected
    assert enumerative.candidate_pool.canonical_hash == random.candidate_pool.canonical_hash


def test_random_search_is_seeded_reproducible_and_not_deterministic_enumeration(tmp_path):
    case = load_public_case(_public_fixture(tmp_path))
    first = random_search(case, budget=50, seed=41)
    replay = random_search(case, budget=50, seed=41)
    other = random_search(case, budget=50, seed=42)
    first_hashes = [item.canonical_hash for item in first.expanded_states]
    assert first_hashes == [item.canonical_hash for item in replay.expanded_states]
    assert first_hashes != [item.canonical_hash for item in other.expanded_states]
    assert first.states_expanded == first.budget_requested == 50


def test_only_frozen_budgets_are_accepted_and_expansions_are_counted_exactly(tmp_path):
    case = load_public_case(_public_fixture(tmp_path))
    assert BUDGET_STATES == (10, 50, 100, 500, 1000)
    for budget in (10, 50, 100):
        result = enumerative_search(case, budget=budget)
        assert result.states_expanded == budget
        assert [item.expansion_index for item in result.expansion_trace] == list(range(1, budget + 1))
    with pytest.raises(SearchContractError, match="STATE_BUDGET_NOT_FROZEN"):
        enumerative_search(case, budget=11)
    with pytest.raises(SearchContractError, match="STATE_BUDGET_NOT_FROZEN"):
        random_search(case, budget=11, seed=0)


def test_grammar_and_latent_object_ablations_change_only_legal_frontier(tmp_path):
    case = load_public_case(_public_fixture(tmp_path))
    pool = extract_candidate_pool(case)
    policy = SearchPolicy()
    full_root = initial_state(case, grammar_id="G_FULL")
    primitive_root = initial_state(case, grammar_id="G_PRIMITIVE")
    full_actions = legal_actions(full_root, case, pool, policy)
    primitive_actions = legal_actions(primitive_root, case, pool, policy)
    assert any(item.action == "CREATE_BASIS" for item in full_actions)
    assert all(item.action != "CREATE_BASIS" for item in primitive_actions)

    synthesis_ids = {
        item.candidate_id for item in pool.latents if item.role == "SEARCH_CANDIDATE"
    }
    latent_action = next(
        item
        for item in full_actions
        if item.action == "CREATE_LATENT"
        and item.payload["candidate_id"] in synthesis_ids
        and len(item.payload["parameters"]) == 1
    )
    full_latent = apply_action(full_root, latent_action, case)
    no_hermite_latent = replace(full_latent, grammar_id="G_NO_HERMITE")
    primitive_latent = replace(full_latent, grammar_id="G_PRIMITIVE")
    repeated_action = next(
        item for item in legal_actions(full_latent, case, pool, policy)
        if item.action == "ADD_REPEATED_NODE"
    )
    full_repeated = apply_action(full_latent, repeated_action, case)
    no_hermite_repeated = replace(full_repeated, grammar_id="G_NO_HERMITE")
    assert any(
        item.action == "ADD_HERMITE_DD"
        for item in legal_actions(full_repeated, case, pool, policy)
    )
    assert all(
        item.action != "ADD_HERMITE_DD"
        for item in legal_actions(no_hermite_repeated, case, pool, policy)
    )
    hermite = next(
        item
        for item in legal_actions(full_repeated, case, pool, policy)
        if item.action == "ADD_HERMITE_DD"
    )
    with pytest.raises(SearchContractError, match="ACTION_FORBIDDEN_BY_ABLATION"):
        apply_action(no_hermite_repeated, hermite, case)
    assert all(
        item.action not in {"ADD_NEWTON_DD", "ADD_HERMITE_DD", "ADD_RECURRENCE", "ADD_PERMUTATION"}
        for item in legal_actions(primitive_latent, case, pool, policy)
    )
    newton = next(
        item
        for item in legal_actions(full_latent, case, pool, policy)
        if item.action == "ADD_NEWTON_DD"
    )
    with pytest.raises(SearchContractError, match="ACTION_FORBIDDEN_BY_ABLATION"):
        apply_action(primitive_latent, newton, case)
    basis_payload = next(
        item.payload for item in full_actions if item.action == "CREATE_BASIS"
    )
    with pytest.raises(SearchContractError, match="ACTION_FORBIDDEN_BY_ABLATION"):
        apply_action(primitive_root, LegalAction("CREATE_BASIS", basis_payload), case)

    disabled = enumerative_search(
        case,
        budget=10,
        policy=SearchPolicy(latent_creation_enabled=False),
    )
    assert disabled.states_expanded == 1
    assert disabled.frontier_exhausted is True


def test_g_primitive_can_instantiate_and_execute_compose(tmp_path):
    case = load_public_case(_public_fixture(tmp_path))
    pool = extract_candidate_pool(case)
    policy = SearchPolicy()
    shared = next(
        item
        for item in pool.latents
        if item.extraction == "PAIRWISE_ANTI_UNIFICATION"
        and set(item.public_origins) == {"A001", "A002"}
        and len(item.parameters) == 1
    )
    state = initial_state(case, grammar_id="G_PRIMITIVE")
    create = next(
        item
        for item in legal_actions(state, case, pool, policy)
        if item.action == "CREATE_LATENT"
        and item.payload["candidate_id"] == shared.candidate_id
    )
    state = apply_action(state, create, case)
    assign_first = next(
        item
        for item in legal_actions(state, case, pool, policy)
        if item.action == "ADD_MEMBER"
        and item.payload.get("member_id") == "A001"
        and "latent_id" in item.payload
    )
    state = apply_action(state, assign_first, case)
    compose = next(
        item
        for item in legal_actions(state, case, pool, policy)
        if item.action == "ADD_COMPOSE"
    )
    state = apply_action(state, compose, case)
    assert state.operators[-1].operator == "COMPOSE"
    compose_output = state.operators[-1].output
    assign_composed = LegalAction("ADD_MEMBER", {
        "member_id": "A002",
        "output": compose_output,
    })
    state = apply_action(state, assign_composed, case)
    assert state.compiled_obligations[0]["status"] == "COMPILED"
    candidates = {
        item["member_id"]: item["candidate_expression"]
        for item in state.compiled_obligations
    }
    assert candidates["A002"] == "x + 2"


def test_g_primitive_compose_uses_outputs_from_a_distinct_inner_latent(tmp_path):
    case = load_public_case(_public_fixture(tmp_path))
    inner = LatentCandidate(
        candidate_id="LC_INNER",
        form="FUNCTION_1",
        parameters=("rps_p0",),
        expression="rps_p0**2",
        public_origins=("A001",),
        instance_maps=(("A001", (("rps_p0", "x"),)),),
        extraction="SYNTHETIC_SCHEMA",
    )
    outer = LatentCandidate(
        candidate_id="LC_OUTER",
        form="FUNCTION_2",
        parameters=("rps_a", "rps_b"),
        expression="rps_a + rps_b",
        public_origins=("A001", "A002"),
        extraction="SYNTHETIC_SCHEMA",
    )
    pool = CandidatePool(
        policy_version=CANDIDATE_POLICY_VERSION,
        latents=(inner, outer),
        node_values=("x", "y"),
        coefficients=("-1", "0", "1", "2", "Rational(1, 2)"),
        branching_incomplete=True,
        incompleteness_reasons=("SYNTHETIC_TEST_POOL",),
        source_member_count=len(case.members),
    )
    policy = SearchPolicy()
    state = initial_state(case, grammar_id="G_PRIMITIVE")
    for candidate_id in (inner.candidate_id, outer.candidate_id):
        create = next(
            item
            for item in legal_actions(state, case, pool, policy)
            if item.action == "CREATE_LATENT"
            and item.payload["candidate_id"] == candidate_id
        )
        state = apply_action(state, create, case)

    inner_id = f"F_{inner.candidate_id}"
    outer_id = f"F_{outer.candidate_id}"
    assign_value = next(
        item
        for item in legal_actions(state, case, pool, policy)
        if item.action == "ADD_MEMBER"
        and item.payload.get("latent_id") == inner_id
        and item.payload.get("member_id") == "A001"
    )
    state = apply_action(state, assign_value, case)
    value_output = state.operators[-1].output

    derivative = next(
        item
        for item in legal_actions(state, case, pool, policy)
        if item.action == "ADD_DERIVATIVE"
        and item.payload["latent_id"] == inner_id
        and item.payload["input"] is None
    )
    state = apply_action(state, derivative, case)
    derivative_output = state.operators[-1].output
    substitute = next(
        item
        for item in legal_actions(state, case, pool, policy)
        if item.action == "SUBSTITUTE_PARAMETER"
        and item.payload["latent_id"] == inner_id
        and item.payload["input"] == derivative_output
        and item.payload["value"] == "x"
    )
    state = apply_action(state, substitute, case)
    substituted_output = state.operators[-1].output

    compose = next(
        item
        for item in legal_actions(state, case, pool, policy)
        if item.action == "ADD_COMPOSE"
        and item.payload["latent_id"] == outer_id
        and item.payload["inputs"] == (value_output, substituted_output)
    )
    state = apply_action(state, compose, case)
    assert state.operators[-1].latent_id == outer_id
    assert state.operators[-1].inputs == (value_output, substituted_output)
    compose_output = state.operators[-1].output
    state = apply_action(state, LegalAction("ADD_MEMBER", {
        "member_id": "A002",
        "output": compose_output,
    }), case)
    assert all(
        item["status"] == "COMPILED" for item in state.compiled_obligations
    )
    candidates = {
        item["member_id"]: item["candidate_expression"]
        for item in state.compiled_obligations
    }
    assert candidates["A002"] == "x**2 + 2*x"


def test_duplicate_canonical_states_are_pruned(tmp_path):
    case = load_public_case(_public_fixture(tmp_path))
    result = enumerative_search(case, budget=50)
    hashes = [item.canonical_hash for item in result.expanded_states]
    assert len(hashes) == len(set(hashes))
    assert result.duplicate_states_pruned > 0


def test_source_literal_memorization_is_pre_verifier_ineligible(tmp_path, monkeypatch):
    case = load_public_case(_public_fixture(tmp_path))
    pool = extract_candidate_pool(case)
    literal = next(
        item
        for item in pool.latents
        if item.extraction == "SOURCE_LITERAL" and item.public_origins == ("A001",)
    )
    root = initial_state(case, grammar_id="G_FULL")
    create = next(
        item
        for item in legal_actions(root, case, pool, SearchPolicy())
        if item.action == "CREATE_LATENT"
        and item.payload["candidate_id"] == literal.candidate_id
    )
    latent = apply_action(root, create, case)
    literal_latent_id = latent.latent_objects[0].latent_id
    assert all(
        item.action == "ADD_MEMBER"
        for item in legal_actions(latent, case, pool, SearchPolicy())
        if item.payload.get("latent_id") == literal_latent_id
    )
    assign = next(
        item
        for item in legal_actions(latent, case, pool, SearchPolicy())
        if item.action == "ADD_MEMBER"
        and item.payload.get("member_id") == "A001"
        and "latent_id" in item.payload
    )
    # Search compilation must not attempt verification in order to detect the
    # IR-level byte-identical wrapper.
    monkeypatch.setattr(
        "symbolic_compactification.verify_equivalent",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("verifier called")),
    )
    memorized = apply_action(latent, assign, case)
    assert memorized.compiled_obligations[0]["status"] == "COMPILED"
    assert memorized.score["ineligible"] is True
    assert "TAUTOLOGICAL" in memorized.score["ineligibility_reasons"]
    assert memorized.verified_obligations == ()


def test_scoring_implements_frozen_formula_and_nonzero_hard_ineligibility(tmp_path):
    path = tmp_path / "members" / "A001.txt"
    digest = _text(path, "x + 1")
    source = SourceMember("A001", "members/A001.txt", digest)
    program = RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=(source,),
        latent_objects=(LatentObject("F0", "FUNCTION_1", ("u",), "u + 1"),),
        node_structures=(),
        operators=(Operator("OP0", "VALUE", "t0", "F0", arguments={"node": "x"}),),
        member_assignments=(MemberAssignment("A001", "t0", ("OP0",)),),
        assumptions_used=(),
        assumption_statuses={},
        obligations=(Obligation("O0", "A001", "t0"),),
    )
    breakdown = complexity_breakdown(program)
    assert breakdown.total == 7
    result = score_program(
        program,
        (ObligationEvidence("O0", "NONZERO"),),
    )
    assert result["coefficients"] == {"lambda1": 1, "lambda2": 1, "lambda3": 1, "lambda4": 2}
    assert result["coverage"] == {"numerator": 1, "denominator": 1}
    assert result["verified_relations"] == 0
    assert result["ineligible"] is True
    assert result["ineligibility_reasons"] == ["REQUIRED_NONZERO"]
    # Coverage 1 - complexity 7 - twice one exception = -8.
    assert result["score"] == {"numerator": -8, "denominator": 1}


def test_search_modules_do_not_import_evaluator_package_loader():
    search_root = Path("research/representation_program_search/search")
    imported: set[str] = set()
    names: set[str] = set()
    for path in search_root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
    assert "research.representation_program_search.program_ir.loader" not in imported
    assert "load_case_package" not in names
