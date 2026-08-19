"""Wall-clock budgets for expensive symbolic operations (fail-closed).

A runaway ``simplify`` / ``equals(0)`` must never hang the verifier. This
module runs budgeted calls in a separate worker PROCESS so a computation that
exceeds its budget can be terminated outright (a daemon thread cannot be
killed; a process can).

Fail-closed contract
--------------------
* Exceeding a budget raises ``BudgetExceeded`` (code ``TIME_BUDGET_EXCEEDED``).
* Callers must NEVER convert a budget timeout into ZERO or NONZERO; the only
  admissible verdict downstream is UNKNOWN with evidence
  ``{"kind": "TIME_BUDGET_EXCEEDED", "operation": ...}``.
* Worker exceptions propagate unchanged (they are not budget events).

Owned child-process lifecycle (process mode)
--------------------------------------------
Every worker this module spawns is ENGINE-OWNED and tracked in a module-level
registry (PID + process group). The lifecycle is strictly:

    spawn -> track -> operation finishes OR timeout/cancel
          -> SIGTERM to the owned process group
          -> bounded grace period (``kill_grace_seconds`` policy, default 2s)
          -> SIGKILL if still alive
          -> reap (waitpid via ``Process.join``/exitcode poll)

Workers lead their OWN process group: the worker target calls ``os.setsid()``
as its first action (the spawn-context equivalent of ``start_new_session``),
so pgid == pid and termination targets exactly that group.
Cleanup is guaranteed on ALL exit paths — success, timeout
(``BudgetExceeded``), exception, and (where interceptable) KeyboardInterrupt —
by the ``ProcessLifecycle`` context manager's try/finally semantics, plus an
``atexit`` hook (``sweep_owned_children``) that sweeps any still-owned
children when the CLI/interpreter exits. ``owned_children_snapshot()``
exposes the registry for tests/telemetry.

SAFETY RULE (absolute): this module NEVER uses ``pkill``/``killall`` and
NEVER signals anything that is not in the owned registry. Signals are sent
exclusively to the process groups of registry-tracked workers that this very
engine spawned.

Process telemetry (v0.2.2)
--------------------------
Every PROCESS-MODE budgeted operation records one telemetry record (thread /
inline modes spawn no owned process and record nothing): ``operation``,
``worker_pid``, ``started_at``, ``finished_at``, ``wall_time_seconds``,
``termination_reason`` (COMPLETED / TIMEOUT / EXCEPTION / CANCELLED),
``cleanup_status`` (CLEAN / FAILED), ``force_kill_required`` and
``owned_processes_remaining`` (empty when clean). The record of the most
recent process-mode operation is available via ``last_process_telemetry()``.
A cleanup failure (worker surviving the SIGKILL window) is NEVER hidden:
``cleanup_status`` becomes FAILED with the still-owned registry entries
listed, and the worker is re-tracked so the exit sweep retries. Only
engine-owned processes are ever listed — never unrelated processes.

Spawn safety: the worker target is a module-level function of this importable
package (NOT of the caller's ``__main__``), so process mode works from
scripts, pytest and stdin-invoked python alike. The payload (fn/args/kwargs)
must still be picklable; unpicklable callables fail closed with a clear
error rather than hanging.

Modes (``BUDGET_POLICY["mode"]``)
---------------------------------
* ``thread`` (default): the call runs in a worker thread; at the deadline an
  asynchronous exception is injected into the worker (CPython
  ``PyThreadState_SetAsyncExc``) so pure-Python runaways terminate promptly,
  and the caller raises ``BudgetExceeded`` either way. No re-import of the
  caller's ``__main__`` is required, so this mode works from scripts, REPLs,
  stdin and pytest alike.
* ``process``: one owned worker per budgeted call (see lifecycle above); on
  timeout the worker's owned process group is terminated outright (kills
  C-level loops too).
* ``inline``: budgets disabled (the call runs directly). Useful in debuggers
  or nested contexts.
"""
from __future__ import annotations

import atexit
import ctypes
import multiprocessing
import os
import pickle
import signal
import threading
import time
from typing import Any, Callable, Optional

from .models import AdapterError

