# HANDOFF — Track V5 Subagent V5-G (remainder sufficiency)

Branch: `work/v5-remainder`
Parent: `7102e8a3884e4f24da453c54f72263fbbb28f2ea`
Owned: `research/coefficient_laurent/remainder/`, `tests/test_cl_remainder.py`
Did not edit: `schema.py`, `cache.py`, `PROTOCOL.md`, freeze inputs, STATUS.
Import: `from research.coefficient_laurent.remainder import remainder_ok, required_pmin`
Tests: `.venv/bin/python -m pytest tests/test_cl_remainder.py -q`
No LLM.

## Sufficiency

Series through `t^0` is enough when the affine polygamma argument at
`t=0` is not a nonpositive integer: polygamma is holomorphic there, so
the given pole order `pmin` bounds the valuation and the tail is
`O(t) → 0`. `z=1+t` is ok; `z=t` is a pole at 0.

`remainder_ok is False` → remainder verdict UNKNOWN (not NONZERO).

## Remaining risks

- Symbolic `α` (spectator in the argument) is UNKNOWN even if a later
  assumption would exclude `Z_<=0`.
- Combined rational+polygamma pole order when sitting on a pole is not
  computed here; that is fail-closed, not a tighter `pmin`.
- Affine-in-`t` is required. Non-affine arguments are UNKNOWN.
