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

Modes (``BUDGET_POLICY["mode"]``)
---------------------------------
* ``thread`` (default): the call runs in a worker thread; at the deadline an
  asynchronous exception is injected into the worker (CPython
  ``PyThreadState_SetAsyncExc``) so pure-Python runaways terminate promptly,
  and the caller raises ``BudgetExceeded`` either way. No re-import of the
  caller's ``__main__`` is required, so this mode works from scripts, REPLs,
  stdin and pytest alike.
* ``process``: a persistent single-worker spawn pool; on timeout the worker
  process is terminated outright (kills C-level loops too). Requires the
  calling program to be re-importable by the child (not true for
  ``python -`` / stdin), and picklable callables/arguments.
* ``inline``: budgets disabled (the call runs directly). Useful in debuggers
  or nested contexts.
"""
from __future__ import annotations

import ctypes
import multiprocessing
import threading
from typing import Any, Callable, Optional

from .models import AdapterError

__all__ = ["BudgetExceeded", "BUDGET_POLICY", "get_budget_policy",
           "set_budget_policy", "run_with_budget", "shutdown_budget_pool"]


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
# process-mode worker pool (persistent; rebuilt after a timeout kill)
# --------------------------------------------------------------------------- #

_pool = None
_pool_lock = threading.Lock()


def _worker_run(payload):
    """Module-level worker target (must be picklable)."""
    fn, args, kwargs = payload
    return fn(*args, **(kwargs or {}))


def _ensure_pool():
    global _pool
    if _pool is None:
        ctx = multiprocessing.get_context("spawn")
        _pool = ctx.Pool(1)
    return _pool


def _kill_pool():
    global _pool
    if _pool is not None:
        try:
            _pool.terminate()
            _pool.join()
        except Exception:
            pass
        _pool = None


def _run_process(fn, args, kwargs, seconds: float, operation: str):
    with _pool_lock:
        pool = _ensure_pool()
        async_res = pool.apply_async(_worker_run, ((fn, args, kwargs),))
        try:
            return async_res.get(timeout=seconds)
        except multiprocessing.TimeoutError:
            _kill_pool()  # terminate the runaway worker outright
            raise BudgetExceeded(operation, seconds) from None


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
    they do not forbid the attempt).
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
    """Tear down the persistent worker pool (test/exit hygiene)."""
    with _pool_lock:
        _kill_pool()
