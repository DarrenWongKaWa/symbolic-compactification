"""v0.2.2 audit-delta: process lifecycle DELTA tests (additive).

Extends ``test_process_lifecycle.py`` with the remaining audit cases:

* CASE D (cancellation) - an interceptable KeyboardInterrupt-style cancel
  through the process-mode budget machinery: cleanup STILL occurs (no owned
  child remains, worker reaped) and the telemetry ``termination_reason``
  reflects ``CANCELLED``.
* CASE E (unrelated-process protection, sweep/shutdown variant) - a
  test-spawned unrelated Python subprocess survives the engine's timeout +
  cleanup sweep AND ``shutdown_budget_pool``; the owned registry NEVER
  contains its PID (asserted by a continuous registry watcher). A
  pkill/name-matching implementation would fail this test.
* Telemetry field inventory - success AND timeout paths report
  ``cleanup_status == "CLEAN"`` with ``owned_processes_remaining == []``;
  every record carries ALL ``PROCESS_TELEMETRY_FIELDS`` with correct types.

Deterministic fixtures only: scripted sleeping workers (module-level, so
they are picklable by the spawn context), tiny budgets, short grace
periods.
"""
from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import threading
import time

import pytest

from symbolic_compactification import (
    BudgetExceeded,
    get_budget_policy,
    last_process_telemetry,
    owned_children_snapshot,
    run_with_budget,
    set_budget_policy,
    shutdown_budget_pool,
    sweep_owned_children,
)
from symbolic_compactification.budgets import PROCESS_TELEMETRY_FIELDS

_ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

# termination_reason vocabulary (mirrors budgets.py; never free-form)
_REASON_VOCABULARY = frozenset({"COMPLETED", "TIMEOUT", "EXCEPTION",
                                "CANCELLED"})


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
            return bool(path.read_text(encoding="utf-8").strip())
        except OSError:
            return False
    assert _wait_until(_present, timeout), "worker never reported its PID"
    return int(path.read_text(encoding="utf-8").strip())


def _assert_telemetry_shape(record: dict) -> None:
    """Every record carries ALL PROCESS_TELEMETRY_FIELDS with correct types."""
    assert record is not None, "no process telemetry was recorded"
    assert set(record) == set(PROCESS_TELEMETRY_FIELDS), \
        f"telemetry keys {sorted(record)} != {sorted(PROCESS_TELEMETRY_FIELDS)}"
    assert isinstance(record["operation"], str) and record["operation"]
    assert isinstance(record["worker_pid"], int)
    assert not isinstance(record["worker_pid"], bool)
    assert record["worker_pid"] > 0
    assert _ISO_UTC.match(record["started_at"]), record["started_at"]
    assert _ISO_UTC.match(record["finished_at"]), record["finished_at"]
    assert isinstance(record["wall_time_seconds"], (int, float))
    assert not isinstance(record["wall_time_seconds"], bool)
    assert record["wall_time_seconds"] >= 0.0
    assert record["termination_reason"] in _REASON_VOCABULARY
    assert record["cleanup_status"] in ("CLEAN", "FAILED")
    assert isinstance(record["force_kill_required"], bool)
    assert isinstance(record["owned_processes_remaining"], list)


# --------------------------------------------------------------------------- #
# CASE D (delta): interceptable cancellation -> cleanup + CANCELLED telemetry
# --------------------------------------------------------------------------- #

def test_case_d_cancel_cleanup_occurs_and_telemetry_says_cancelled(tmp_path):
    """A KeyboardInterrupt-style cancel raised into the budget polling loop
    is the documented interceptable cancellation path: the owned worker's
    process group is STILL terminated + reaped, no owned child remains, and
    the telemetry termination_reason is CANCELLED (never COMPLETED)."""
    pid_path = tmp_path / "worker_cancel.pid"
    set_budget_policy(mode="process", kill_grace_seconds=0.2)

    # Deliver SIGINT to the MAIN thread shortly after the worker is up: the
    # budget call is blocked in its polling loop on this thread, so the
    # signal surfaces there as KeyboardInterrupt — exactly the documented
    # interceptable cancel path. The 30s budget guarantees the deadline
    # itself can never fire first.
    def _cancel():
        signal.pthread_kill(threading.main_thread().ident, signal.SIGINT)

    timer = threading.Timer(0.8, _cancel)
    timer.daemon = True
    timer.start()
    try:
        with pytest.raises(KeyboardInterrupt):
            run_with_budget(_slow_pid_report_worker, (60.0, str(pid_path)),
                            seconds=30.0, operation="case-d-cancel")
    finally:
        timer.cancel()

    # cleanup still occurred on the cancellation path
    assert owned_children_snapshot() == []
    worker_pid = _read_pid_file(pid_path)
    assert _wait_until(lambda: not _pid_alive(worker_pid), timeout=15.0), \
        f"cancelled worker PID {worker_pid} survived the cancel cleanup"

    # telemetry termination_reason reflects the cancellation
    record = last_process_telemetry()
    _assert_telemetry_shape(record)
    assert record["operation"] == "case-d-cancel"
    assert record["termination_reason"] == "CANCELLED"
    assert record["cleanup_status"] == "CLEAN"
    assert record["owned_processes_remaining"] == []
    assert record["worker_pid"] == worker_pid