__all__ = ["BudgetExceeded", "BUDGET_POLICY", "get_budget_policy",
           "set_budget_policy", "run_with_budget", "shutdown_budget_pool",
           "ProcessLifecycle", "owned_children_snapshot",
           "sweep_owned_children", "last_process_telemetry",
           "PROCESS_TELEMETRY_FIELDS"]

# Telemetry field inventory (v0.2.2): the exact keys every process-mode
# operation's telemetry record carries. Exposed for tests/contracts.
PROCESS_TELEMETRY_FIELDS = (
    "operation", "worker_pid", "started_at", "finished_at",
    "wall_time_seconds", "termination_reason", "cleanup_status",
    "force_kill_required", "owned_processes_remaining",
)

# termination_reason vocabulary (never a free-form string)
_TELEMETRY_COMPLETED = "COMPLETED"
_TELEMETRY_TIMEOUT = "TIMEOUT"
_TELEMETRY_EXCEPTION = "EXCEPTION"
_TELEMETRY_CANCELLED = "CANCELLED"


class BudgetExceeded(AdapterError):
    """A budgeted operation exceeded its wall-clock budget."""

    def __init__(self, operation: str, seconds: float):
        super().__init__("TIME_BUDGET_EXCEEDED")
        self.operation = operation
        self.seconds = seconds


# --------------------------------------------------------------------------- #
# budget policy (limits are POLICY, never silently edited constants)
# --------------------------------------------------------------------------- #

_DEFAULT_BUDGET_POLICY: dict = {
    "mode": "thread",              # thread | process | inline
    "simplify_seconds": 30.0,      # global simplify of a residual
    "probe_simplify_seconds": 10.0,  # per-probe simplify in the NONZERO branch
    "equals_seconds": 10.0,        # value.equals(0) adjudication per probe
    "expand_complex_seconds": 10.0,  # complex-normalization branch
    "transform_seconds": 15.0,     # targeted structural primitives
    # bounded grace between SIGTERM and SIGKILL of an owned worker group
    "kill_grace_seconds": 2.0,
}

BUDGET_POLICY: dict = dict(_DEFAULT_BUDGET_POLICY)


def get_budget_policy() -> dict:
    """Return a fresh copy of the current budget policy."""
    return dict(BUDGET_POLICY)


def set_budget_policy(**overrides) -> dict:
    """Update module-level budget policy. Unknown keys are rejected."""
    unknown = set(overrides) - set(_DEFAULT_BUDGET_POLICY)
    if unknown:
        raise AdapterError("BUDGET_POLICY_KEY_UNKNOWN")
    if "mode" in overrides and overrides["mode"] not in ("process", "thread", "inline"):
        raise AdapterError("BUDGET_POLICY_KEY_UNKNOWN")
    BUDGET_POLICY.update(overrides)
    return get_budget_policy()


# --------------------------------------------------------------------------- #
# engine-owned process registry (PID + process group; NEVER kill unowned)
# --------------------------------------------------------------------------- #

_OWNED: dict = {}
_REGISTRY_LOCK = threading.Lock()


def _track(proc, operation: str) -> None:
    """Register a freshly spawned worker as engine-owned."""
    with _REGISTRY_LOCK:
        _OWNED[proc.pid] = {
            "pid": proc.pid,
            # start_new_session=True makes the worker its own group leader
            "pgid": proc.pid,
            "operation": operation,
            "spawned_at": time.time(),
            "proc": proc,
        }


def _untrack(pid: int) -> Optional[dict]:
    with _REGISTRY_LOCK:
        return _OWNED.pop(pid, None)


def owned_children_snapshot() -> list:
    """Introspection helper (tests/telemetry): snapshot of the owned registry.

    Returns a list of ``{"pid", "pgid", "operation", "alive"}`` dicts, one
    per currently tracked worker. An empty list means no engine-owned
    children are outstanding.
    """
    with _REGISTRY_LOCK:
        entries = list(_OWNED.values())
    out = []
    for e in entries:
        try:
            alive = e["proc"].is_alive()
        except Exception:
            alive = False
        out.append({"pid": e["pid"], "pgid": e["pgid"],
                    "operation": e["operation"], "alive": alive})
    return out


def _signal_group(pgid: int, sig: int) -> bool:
    """Signal an OWNED process group only. False when nothing is left."""
    try:
        os.killpg(pgid, sig)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


