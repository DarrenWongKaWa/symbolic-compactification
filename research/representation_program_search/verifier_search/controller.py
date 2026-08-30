"""Recorded exact-verifier controller for search evaluation.

This module does not generate representation programs.  A method-neutral
frontier supplies public states and legal successors.  Complete eligible
states are compiled by M1 and each compiled equality is adjudicated through a
fresh persisted session (init -> set current -> step).  Only aggregate
ZERO/NONZERO/UNKNOWN/COMPILE_FAILURE feedback can reach the successor
expander.
"""
from __future__ import annotations

import hashlib
import heapq
import json
import os
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Callable, Iterable, Mapping

from symbolic_compactification import (
    AdapterError,
    adjudicate_candidate,
    init_session,
    load_expression,
    set_current,
)

from research.representation_program_search.program_ir import (
    CompilationResult,
    CompiledObligation,
    canonical_json,
    compile_program,
)

from .model import (
    EVALUATION_CONDITIONS,
    FEEDBACK_VALUES,
    FIXED_STATE_BUDGETS,
    FrontierContractError,
    VerifierFrontierNode,
    VerifierSearchPolicy,
    VerifierSearchResult,
)

SuccessorExpander = Callable[
    [VerifierFrontierNode, str | None], Iterable[VerifierFrontierNode]
]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: Mapping | list) -> str:
    return _sha256_bytes(canonical_json(value).encode("utf-8"))