# --------------------------------------------------------------------------- #
# CASE E (delta): unrelated process survives timeout + sweep + shutdown;
# the registry NEVER contains its PID (fails any pkill/name-matching design)
# --------------------------------------------------------------------------- #

def test_case_e_unrelated_process_survives_sweep_and_shutdown(tmp_path):
    """Sweep/shutdown variant: while the engine runs one successful and one
    timed-out budgeted worker, a continuous watcher records EVERY owned
    registry snapshot; an unrelated test-spawned subprocess must appear in
    NONE of them, must survive sweep_owned_children() + shutdown_budget_pool()
    outright, and must never be in the swept PID list."""
    unrelated = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"])
    try:
        set_budget_policy(mode="process", kill_grace_seconds=0.2)

        snapshots: list = []
        stop = threading.Event()

        def _watch():
            while not stop.is_set():
                snapshots.append(owned_children_snapshot())
                time.sleep(0.02)

        watcher = threading.Thread(target=_watch, daemon=True)
        watcher.start()
        swept: list = []
        try:
            # one successful owned worker ...
            assert run_with_budget(_quick_add, (2, 3), seconds=30.0,
                                   operation="case-e-ok") == 5
            # ... and one timed-out owned worker ...
            pid_path = tmp_path / "worker_e.pid"
            with pytest.raises(BudgetExceeded):
                run_with_budget(_slow_pid_report_worker,
                                (60.0, str(pid_path)),
                                seconds=0.8, operation="case-e-slow")
            # ... then the explicit sweep + shutdown hygiene paths
            swept = sweep_owned_children()
            shutdown_budget_pool()
        finally:
            stop.set()
            watcher.join(timeout=5.0)
            assert not watcher.is_alive()

        # the unrelated process survived ALL engine cleanup paths
        assert unrelated.poll() is None, \
            "unrelated process was killed by sweep/shutdown"
        assert _pid_alive(unrelated.pid)

        # the owned registry NEVER contained its PID (every snapshot ever
        # taken is checked — a name/pid-matching kill list would show up)
        pids_ever_owned = {entry["pid"] for snap in snapshots
                           for entry in snap}
        assert unrelated.pid not in pids_ever_owned
        assert unrelated.pid not in swept
        assert owned_children_snapshot() == []
        # the watcher actually observed the engine's owned worker(s)
        assert pids_ever_owned, "watcher never saw any owned worker"
    finally:
        unrelated.terminate()
        try:
            unrelated.wait(timeout=10)
        except subprocess.TimeoutExpired:
            unrelated.kill()
            unrelated.wait(timeout=10)


# --------------------------------------------------------------------------- #
# telemetry field inventory on the success / timeout paths
# --------------------------------------------------------------------------- #

def test_success_path_telemetry_complete_clean_and_typed(tmp_path):
    """Success path: cleanup_status CLEAN, owned_processes_remaining [],
    termination_reason COMPLETED, and EVERY PROCESS_TELEMETRY_FIELDS entry
    present with the documented type."""
    pid_path = tmp_path / "worker_tel_ok.pid"
    set_budget_policy(mode="process")
    assert run_with_budget(_pid_report_worker, (7, str(pid_path)),
                           seconds=30.0, operation="telemetry-success") == 7

    record = last_process_telemetry()
    _assert_telemetry_shape(record)
    assert record["operation"] == "telemetry-success"
    assert record["termination_reason"] == "COMPLETED"
    assert record["cleanup_status"] == "CLEAN"
    assert record["force_kill_required"] is False
    assert record["owned_processes_remaining"] == []
    assert record["worker_pid"] == _read_pid_file(pid_path)
    assert owned_children_snapshot() == []


def test_timeout_path_telemetry_complete_clean_and_typed(tmp_path):
    """Timeout path: the killed worker still yields a COMPLETE telemetry
    record — cleanup_status CLEAN with owned_processes_remaining [] — plus
    termination_reason TIMEOUT."""
    pid_path = tmp_path / "worker_tel_timeout.pid"
    set_budget_policy(mode="process", kill_grace_seconds=0.2)

    with pytest.raises(BudgetExceeded):
        run_with_budget(_slow_pid_report_worker, (60.0, str(pid_path)),
                        seconds=0.8, operation="telemetry-timeout")

    record = last_process_telemetry()
    _assert_telemetry_shape(record)
    assert record["operation"] == "telemetry-timeout"
    assert record["termination_reason"] == "TIMEOUT"
    assert record["cleanup_status"] == "CLEAN"
    assert record["owned_processes_remaining"] == []
    assert record["worker_pid"] == _read_pid_file(pid_path)
    assert owned_children_snapshot() == []