def _terminate_entry(entry: dict) -> dict:
    """SIGTERM (owned group) -> bounded grace -> SIGKILL -> reap.

    Returns a cleanup result dict: ``{"force_kill_required": bool,
    "cleanup_ok": bool}``. ``cleanup_ok`` is False ONLY when the worker
    still cannot be reaped after the SIGKILL window — callers must surface
    that honestly (telemetry ``cleanup_status=FAILED``), never hide it.
    """
    proc = entry.get("proc")
    pgid = entry.get("pgid")
    try:
        grace = float(BUDGET_POLICY.get("kill_grace_seconds", 2.0))
    except (TypeError, ValueError):
        grace = 2.0
    if pgid is not None:
        _signal_group(pgid, signal.SIGTERM)
    if proc is None:
        return {"force_kill_required": False, "cleanup_ok": True}
    deadline = time.monotonic() + max(grace, 0.0)
    while time.monotonic() < deadline:
        try:
            if proc.exitcode is not None:  # exitcode poll reaps (waitpid)
                return {"force_kill_required": False, "cleanup_ok": True}
        except Exception:
            return {"force_kill_required": False, "cleanup_ok": True}
        time.sleep(0.01)
    if pgid is not None:
        _signal_group(pgid, signal.SIGKILL)
    try:
        proc.join(timeout=10.0)
    except Exception:
        pass
    try:
        reaped = proc.exitcode is not None
    except Exception:
        reaped = True
    return {"force_kill_required": True, "cleanup_ok": reaped}


def sweep_owned_children() -> list:
    """Terminate + reap every still-owned child. Returns swept PIDs.

    Registered with ``atexit`` so CLI/interpreter shutdown never leaks a
    worker; also safe to call explicitly (idempotent per PID).
    """
    with _REGISTRY_LOCK:
        pids = list(_OWNED)
    swept = []
    for pid in pids:
        entry = _untrack(pid)
        if entry is None:
            continue
        _terminate_entry(entry)
        swept.append(pid)
    return swept


atexit.register(sweep_owned_children)


# --------------------------------------------------------------------------- #
# process-mode telemetry (v0.2.2): one record per process-backed operation
# --------------------------------------------------------------------------- #

_TELEMETRY_LOCK = threading.Lock()
_LAST_PROCESS_TELEMETRY: Optional[dict] = None