def _file_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _atomic_write(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _atomic_json(path: Path, payload: Mapping) -> None:
    _atomic_write(
        path,
        (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
            "utf-8"
        ),
    )


def _safe_exception_code(exc: BaseException) -> str:
    if isinstance(exc, AdapterError):
        return exc.code
    if isinstance(exc, FrontierContractError):
        return exc.code
    return type(exc).__name__


def _obligation_payload(obligation: CompiledObligation) -> dict:
    return obligation.to_dict()


def _obligation_hash(obligation: CompiledObligation) -> str:
    return _sha256_json(_obligation_payload(obligation))


def _obligation_fingerprint(compilation: CompilationResult) -> str:
    """Exact, proof-free identity used for conservative dominance only."""
    rows = sorted(
        (
            {
                "candidate_expression": item.candidate_expression,
                "current_sha256": item.current_sha256,
                "member_id": item.member_id,
                "required": item.required,
            }
            for item in compilation.obligations
        ),
        key=canonical_json,
    )
    return _sha256_json(rows)


class _DominanceIndex:
    """Conservative exact-obligation dominance witness registry."""

    def __init__(self) -> None:
        self._best: dict[tuple[tuple[str, ...], str], tuple[int, str]] = {}

    def witness(
        self,
        node: VerifierFrontierNode,
        compilation: CompilationResult,
    ) -> str | None:
        coverage = tuple(
            sorted(item.member_id for item in node.program.member_assignments)
        )
        key = (coverage, _obligation_fingerprint(compilation))
        previous = self._best.get(key)
        if previous is not None and previous[0] < node.complexity:
            return previous[1]
        if previous is None or node.complexity < previous[0]:
            self._best[key] = (node.complexity, node.canonical_hash)
        return None


class VerifierSearchController:
    """Run exact evaluation over a public frontier under a fixed budget."""

    condition = "S6"

    def __init__(
        self,
        *,
        output_root: str | Path,
        budget: int,
        condition: str = "S6",
        llm_tokens_used: int = 0,
        policy: VerifierSearchPolicy | None = None,
        expander: SuccessorExpander | None = None,
    ) -> None:
        if budget not in FIXED_STATE_BUDGETS:
            raise FrontierContractError("STATE_BUDGET_NOT_FROZEN_CHECKPOINT")
        if condition not in EVALUATION_CONDITIONS:
            raise FrontierContractError("EVALUATION_CONDITION_UNKNOWN")
        if (
            not isinstance(llm_tokens_used, int)
            or isinstance(llm_tokens_used, bool)
            or llm_tokens_used < 0
        ):
            raise FrontierContractError("LLM_TOKEN_COUNT_INVALID")
        self.output_root = Path(output_root)
        self.budget = budget
        self.condition = condition
        self.llm_tokens_used = llm_tokens_used
        self.policy = policy or VerifierSearchPolicy()
        self.expander = expander

    def _initialize_output(self) -> None:
        if self.output_root.exists():
            try:
                next(self.output_root.iterdir())
            except StopIteration:
                pass
            else:
                raise FrontierContractError("OUTPUT_ROOT_NOT_EMPTY")
        else:
            self.output_root.mkdir(parents=True)
        (self.output_root / "decisions").mkdir(exist_ok=True)
        (self.output_root / "states").mkdir(exist_ok=True)
        policy_payload = self.policy.to_dict()
        _atomic_json(
            self.output_root / "controller.json",
            {
                "budget_requested": self.budget,
                "condition": self.condition,
                "feedback_guides_successors": self.expander is not None,
                "feedback_values": sorted(FEEDBACK_VALUES),
                "policy": policy_payload,
                "policy_hash": _sha256_json(policy_payload),
                "private_reasoning_recorded": False,
                "state_budget_unit": "STATES_EXPANDED",
            },
        )

    @staticmethod
    def _queue_key(
        node: VerifierFrontierNode, priority_band: int
    ) -> tuple:
        normalized_priority = tuple(
            (0, item) if isinstance(item, int) else (1, item)
            for item in node.public_priority
        )
        return (
            priority_band,
            normalized_priority,
            node.complexity,
            node.canonical_hash,
        )

    @staticmethod
    def _frontier_snapshot_hash(
        queue: list[tuple], queued: Mapping[str, tuple]
    ) -> str:
        rows = sorted(
            (
                {
                    "priority_band": item[0][0],
                    "queue_key": list(item[0]),
                    "state_hash": item[2].canonical_hash,
                }
                for item in queue
                if queued.get(item[2].canonical_hash) == item[0]
            ),
            key=lambda row: (canonical_json(row)),
        )
        return _sha256_json(rows)

    def _enqueue(
        self,
        queue: list[tuple],
        queued: dict[str, tuple],
        expanded: set[str],
        contracts: dict[str, str],
        node: VerifierFrontierNode,
        band: int,
        serial: int,
    ) -> tuple[int, bool]:
        state_hash = node.canonical_hash
        public_contract = node.to_public_dict()
        # Route provenance can legitimately differ when two action sequences
        # reach the same scientific state.  It never changes state identity.
        public_contract.pop("action_from_parent", None)
        public_contract.pop("parent_hash", None)
        public_contract.pop("depth", None)
        contract_hash = _sha256_json(public_contract)
        previous_contract = contracts.get(state_hash)
        if previous_contract is not None and previous_contract != contract_hash:
            raise FrontierContractError("DUPLICATE_STATE_METADATA_CONFLICT")
        contracts[state_hash] = contract_hash
        if state_hash in expanded:
            return serial, False
        key = self._queue_key(node, band)
        previous_key = queued.get(state_hash)
        if previous_key is not None and previous_key <= key:
            return serial, False
        # A state rediscovered through a better verifier band is reinserted.
        # The old heap entry becomes a harmless stale record and never counts
        # as a state expansion.
        heapq.heappush(queue, (key, serial, node))
        queued[state_hash] = key
        return serial + 1, True

    def _expand(
        self,
        node: VerifierFrontierNode,
        feedback: str | None,
    ) -> tuple[VerifierFrontierNode, ...]:
        if self.expander is None:
            return ()
        if feedback is not None and feedback not in FEEDBACK_VALUES:
            raise FrontierContractError(f"FEEDBACK_UNKNOWN:{feedback}")
        children = tuple(self.expander(node, feedback))
        if not all(isinstance(item, VerifierFrontierNode) for item in children):
            raise FrontierContractError("EXPANDER_RETURNED_INVALID_STATE")
        return children

    @staticmethod
    def _required_coverage_failure(
        node: VerifierFrontierNode,
        compilation: CompilationResult,
    ) -> str | None:
        assigned = {item.member_id for item in node.program.member_assignments}
        required = {
            item.member_id for item in compilation.obligations if item.required
        }
        if assigned != required:
            return "REQUIRED_OBLIGATION_COVERAGE_INCOMPLETE"
        return None

    def _adjudicate_obligation(
        self,
        *,
        node: VerifierFrontierNode,
        obligation: CompiledObligation,
        state_root: Path,
        ordinal: int,
    ) -> dict:
        started = time.perf_counter()
        obligation_hash = _obligation_hash(obligation)
        artifact_name = f"{ordinal:03d}-{obligation_hash[:16]}"
        obligations_root = state_root / "obligations"
        obligations_root.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{artifact_name}.", dir=obligations_root))
        final = obligations_root / artifact_name
        verdict = "COMPILE_FAILURE"
        failure_code: str | None = None
        adjudication_started = False
        evidence_payload: dict = {}
        try:
            candidate_path = staging / "input" / "candidate.txt"
            _atomic_write(
                candidate_path,
                (obligation.candidate_expression + "\n").encode("utf-8"),
            )
            current_path = node.context.package_root / obligation.current_path
            current = load_expression(
                current_path,
                node.context.symbols,
                functions=node.context.functions or None,
            )
            candidate = load_expression(
                candidate_path,
                node.context.symbols,
                functions=node.context.functions or None,
            )
            if (
                current.sha256 != obligation.current_sha256
                or current.text != obligation.current_expression
            ):
                raise FrontierContractError("COMPILED_SOURCE_DRIFT")
            if candidate.text != obligation.candidate_expression:
                raise FrontierContractError("COMPILED_CANDIDATE_DRIFT")

            # Persist stable artifact-relative provenance rather than staging
            # directory paths, which change when the directory is published.
            current.source_path = obligation.current_path
            candidate.source_path = "input/candidate.txt"
            meta = {
                "condition": self.condition,
                "obligation_hash": obligation_hash,
                "obligation_id": obligation.obligation_id,
                "program_id": node.program_id,
                "state_hash": node.canonical_hash,
            }
            session = init_session(
                str(staging / "verification"),
                meta=meta,
            )
            set_current(session, current, meta=meta)
            adjudication_started = True
            outcome = adjudicate_candidate(session, candidate, meta=meta)
            verdict = outcome.result.verdict
            run_root = Path(session.run_root)
            step_sha256 = _file_sha256(outcome.step_path)
            manifest_sha256 = _file_sha256(run_root / "manifest.json")
            final_current = run_root / "final" / "current.json"
            evidence_payload = {
                "candidate_artifact_sha256": candidate.sha256,
                "candidate_expression_sha256": _sha256_bytes(
                    obligation.candidate_expression.encode("utf-8")
                ),
                "current_sha256": current.sha256,
                "final_current_sha256": (
                    _file_sha256(final_current) if final_current.is_file() else None
                ),
                "manifest_sha256": manifest_sha256,
                "promoted": outcome.promoted,
                "run_id": session.run_id,
                "run_path": f"verification/runs/{session.run_id}",
                "step_path": (
                    f"verification/runs/{session.run_id}/steps/"
                    f"{outcome.step_path.name}"
                ),
                "step_sha256": step_sha256,
                "verdict": verdict,
                "verifier_wall_time_seconds": outcome.result.seconds,
            }
            semantic_evidence_inputs = {
                "candidate_expression_sha256": evidence_payload[
                    "candidate_expression_sha256"
                ],
                "current_sha256": current.sha256,
                "obligation_hash": obligation_hash,
                "verdict": verdict,
            }
        except Exception as exc:
            failure_code = _safe_exception_code(exc)
            # If adjudication may have begun but did not return a complete
            # persisted outcome, fail closed as UNKNOWN.  Setup/compile drift
            # before the verifier remains COMPILE_FAILURE.
            verdict = "UNKNOWN" if adjudication_started else "COMPILE_FAILURE"
            evidence_payload = {
                "failure_code": failure_code,
                "verdict": verdict,
            }
            semantic_evidence_inputs = {
                "failure_code": failure_code,
                "obligation_hash": obligation_hash,
                "verdict": verdict,
            }

        wall_time = time.perf_counter() - started
        payload = {
            "evidence": evidence_payload,
            "failure_code": failure_code,
            "member_id": obligation.member_id,
            "obligation_hash": obligation_hash,
            "obligation_id": obligation.obligation_id,
            "required": obligation.required,
            "schema_version": "RPSVerifierObligationDecisionV1",
            "semantic_evidence_hash_inputs": semantic_evidence_inputs,
            "semantic_evidence_hash": _sha256_json(semantic_evidence_inputs),
            "verdict": verdict,
            "wall_time_seconds": wall_time,
        }
        payload["evidence_record_hash"] = _sha256_json(payload)
        _atomic_json(staging / "evidence.json", payload)
        os.replace(staging, final)
        return {
            **payload,
            "artifact_path": final.relative_to(self.output_root).as_posix(),
        }

    @staticmethod
    def _aggregate_feedback(obligations: tuple[dict, ...]) -> str:
        required = [item["verdict"] for item in obligations if item["required"]]
        if not required:
            return "COMPILE_FAILURE"
        if "NONZERO" in required:
            return "NONZERO"
        if "COMPILE_FAILURE" in required:
            return "COMPILE_FAILURE"
        if "UNKNOWN" in required:
            return "UNKNOWN"
        if all(item == "ZERO" for item in required):
            return "ZERO"
        return "UNKNOWN"

    def _evaluate_complete(
        self,
        node: VerifierFrontierNode,
        state_root: Path,
        dominance: _DominanceIndex,
    ) -> dict:
        if node.assumption_clearance != "CLEARED":
            return {
                "compiled_obligations": (),
                "disposition": "PRE_VERIFICATION_INELIGIBLE",
                "feedback": None,
                "reason": (
                    "ASSUMPTIONS_INCOMPLETE"
                    if node.assumption_clearance == "INCOMPLETE"
                    else "ASSUMPTION_CLEARANCE_NOT_ESTABLISHED"
                ),
            }
        if node.leakage_status != "CLEARED":
            return {
                "compiled_obligations": (),
                "disposition": "PRE_VERIFICATION_INELIGIBLE",
                "feedback": None,
                "reason": (
                    "TARGET_LEAKAGE_FOUND"
                    if node.leakage_status == "FOUND"
                    else "TARGET_LEAKAGE_NOT_CLEARED"
                ),
            }

        compilation = compile_program(node.program, node.context)
        if compilation.status == "COMPILE_FAILURE":
            return {
                "compilation": compilation.to_dict(),
                "compiled_obligations": (),
                "disposition": "PRUNED",
                "feedback": "COMPILE_FAILURE",
                "reason": "COMPILE_FAILURE",
            }
        if compilation.tautological is True:
            return {
                "compilation": compilation.to_dict(),
                "compiled_obligations": (),
                "disposition": "PRE_VERIFICATION_INELIGIBLE",
                "feedback": None,
                "reason": "TAUTOLOGICAL_PROGRAM",
            }
        coverage_failure = self._required_coverage_failure(node, compilation)
        if coverage_failure is not None:
            return {
                "compilation": compilation.to_dict(),
                "compiled_obligations": (),
                "disposition": "PRUNED",
                "feedback": "COMPILE_FAILURE",
                "reason": coverage_failure,
            }
        dominated_by = dominance.witness(node, compilation)
        if dominated_by is not None:
            return {
                "compilation": compilation.to_dict(),
                "compiled_obligations": (),
                "disposition": "PRE_VERIFICATION_INELIGIBLE",
                "dominated_by": dominated_by,
                "feedback": None,
                "reason": "DOMINATED_EXACT_OBLIGATIONS",
            }

        obligation_rows = tuple(
            self._adjudicate_obligation(
                node=node,
                obligation=obligation,
                state_root=state_root,
                ordinal=index,
            )
            for index, obligation in enumerate(compilation.obligations, start=1)
        )
        feedback = self._aggregate_feedback(obligation_rows)
        return {
            "compilation": compilation.to_dict(),
            "compiled_obligations": obligation_rows,
            "disposition": {
                "ZERO": "PROGRAM_SUCCESS",
                "NONZERO": "PRUNED",
                "UNKNOWN": "RETAINED_LOWER_PRIORITY",
                "COMPILE_FAILURE": "PRUNED",
            }[feedback],
            "feedback": feedback,
            "reason": None,
        }

    def run(
        self,
        initial_states: Iterable[VerifierFrontierNode],
    ) -> VerifierSearchResult:
        """Execute one fixed-budget, deterministic-order S6 run."""
        self._initialize_output()
        started = time.perf_counter()
        queue: list[tuple] = []
        queued: dict[str, tuple] = {}
        expanded: set[str] = set()
        contracts: dict[str, str] = {}
        serial = 0
        duplicate_count = 0
        for node in initial_states:
            if not isinstance(node, VerifierFrontierNode):
                raise FrontierContractError("INITIAL_STATE_INVALID")
            serial, added = self._enqueue(
                queue,
                queued,
                expanded,
                contracts,
                node,
                self.policy.initial_priority_band,
                serial,
            )
            duplicate_count += int(not added)

        dominance = _DominanceIndex()
        decisions: list[dict] = []
        successes: list[str] = []
        retained_unknown: list[str] = []
        disposition_counts: Counter[str] = Counter()
        feedback_counts: Counter[str] = Counter()
        obligation_verdict_counts: Counter[str] = Counter()
        first_success: int | None = None
        time_to_first_success: float | None = None

        while queue and len(decisions) < self.budget:
            queue_key, _serial, node = heapq.heappop(queue)
            if queued.get(node.canonical_hash) != queue_key:
                continue
            snapshot_hash = self._frontier_snapshot_hash(
                [(queue_key, _serial, node), *queue], queued
            )
            queued.pop(node.canonical_hash)
            expanded.add(node.canonical_hash)
            index = len(decisions) + 1
            decision_started = time.perf_counter()
            state_root = self.output_root / "states" / f"state_{index:05d}"
            state_root.mkdir(parents=True, exist_ok=False)

            if node.complete:
                evaluation = self._evaluate_complete(node, state_root, dominance)
            else:
                evaluation = {
                    "compiled_obligations": (),
                    "disposition": "PARTIAL_EXPANDED",
                    "feedback": None,
                    "reason": "INCOMPLETE_PROGRAM",
                }
            feedback = evaluation["feedback"]
            if feedback is not None and feedback not in FEEDBACK_VALUES:
                raise FrontierContractError(f"FEEDBACK_UNKNOWN:{feedback}")

            should_expand = (
                evaluation["disposition"] not in {
                    "PRE_VERIFICATION_INELIGIBLE",
                }
                and (
                    feedback != "ZERO"
                    or self.policy.continue_after_success
                )
            )
            expander_failure: str | None = None
            try:
                children = self._expand(node, feedback) if should_expand else ()
            except Exception as exc:
                # The verifier evidence has already been atomically published.
                # Preserve the state decision before surfacing an infrastructure
                # failure so no scientific attempt becomes an orphaned record.
                children = ()
                expander_failure = _safe_exception_code(exc)
            child_band = (
                self.policy.initial_priority_band
                if feedback is None
                else self.policy.band_for_feedback(feedback)
            )
            legal_child_hashes: list[str] = []
            for child in children:
                serial, added = self._enqueue(
                    queue,
                    queued,
                    expanded,
                    contracts,
                    child,
                    child_band,
                    serial,
                )
                if added:
                    legal_child_hashes.append(child.canonical_hash)
                else:
                    duplicate_count += 1

            if feedback is not None:
                feedback_counts[feedback] += 1
            disposition = evaluation["disposition"]
            disposition_counts[disposition] += 1
            if disposition == "PROGRAM_SUCCESS":
                successes.append(node.canonical_hash)
                if first_success is None:
                    first_success = index
                    time_to_first_success = time.perf_counter() - started
            if disposition == "RETAINED_LOWER_PRIORITY":
                retained_unknown.append(node.canonical_hash)

            obligation_rows = evaluation.pop("compiled_obligations", ())
            for row in obligation_rows:
                obligation_verdict_counts[row["verdict"]] += 1
            decision_payload = {
                "decision_index": index,
                "disposition": disposition,
                "evaluation": evaluation,
                "expander_failure": expander_failure,
                "feedback_exposed_to_expander": feedback,
                "frontier_snapshot_hash": snapshot_hash,
                "legal_child_hashes": sorted(legal_child_hashes),
                "node": node.to_public_dict(),
                "obligations": list(obligation_rows),
                "ordering_key": list(queue_key),
                "private_reasoning_recorded": False,
                "schema_version": "RPSVerifierStateDecisionV1",
                "wall_time_seconds": time.perf_counter() - decision_started,
            }
            semantic_obligations = [
                {
                    "member_id": row["member_id"],
                    "obligation_hash": row["obligation_hash"],
                    "obligation_id": row["obligation_id"],
                    "required": row["required"],
                    "semantic_evidence_hash": row["semantic_evidence_hash"],
                    "verdict": row["verdict"],
                }
                for row in obligation_rows
            ]
            semantic_decision_inputs = {
                "action_from_parent": decision_payload["node"][
                    "action_from_parent"
                ],
                "assumption_clearance": node.assumption_clearance,
                "condition": self.condition,
                "decision_index": index,
                "disposition": disposition,
                "evaluation": evaluation,
                "feedback": feedback,
                "feedback_guides_successors": self.expander is not None,
                "frontier_snapshot_hash": snapshot_hash,
                "legal_child_hashes": sorted(legal_child_hashes),
                "leakage_status": node.leakage_status,
                "obligations": semantic_obligations,
                "ordering_key": list(queue_key),
                "parent_hash": decision_payload["node"]["parent_hash"],
                "program_id": node.program_id,
                "schema_version": "RPSVerifierSemanticDecisionV1",
                "state_hash": node.canonical_hash,
            }
            decision_payload["semantic_decision_hash_inputs"] = (
                semantic_decision_inputs
            )
            decision_payload["semantic_decision_hash"] = _sha256_json(
                semantic_decision_inputs
            )
            decision_hash = _sha256_json(decision_payload)
            decision_payload["decision_hash"] = decision_hash
            decision_path = (
                self.output_root / "decisions" / f"decision_{index:05d}.json"
            )
            _atomic_json(decision_path, decision_payload)
            decisions.append(decision_payload)
            if expander_failure is not None:
                raise FrontierContractError(
                    f"EXPANDER_FAILURE:{expander_failure}"
                )

        observed = len(decisions)
        success_at: dict[str, bool | None] = {}
        for checkpoint in FIXED_STATE_BUDGETS:
            key = f"SUCCESS@{checkpoint}"
            if checkpoint > self.budget:
                success_at[key] = None
            else:
                success_at[key] = (
                    first_success is not None and first_success <= checkpoint
                )
        decision_hashes = tuple(item["decision_hash"] for item in decisions)
        trace_hash = _sha256_json(list(decision_hashes))
        semantic_decision_hashes = tuple(
            item["semantic_decision_hash"] for item in decisions
        )
        semantic_trace_hash = _sha256_json(list(semantic_decision_hashes))
        result = VerifierSearchResult(
            condition=self.condition,
            budget_requested=self.budget,
            states_expanded=observed,
            frontier_exhausted=not queued,
            first_success_index=first_success,
            successful_state_hashes=tuple(successes),
            retained_unknown_state_hashes=tuple(retained_unknown),
            duplicate_states_pruned=duplicate_count,
            disposition_counts=dict(sorted(disposition_counts.items())),
            feedback_counts={
                value: feedback_counts.get(value, 0)
                for value in sorted(FEEDBACK_VALUES)
            },
            obligation_verdict_counts={
                value: obligation_verdict_counts.get(value, 0)
                for value in sorted(FEEDBACK_VALUES)
            },
            success_at=success_at,
            decision_hashes=decision_hashes,
            trace_hash=trace_hash,
            semantic_decision_hashes=semantic_decision_hashes,
            semantic_trace_hash=semantic_trace_hash,
            wall_time_seconds=time.perf_counter() - started,
            time_to_first_success_seconds=time_to_first_success,
            llm_tokens_used=self.llm_tokens_used,
            output_root=str(self.output_root),
            policy=self.policy,
        )
        _atomic_json(self.output_root / "result.json", result.to_dict())
        return result


def verifier_search(
    initial_states: Iterable[VerifierFrontierNode],
    *,
    output_root: str | Path,
    budget: int,
    condition: str = "S6",
    llm_tokens_used: int = 0,
    policy: VerifierSearchPolicy | None = None,
    expander: SuccessorExpander | None = None,
) -> VerifierSearchResult:
    """Functional entry point; defaults to verifier-guided condition S6."""
    return VerifierSearchController(
        output_root=output_root,
        budget=budget,
        condition=condition,
        llm_tokens_used=llm_tokens_used,
        policy=policy,
        expander=expander,
    ).run(initial_states)
