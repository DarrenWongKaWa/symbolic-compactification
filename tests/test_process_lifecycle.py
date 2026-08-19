"""Regression tests for the owned child-process lifecycle (v0.2.2 hardening).

Covers the process-mode budget machinery's cleanup contract (CASE A-D):
* CASE A - a successful bounded operation in process mode leaves NO
  engine-owned child afterwards (registry empty; recorded worker PID reaped).
* CASE B - a timed-out operation raises BudgetExceeded
  (TIME_BUDGET_EXCEEDED) AND leaves no engine-owned child; at verifier
  level the timeout surfaces as UNKNOWN with TIME_BUDGET_EXCEEDED evidence.
* CASE C - the exception path (worker raising; unpicklable payload)
  propagates the error unchanged and leaves no engine-owned child.
* CASE D - an UNRELATED process spawned by the test itself (never through
  the engine) survives the engine's timeout/shutdown/sweep paths: the
  engine only ever signals process groups of registry-tracked workers.
* ``sweep_owned_children`` / ``shutdown_budget_pool`` sweep still-owned
  children, and the owned registry only ever contains engine-spawned PIDs.

Deterministic fixtures only: scripted sleeping workers (module-level, so
they are picklable by the spawn context), tiny budgets, short grace
periods; no wall-clock races.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time

import pytest

from symbolic_compactification import (
    UNKNOWN,
    ZERO,
    NONZERO,
    BudgetExceeded,
    get_budget_policy,
    owned_children_snapshot,
    run_with_budget,
    set_budget_policy,
    shutdown_budget_pool,
    sweep_owned_children,
    verify_equivalent,
)

# --------------------------------------------------------------------------- #
# scripted workers (module-level: picklable by the spawn context)
# --------------------------------------------------------------------------- #


def _quick_add(a, b):
    """A fast, always-successful bounded operation."""
    return a + b


def _pid_report_worker(result, pid_path):
    """Records its own PID, then returns promptly (success path)."""
    with open(pid_path, "w", encoding="utf-8") as fh:
        fh.write(str(os.getpid()))
    return result


def _slow_pid_report_worker(duration, pid_path):
    """Records its own PID, then sleeps FAR past any tiny test budget."""
    with open(pid_path, "w", encoding="utf-8") as fh:
        fh.write(str(os.getpid()))
    time.sleep(duration)
    return "should never be returned"


def _raising_worker():
    raise ValueError("scripted worker failure")


# --------------------------------------------------------------------------- #
# helpers / fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture(autouse=True)
def _restore_budget_policy():
    """Every test sees the default policy; pool/registry hygiene on exit."""
    saved = get_budget_policy()
    yield
    shutdown_budget_pool()
    set_budget_policy(**saved)


def _pid_alive(pid: int) -> bool:
    """os.kill(pid, 0) probe: True while the PID exists (incl. zombie)."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _wait_until(predicate, timeout: float, interval: float = 0.02) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def _read_pid_file(path, timeout: float = 10.0) -> int:
    """Poll for the worker's self-reported PID (spawn import takes a bit)."""
    def _present():
        try:
            text = path.read_text(encoding="utf-8").strip()
            return bool(text)
        except OSError:
            return False
    assert _wait_until(_present, timeout), "worker never reported its PID"
    return int(path.read_text(encoding="utf-8").strip())


# --------------------------------------------------------------------------- #
# CASE A: successful bounded operation leaves no engine-owned child
# --------------------------------------------------------------------------- #

def test_case_a_success_leaves_no_owned_child_and_reaps_worker(tmp_path):
    pid_path = tmp_path / "worker_a.pid"
    set_budget_policy(mode="process")

    result = run_with_budget(_pid_report_worker, (42, str(pid_path)),
                             seconds=30.0, operation="case-a-success")
    assert result == 42

    # registry is empty on every exit path, including success
    assert owned_children_snapshot() == []

    # the recorded worker PID is reaped outright (not a zombie, not alive)
    worker_pid = _read_pid_file(pid_path)
    assert _wait_until(lambda: not _pid_alive(worker_pid), timeout=10.0), \
        f"worker PID {worker_pid} was not reaped after a successful call"


def test_case_a_plain_result_round_trip(tmp_path):
    set_budget_policy(mode="process")
    assert run_with_budget(_quick_add, (2, 3), seconds=30.0,
                           operation="case-a-add") == 5
    assert owned_children_snapshot() == []