def _iso_utc(epoch_seconds: float) -> str:
    """UTC ISO-8601 timestamp (same format as the session records)."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch_seconds))


def _record_process_telemetry(operation: str, proc, started_at: float,
                              finished_at: float, termination_reason: str,
                              lifecycle: Optional["ProcessLifecycle"]) -> dict:
    """Assemble + store the telemetry record of one process-mode operation.

    Called on EVERY exit path of a process-backed budgeted call (success,
    timeout, worker exception, cancellation). Never lists unrelated
    processes: ``owned_processes_remaining`` is drawn exclusively from the
    engine's owned registry, and is empty whenever cleanup was clean.
    """
    global _LAST_PROCESS_TELEMETRY
    # the lifecycle captures the worker pid BEFORE proc.close(); fall back to
    # a guarded direct read when no lifecycle was constructed (spawn failure)
    pid = getattr(lifecycle, "pid", None)
    if pid is None:
        try:
            pid = proc.pid if proc is not None else None
        except Exception:
            pid = None
    force_kill = bool(getattr(lifecycle, "force_kill_required", False))
    cleanup_ok = bool(getattr(lifecycle, "cleanup_ok", True))
    remaining = [] if cleanup_ok else owned_children_snapshot()
    record = {
        "operation": operation,
        "worker_pid": pid,
        "started_at": _iso_utc(started_at),
        "finished_at": _iso_utc(finished_at),
        "wall_time_seconds": round(max(finished_at - started_at, 0.0), 6),
        "termination_reason": termination_reason,
        "cleanup_status": "CLEAN" if cleanup_ok else "FAILED",
        "force_kill_required": force_kill,
        "owned_processes_remaining": remaining,
    }
    with _TELEMETRY_LOCK:
        _LAST_PROCESS_TELEMETRY = record
    return record


def last_process_telemetry() -> Optional[dict]:
    """Telemetry record of the most recent PROCESS-MODE budgeted operation.

    Returns a copy (or ``None`` when no process-mode operation has run in
    this process). Thread/inline mode operations spawn no owned process and
    therefore never produce a record. See ``PROCESS_TELEMETRY_FIELDS`` for
    the exact field inventory.
    """
    with _TELEMETRY_LOCK:
        record = _LAST_PROCESS_TELEMETRY
    if record is None:
        return None
    out = dict(record)
    out["owned_processes_remaining"] = list(record["owned_processes_remaining"])
    return out


class ProcessLifecycle:
    """Owned child-process lifecycle with try/finally guarantees.

    Usage::

        with ProcessLifecycle(proc, operation):
            proc.start()
            _track(proc, operation)
            ... wait for the result / enforce the budget ...
        # on ANY exit path the worker's owned process group is terminated
        # (SIGTERM -> grace -> SIGKILL) and reaped

    ``__exit__`` never suppresses exceptions.
    """

    def __init__(self, proc, operation: str):
        self.proc = proc
        self.operation = operation
        # cleanup outcome (populated by __exit__; read by telemetry)
        self.force_kill_required = False
        self.cleanup_ok = True
        # captured in __exit__ BEFORE close() — a closed process object
        # refuses .pid access, so telemetry reads the worker pid from here
        self.pid = None

    def __enter__(self) -> "ProcessLifecycle":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        proc = self.proc
        pid = getattr(proc, "pid", None)
        self.pid = pid
        if pid is not None:
            # untrack first so the atexit sweep cannot double-terminate
            entry = _untrack(pid)
            if entry is None:
                entry = {"pid": pid, "pgid": pid,
                         "operation": self.operation, "proc": proc}
            info = _terminate_entry(entry)
            self.force_kill_required = info["force_kill_required"]
            self.cleanup_ok = info["cleanup_ok"]
            if not self.cleanup_ok:
                # NEVER hide a surviving owned worker: re-track it so the
                # exit sweep retries, and let telemetry report FAILED with
                # the still-owned registry entries listed.
                with _REGISTRY_LOCK:
                    if pid not in _OWNED:
                        _OWNED[pid] = entry
        try:
            if proc is not None:
                proc.close()
        except Exception:
            pass
        return False


# --------------------------------------------------------------------------- #
# process-mode worker (one owned child per budgeted call)
# --------------------------------------------------------------------------- #

def _budget_worker(conn, payload):
    """Owned-child worker target. Module-level on purpose: it lives in this
    importable package (never in the caller's ``__main__``), so spawn works
    from scripts, pytest and stdin-invoked python alike."""
    # Own session/process group: makes pgid == pid, so the registry's group
    # kill targets exactly this worker and nothing else. setsid fails only if
    # already a group leader (never true for a freshly forked/spawned child),
    # so a failure is tolerated without losing the worker.
    try:
        os.setsid()
    except OSError:
        pass
    try:
        fn, args, kwargs = payload
        try:
            result = ("ok", fn(*args, **(kwargs or {})))
        except BaseException as exc:  # worker exceptions propagate unchanged
            result = ("error", exc)
        conn.send_bytes(pickle.dumps(result))
    except BaseException as exc:
        # payload/result could not round-trip pickle: fail loud, never hang
        try:
            conn.send_bytes(pickle.dumps(
                ("error", RuntimeError(
                    f"BUDGET_WORKER_TRANSFER_FAILED: {exc!r}"))))
        except BaseException:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _run_process(fn, args, kwargs, seconds: float, operation: str):
    """Run one budgeted call in a freshly spawned OWNED worker process.

    Every exit path (success, budget timeout, worker exception, cancellation
    via KeyboardInterrupt) records one process telemetry record — see
    ``last_process_telemetry()`` / ``PROCESS_TELEMETRY_FIELDS``.
    """
    started_at = time.time()
    termination_reason = _TELEMETRY_EXCEPTION
    lifecycle: Optional[ProcessLifecycle] = None
    proc = None
    parent_conn = None
    try:
        ctx = multiprocessing.get_context("spawn")
        parent_conn, child_conn = ctx.Pipe(duplex=False)
        proc = ctx.Process(target=_budget_worker,
                           args=(child_conn, (fn, args, kwargs)),
                           name=f"symbolic-budget-{operation}",
                           daemon=False)
        lifecycle = ProcessLifecycle(proc, operation)
        with lifecycle:
            proc.start()  # worker calls os.setsid(): own session, pgid == pid
            child_conn.close()  # the child owns its end now
            _track(proc, operation)
            deadline = time.monotonic() + max(float(seconds), 0.0)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    # BudgetExceeded escapes the with-block: __exit__ then
                    # terminates the owned worker group outright.
                    raise BudgetExceeded(operation, seconds)
                if parent_conn.poll(min(remaining, 0.05)):
                    tag, payload = pickle.loads(parent_conn.recv_bytes())
                    if tag == "ok":
                        termination_reason = _TELEMETRY_COMPLETED
                        return payload
                    raise payload
                if not proc.is_alive() and not parent_conn.poll(0):
                    raise RuntimeError("BUDGET_WORKER_DIED")
    except BudgetExceeded:
        termination_reason = _TELEMETRY_TIMEOUT
        raise
    except KeyboardInterrupt:
        # cancellation path (where interceptable): cleanup still happens in
        # ProcessLifecycle.__exit__, and telemetry records it as CANCELLED
        termination_reason = _TELEMETRY_CANCELLED
        raise
    finally:
        try:
            if parent_conn is not None:
                parent_conn.close()
        except Exception:
            pass
        # telemetry on EVERY exit path; never hides a cleanup failure
        _record_process_telemetry(operation, proc, started_at, time.time(),
                                  termination_reason, lifecycle)


# --------------------------------------------------------------------------- #
# thread-mode fallback (cooperative: the runaway thread is abandoned)
# --------------------------------------------------------------------------- #

def _run_thread(fn, args, kwargs, seconds: float, operation: str):
    box: dict = {}
    worker: dict = {}

    def _target():
        worker["tid"] = threading.get_ident()
        try:
            box["result"] = fn(*args, **(kwargs or {}))
        except BaseException as exc:  # includes the injected budget interrupt
            box["error"] = exc

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout=seconds)
    if t.is_alive():
        # Best-effort termination of a pure-Python runaway: inject an
        # asynchronous exception into the worker thread. C-level loops may not
        # observe it until they return to Python; the caller still raises
        # BudgetExceeded at the deadline either way.
        tid = worker.get("tid")
        if tid is not None:
            try:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_ulong(tid),
                    ctypes.py_object(BudgetExceeded))
            except Exception:
                pass
        raise BudgetExceeded(operation, seconds)
    if "error" in box and not isinstance(box["error"], BudgetExceeded):
        raise box["error"]
    return box.get("result")


# --------------------------------------------------------------------------- #
# public API
# --------------------------------------------------------------------------- #

def run_with_budget(fn: Callable, args: tuple = (), seconds: float = 30.0, *,
                    kwargs: Optional[dict] = None,
                    operation: str = "call",
                    mode: Optional[str] = None) -> Any:
    """Run ``fn(*args, **kwargs)`` under a wall-clock budget.

    Returns the call result, or raises:
      * ``BudgetExceeded`` when the budget elapses (fail-closed: never map
        this to ZERO/NONZERO downstream),
      * whatever exception ``fn`` itself raises (propagated unchanged).

    ``mode`` overrides ``BUDGET_POLICY['mode']`` for this single call.
    Non-positive budgets still execute the call once (budgets bound long work;
    they do not forbid the attempt). Process mode requires a picklable
    ``fn``/``args``/``kwargs``; every spawned worker is engine-owned and
    cleaned up per the module docstring's lifecycle.
    """
    effective_mode = mode or BUDGET_POLICY["mode"]
    if effective_mode == "inline":
        return fn(*args, **(kwargs or {}))
    seconds = float(seconds)
    if effective_mode == "thread":
        return _run_thread(fn, args, kwargs, seconds, operation)
    if effective_mode == "process":
        return _run_process(fn, args, kwargs, seconds, operation)
    raise AdapterError("BUDGET_POLICY_KEY_UNKNOWN")


def shutdown_budget_pool() -> None:
    """Exit hygiene: terminate + reap any still-owned budget workers.

    Retained for API compatibility. The persistent worker pool is gone; the
    owned-child registry sweep is the modern equivalent (also run at exit).
    """
    sweep_owned_children()