# --------------------------------------------------------------------------- #
# CASE B: timeout -> TIME_BUDGET_EXCEEDED, worker terminated and reaped
# --------------------------------------------------------------------------- #

def test_case_b_timeout_raises_budget_exceeded_and_reaps_worker(tmp_path):
    pid_path = tmp_path / "worker_b.pid"
    set_budget_policy(mode="process", kill_grace_seconds=0.2)

    with pytest.raises(BudgetExceeded) as excinfo:
        run_with_budget(_slow_pid_report_worker, (60.0, str(pid_path)),
                        seconds=0.8, operation="case-b-slow")
    assert excinfo.value.code == "TIME_BUDGET_EXCEEDED"
    assert excinfo.value.operation == "case-b-slow"

    worker_pid = _read_pid_file(pid_path)
    # registry empty immediately after the budget kill path returns
    assert owned_children_snapshot() == []
    # SIGTERM -> grace -> SIGKILL -> reap: the PID must be gone (grace 0.2s
    # keeps this fast; allow generous slack for scheduling only)
    assert _wait_until(lambda: not _pid_alive(worker_pid), timeout=15.0), \
        f"timed-out worker PID {worker_pid} survived the kill path"


def test_case_b_verifier_level_timeout_is_unknown_with_evidence():
    """A verifier adjudication that blows its budget in PROCESS mode must
    fail closed to UNKNOWN with TIME_BUDGET_EXCEEDED evidence — never
    ZERO/NONZERO — and must leave no engine-owned child."""
    saved = get_budget_policy()
    try:
        # a sub-millisecond simplify budget is always exceeded by the
        # spawn-context worker startup alone: deterministic timeout
        set_budget_policy(mode="process", simplify_seconds=0.0005)
        result = verify_equivalent(
            "(x**2 - 1)/(x - 1)", "x + 1",
            [{"name": "x", "real": True, "nonzero": True}])
    finally:
        shutdown_budget_pool()
        set_budget_policy(**saved)

    assert result.verdict == UNKNOWN
    assert result.verdict not in (ZERO, NONZERO)
    kinds = {e.get("kind") for e in result.evidence}
    assert "TIME_BUDGET_EXCEEDED" in kinds
    assert owned_children_snapshot() == []


# --------------------------------------------------------------------------- #
# CASE C: exception / cancel paths leave no engine-owned child
# --------------------------------------------------------------------------- #

def test_case_c_worker_exception_propagates_and_leaves_no_child():
    set_budget_policy(mode="process")
    with pytest.raises(ValueError, match="scripted worker failure"):
        run_with_budget(_raising_worker, (), seconds=30.0,
                        operation="case-c-raise")
    assert owned_children_snapshot() == []


def test_case_c_budget_exceeded_propagation_leaves_no_child(tmp_path):
    """BudgetExceeded is itself the cancel path: after it propagates to the
    caller, the worker group must already be terminated + reaped."""
    pid_path = tmp_path / "worker_c.pid"
    set_budget_policy(mode="process", kill_grace_seconds=0.2)
    try:
        run_with_budget(_slow_pid_report_worker, (60.0, str(pid_path)),
                        seconds=0.8, operation="case-c-cancel")
        raise AssertionError("expected BudgetExceeded")
    except BudgetExceeded as exc:
        assert exc.code == "TIME_BUDGET_EXCEEDED"
    assert owned_children_snapshot() == []


def test_case_c_unpicklable_payload_fails_closed_without_leaking():
    """Process mode requires a picklable payload; an unpicklable callable
    must fail loud (never hang) and leave nothing owned behind."""
    set_budget_policy(mode="process")
    with pytest.raises(Exception):
        run_with_budget(lambda: 1, (), seconds=5.0,
                        operation="case-c-unpicklable")
    assert owned_children_snapshot() == []


# --------------------------------------------------------------------------- #
# CASE D: unrelated (non-engine) processes are NEVER touched
# --------------------------------------------------------------------------- #

def test_case_d_unrelated_process_survives_timeout_and_shutdown(tmp_path):
    """A plain subprocess spawned by the TEST (never through the engine)
    must survive the engine's budget timeout AND the shutdown sweep: the
    engine signals exclusively registry-tracked owned process groups."""
    unrelated = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"])
    try:
        pid_path = tmp_path / "worker_d.pid"
        set_budget_policy(mode="process", kill_grace_seconds=0.2)
        with pytest.raises(BudgetExceeded):
            run_with_budget(_slow_pid_report_worker, (60.0, str(pid_path)),
                            seconds=0.8, operation="case-d-timeout")
        # explicit shutdown/sweep while the unrelated process is alive
        swept = sweep_owned_children()
        shutdown_budget_pool()

        assert unrelated.poll() is None, "unrelated process was killed"
        assert _pid_alive(unrelated.pid)
        # nothing engine-owned remains, and the unrelated PID was never
        # part of the owned registry (nothing left to have contained it)
        assert owned_children_snapshot() == []
        assert unrelated.pid not in swept
    finally:
        unrelated.terminate()
        try:
            unrelated.wait(timeout=10)
        except subprocess.TimeoutExpired:
            unrelated.kill()
            unrelated.wait(timeout=10)


def test_case_d_registry_never_contains_non_engine_pids(tmp_path):
    """While exactly one budgeted worker is running, the owned registry
    holds exactly ONE entry whose PID is the engine worker's own PID —
    never an unrelated process's PID."""
    unrelated = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"])
    try:
        pid_path = tmp_path / "worker_d2.pid"
        set_budget_policy(mode="process", kill_grace_seconds=0.2)

        observations: list = []

        def _observe():
            worker_pid = _read_pid_file(pid_path)
            _wait_until(lambda: len(owned_children_snapshot()) == 1,
                        timeout=5.0)
            observations.extend((worker_pid, owned_children_snapshot()))

        observer = threading.Thread(target=_observe)
        observer.start()
        try:
            # budgeted call blocks THIS thread until the deadline; the
            # observer inspects the registry mid-flight
            with pytest.raises(BudgetExceeded):
                run_with_budget(_slow_pid_report_worker,
                                (60.0, str(pid_path)),
                                seconds=2.5, operation="case-d-registry")
        finally:
            observer.join(timeout=10)
            assert not observer.is_alive()

        worker_pid, snapshot = observations[0], observations[1]
        assert len(snapshot) == 1
        entry = snapshot[0]
        # the registry carries EXACTLY the engine's worker: its own PID and
        # its own session group (pgid == pid after setsid) — never the
        # unrelated test-spawned process
        assert entry["pid"] == worker_pid
        assert entry["pgid"] == worker_pid
        assert entry["operation"] == "case-d-registry"
        assert entry["pid"] != unrelated.pid
        # after the kill path, the registry is empty again
        assert owned_children_snapshot() == []
    finally:
        unrelated.terminate()
        try:
            unrelated.wait(timeout=10)
        except subprocess.TimeoutExpired:
            unrelated.kill()
            unrelated.wait(timeout=10)


# --------------------------------------------------------------------------- #
# sweep / shutdown hygiene
# --------------------------------------------------------------------------- #

def test_sweep_owned_children_terminates_outstanding_worker(tmp_path):
    """sweep_owned_children() terminates + reaps a still-tracked worker
    mid-operation (the budget_shutdown() equivalent of the hardening)."""
    pid_path = tmp_path / "worker_sweep.pid"
    set_budget_policy(mode="process", kill_grace_seconds=0.2)

    def _drive():
        try:
            return run_with_budget(_slow_pid_report_worker,
                                   (60.0, str(pid_path)),
                                   seconds=30.0, operation="sweep-target")
        except Exception:
            # expected: the sweep kills the worker out from under this call;
            # the exact escape (BudgetExceeded / BUDGET_WORKER_DIED / pipe
            # EOF mid-poll) is not under test here — the sweep's effect is
            return None

    driver = threading.Thread(target=_drive)
    driver.start()
    try:
        worker_pid = _read_pid_file(pid_path)
        assert _wait_until(lambda: len(owned_children_snapshot()) == 1,
                           timeout=5.0)

        swept = sweep_owned_children()
        assert worker_pid in swept
        assert owned_children_snapshot() == []
        assert _wait_until(lambda: not _pid_alive(worker_pid), timeout=15.0)
    finally:
        driver.join(timeout=30)
    # the driver observed the killed worker (never a silent hang)
    assert not driver.is_alive()
    # idempotent: sweeping again finds nothing
    assert sweep_owned_children() == []


def test_shutdown_budget_pool_is_safe_and_leaves_nothing_owned():
    """shutdown_budget_pool() (the retained API name) sweeps the registry
    and is safe to call repeatedly with no outstanding workers."""
    shutdown_budget_pool()
    shutdown_budget_pool()
    assert owned_children_snapshot() == []
