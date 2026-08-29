"""Typed Landau ``O(t^k)`` / ``o(t^k)`` algebra as ``t → 0``.

No heuristic truncation: a present term is never dropped, and two
same-order exact monomials are ``O``, not cancelled. Division is
``UNKNOWN`` unless the denominator's leading coefficient is certified
nonzero. A remainder that vanishes through ``t^0`` is not hop ZERO.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Union

UNKNOWN = "UNKNOWN"
BIG_O = "O"
LITTLE_O = "o"
KEEP_THROUGH = 0

_KINDS = (BIG_O, LITTLE_O)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_int(value: Any, name: str) -> int:
    if not _is_int(value):
        raise TypeError(f"{name} must be an int, got {type(value)!r}")
    return value


def _require_var(variable: Any) -> str:
    if not isinstance(variable, str) or not variable or len(variable) > 32:
        raise ValueError(f"variable must be a short non-empty str, got {variable!r}")
    return variable


def _fmt_power(variable: str, exponent: int) -> str:
    if exponent == 0:
        return "1"
    if exponent == 1:
        return variable
    if exponent > 1:
        return f"{variable}^{exponent}"
    return f"{variable}^{{{exponent}}}"


def _fmt_landau(kind: str, variable: str, exponent: int) -> str:
    if exponent == 0:
        return f"{kind}(1)"
    return f"{kind}({_fmt_power(variable, exponent)})"


@dataclass(frozen=True)
class Order:
    """Landau class ``O(t^k)`` or ``o(t^k)`` as ``t → 0``."""

    kind: str
    exponent: int
    variable: str = "t"

    def __post_init__(self) -> None:
        if self.kind not in _KINDS:
            raise ValueError(f"kind must be 'O' or 'o', got {self.kind!r}")
        _require_int(self.exponent, "exponent")
        _require_var(self.variable)

    def __str__(self) -> str:
        return _fmt_landau(self.kind, self.variable, self.exponent)


@dataclass(frozen=True)
class ExactPower:
    """Monomial ``c t^m`` as ``t → 0``.

    ``leading_certified_nonzero=False`` forbids division by this term.
    """

    exponent: int
    leading_certified_nonzero: bool = True
    variable: str = "t"

    def __post_init__(self) -> None:
        _require_int(self.exponent, "exponent")
        if not isinstance(self.leading_certified_nonzero, bool):
            raise TypeError("leading_certified_nonzero must be bool")
        _require_var(self.variable)

    def __str__(self) -> str:
        body = _fmt_power(self.variable, self.exponent)
        if self.leading_certified_nonzero:
            return body
        return f"({body}, leading uncertified)"


@dataclass(frozen=True)
class ExactZero:
    """The zero remainder. Vanishes as ``t → 0``."""

    variable: str = "t"

    def __post_init__(self) -> None:
        _require_var(self.variable)

    def __str__(self) -> str:
        return "0"


@dataclass(frozen=True)
class AnalyticExpansion:
    """Certified ``f(w) = Σ c_n w^n + R(w)`` as ``w → 0``.

    ``terms`` lists *present* powers as ``(n, certified_nonzero)``.
    Omitted powers are certified zero. A present coefficient that is
    not certified nonzero is kept as an ``O`` summand; it is never
    dropped. ``remainder`` is a Landau class in ``variable``.
    """

    remainder: Order
    terms: tuple[tuple[int, bool], ...] = ()
    variable: str = "w"

    def __post_init__(self) -> None:
        if not isinstance(self.remainder, Order):
            raise TypeError("remainder must be an Order")
        _require_var(self.variable)
        if self.remainder.variable != self.variable:
            raise ValueError("remainder variable must match expansion variable")
        seen: dict[int, bool] = {}
        for item in self.terms:
            if not isinstance(item, tuple) or len(item) != 2:
                raise TypeError("terms must be (power, certified_nonzero) pairs")
            power, nz = item
            _require_int(power, "term power")
            if not isinstance(nz, bool):
                raise TypeError("certified_nonzero must be bool")
            if power in seen:
                raise ValueError(f"duplicate expansion power {power}")
            seen[power] = nz
        object.__setattr__(
            self, "terms", tuple(sorted(seen.items(), key=lambda kv: kv[0]))
        )


Operand = Union[Order, ExactPower, ExactZero]


def O(exponent: int, variable: str = "t") -> Order:
    """``O(t^k)`` as ``t → 0``."""
    return Order(BIG_O, exponent, variable)


def o(exponent: int, variable: str = "t") -> Order:
    """``o(t^k)`` as ``t → 0``."""
    return Order(LITTLE_O, exponent, variable)


big_o = O
little_o = o


def exact_power(
    exponent: int,
    *,
    leading_certified_nonzero: bool = True,
    variable: str = "t",
) -> ExactPower:
    """Certified monomial ``c t^m`` (default ``c ≠ 0``)."""
    return ExactPower(
        exponent,
        leading_certified_nonzero=leading_certified_nonzero,
        variable=variable,
    )


def zero(*, variable: str = "t") -> ExactZero:
    return ExactZero(variable=variable)


def taylor_expansion(kept_degree: int, *, variable: str = "w") -> AnalyticExpansion:
    """Taylor polynomial through ``w^{kept_degree}`` plus ``O(w^{N+1})``.

    Coefficients of ``w^0 … w^N`` are present but not certified nonzero.
    Use ``compose_remainder`` when only the remainder class is needed.
    """
    n = _require_int(kept_degree, "kept_degree")
    terms = tuple((k, False) for k in range(n + 1)) if n >= 0 else ()
    return AnalyticExpansion(
        remainder=Order(BIG_O, n + 1, variable),
        terms=terms,
        variable=variable,
    )


def add(left: Any, right: Any) -> Any:
    """Sum of Landau classes / exact monomials. Fail-closed ``UNKNOWN``."""
    a = _coerce(left)
    b = _coerce(right)
    if a is None or b is None:
        return UNKNOWN
    if _var(a) != _var(b):
        return UNKNOWN
    if isinstance(a, ExactZero):
        return b
    if isinstance(b, ExactZero):
        return a
    ca = _as_class(a)
    cb = _as_class(b)
    if ca is None or cb is None:
        return UNKNOWN
    if ca.exponent < cb.exponent:
        return _from_class(ca)
    if cb.exponent < ca.exponent:
        return _from_class(cb)
    return _from_class(_add_same_exponent(ca, cb))


def mul(left: Any, right: Any) -> Any:
    """Product of Landau classes / exact monomials. Fail-closed ``UNKNOWN``."""
    a = _coerce(left)
    b = _coerce(right)
    if a is None or b is None:
        return UNKNOWN
    if _var(a) != _var(b):
        return UNKNOWN
    if isinstance(a, ExactZero) or isinstance(b, ExactZero):
        return ExactZero(variable=_var(a))
    ca = _as_class(a)
    cb = _as_class(b)
    if ca is None or cb is None:
        return UNKNOWN
    exp = ca.exponent + cb.exponent
    if ca.kind == "exact" and cb.kind == "exact":
        return ExactPower(exp, True, ca.variable)
    if ca.kind == LITTLE_O or cb.kind == LITTLE_O:
        return Order(LITTLE_O, exp, ca.variable)
    return Order(BIG_O, exp, ca.variable)


def div(numer: Any, denom: Any) -> Any:
    """Quotient. ``UNKNOWN`` unless ``denom`` has certified nonzero leading coefficient."""
    a = _coerce(numer)
    b = _coerce(denom)
    if a is None or b is None:
        return UNKNOWN
    if _var(a) != _var(b):
        return UNKNOWN
    if isinstance(b, ExactZero):
        return UNKNOWN
    if isinstance(b, Order):
        return UNKNOWN
    if isinstance(b, ExactPower):
        if not b.leading_certified_nonzero:
            return UNKNOWN
        return mul(a, ExactPower(-b.exponent, True, b.variable))
    return UNKNOWN


def sum_orders(*terms: Any) -> Any:
    """Finite sum. Empty sum is exact zero."""
    if not terms:
        return ExactZero()
    acc: Any = terms[0]
    for item in terms[1:]:
        acc = add(acc, item)
        if acc is UNKNOWN:
            return UNKNOWN
    return acc


def prod_orders(*terms: Any) -> Any:
    """Finite product. Empty product is the exact unit ``t^0``."""
    if not terms:
        return ExactPower(0, True, "t")
    acc: Any = terms[0]
    for item in terms[1:]:
        acc = mul(acc, item)
        if acc is UNKNOWN:
            return UNKNOWN
    return acc


def compose(expansion: Any, inner: Any) -> Any:
    """``f(inner)`` from a certified analytic expansion as the inner → 0."""
    if not isinstance(expansion, AnalyticExpansion):
        return UNKNOWN
    acc = _compose_landau(expansion.remainder, inner)
    if acc is UNKNOWN:
        return UNKNOWN
    for power, certified_nz in expansion.terms:
        piece = _power_inner(inner, power)
        if piece is UNKNOWN:
            return UNKNOWN
        if not certified_nz:
            piece = _as_landau_bound(piece)
            if piece is UNKNOWN:
                return UNKNOWN
        acc = add(acc, piece)
        if acc is UNKNOWN:
            return UNKNOWN
    return acc


def compose_remainder(expansion: Any, inner: Any) -> Any:
    """Remainder class of ``f(inner)`` after the certified polynomial."""
    if not isinstance(expansion, AnalyticExpansion):
        return UNKNOWN
    return _compose_landau(expansion.remainder, inner)


def times_prefactor(term: Any, m: Any, *, variable: Optional[str] = None) -> Any:
    """Multiply by the exact monomial ``t^{-m}`` (coefficient 1, certified nonzero)."""
    if not _is_int(m):
        return UNKNOWN
    coerced = _coerce(term)
    if coerced is None:
        return UNKNOWN
    var = variable if variable is not None else _var(coerced)
    if not isinstance(var, str):
        return UNKNOWN
    return mul(ExactPower(-m, True, var), coerced)


def remainder_times_prefactor(N: Any, m: Any, *, variable: str = "t") -> Any:
    """``t^{-m} * O(t^{N+1}) = O(t^{N+1-m})``."""
    if not _is_int(N) or not _is_int(m):
        return UNKNOWN
    try:
        _require_var(variable)
    except (TypeError, ValueError):
        return UNKNOWN
    return mul(ExactPower(-m, True, variable), Order(BIG_O, N + 1, variable))


def vanishes_through_constant(term: Any) -> Any:
    """Whether the class is certified to vanish as ``t → 0`` after keeping ``t^{…}`` through ``t^0``.

    ``O(t^k)`` vanishes iff ``k >= 1``. ``o(t^k)`` vanishes iff ``k >= 0``.
    ``O(1)`` does not vanish. This is not hop ZERO.
    """
    x = _coerce(term)
    if x is None:
        return UNKNOWN
    if isinstance(x, ExactZero):
        return True
    if isinstance(x, ExactPower):
        if x.exponent > KEEP_THROUGH:
            return True
        if x.leading_certified_nonzero:
            return False
        return UNKNOWN
    if isinstance(x, Order):
        if x.kind == BIG_O:
            return x.exponent > KEEP_THROUGH
        if x.kind == LITTLE_O:
            return x.exponent >= KEEP_THROUGH
    return UNKNOWN


def sufficient_expansion_order(N: Any, m: Any, *, variable: str = "t") -> Any:
    """True iff ``N+1-m >= 1``, i.e. ``t^{-m} O(t^{N+1})`` vanishes through ``t^0``."""
    rem = remainder_times_prefactor(N, m, variable=variable)
    if rem is UNKNOWN:
        return UNKNOWN
    return vanishes_through_constant(rem)


def is_unknown(value: Any) -> bool:
    return value == UNKNOWN


# --- internals --------------------------------------------------------------


@dataclass(frozen=True)
class _Class:
    kind: str
    exponent: int
    variable: str


def _coerce(value: Any) -> Optional[Operand]:
    if value is UNKNOWN or value is None:
        return None
    if isinstance(value, (Order, ExactPower, ExactZero)):
        return value
    return None


def _var(value: Operand) -> str:
    return value.variable


def _as_class(value: Operand) -> Optional[_Class]:
    if isinstance(value, ExactZero):
        return None
    if isinstance(value, ExactPower):
        if value.leading_certified_nonzero:
            return _Class("exact", value.exponent, value.variable)
        return _Class(BIG_O, value.exponent, value.variable)
    if isinstance(value, Order):
        return _Class(value.kind, value.exponent, value.variable)
    return None


def _from_class(cls: _Class) -> Operand:
    if cls.kind == "exact":
        return ExactPower(cls.exponent, True, cls.variable)
    return Order(cls.kind, cls.exponent, cls.variable)


def _add_same_exponent(a: _Class, b: _Class) -> _Class:
    # No cancellation of two exact monomials of equal order.
    if a.kind == "exact" and b.kind == LITTLE_O:
        return a
    if b.kind == "exact" and a.kind == LITTLE_O:
        return b
    if a.kind == LITTLE_O and b.kind == LITTLE_O:
        return _Class(LITTLE_O, a.exponent, a.variable)
    return _Class(BIG_O, a.exponent, a.variable)


def _as_landau_bound(value: Any) -> Any:
    x = _coerce(value)
    if x is None:
        return UNKNOWN
    if isinstance(x, ExactZero):
        return x
    if isinstance(x, ExactPower):
        return Order(BIG_O, x.exponent, x.variable)
    return x


def _tends_to_zero(value: Operand) -> bool:
    if isinstance(value, ExactZero):
        return True
    if isinstance(value, ExactPower):
        return value.exponent > KEEP_THROUGH
    if isinstance(value, Order):
        if value.kind == BIG_O:
            return value.exponent > KEEP_THROUGH
        if value.kind == LITTLE_O:
            return value.exponent >= KEEP_THROUGH
    return False


def _compose_landau(outer: Order, inner: Any) -> Any:
    """Substitute ``w = inner`` into a Landau class in ``w``.

    Negative outer exponents need a certified exact inner valuation:
    an ``O`` upper bound on ``w`` does not bound ``w^{-p}``.
    """
    if not isinstance(outer, Order):
        return UNKNOWN
    w = _coerce(inner)
    if w is None:
        return UNKNOWN
    if not _tends_to_zero(w):
        return UNKNOWN
    p = outer.exponent
    var = _var(w)
    if isinstance(w, ExactZero):
        if p > 0:
            return ExactZero(variable=var)
        if p == 0:
            return Order(outer.kind, 0, var)
        return UNKNOWN
    if isinstance(w, ExactPower):
        if p < 0 and not w.leading_certified_nonzero:
            return UNKNOWN
        return Order(outer.kind, p * w.exponent, var)
    if isinstance(w, Order):
        if p < 0:
            return UNKNOWN
        if p == 0:
            return Order(outer.kind, 0, var)
        kind = LITTLE_O if (outer.kind == LITTLE_O or w.kind == LITTLE_O) else BIG_O
        return Order(kind, p * w.exponent, var)
    return UNKNOWN


def _power_inner(inner: Any, n: int) -> Any:
    w = _coerce(inner)
    if w is None or not _is_int(n):
        return UNKNOWN
    if n == 0:
        return ExactPower(0, True, _var(w))
    if n < 0:
        inv = div(ExactPower(0, True, _var(w)), w)
        if inv is UNKNOWN:
            return UNKNOWN
        return _power_inner(inv, -n)
    if isinstance(w, ExactZero):
        return ExactZero(variable=_var(w))
    cls = _as_class(w)
    if cls is None:
        return UNKNOWN
    exp = cls.exponent * n
    if cls.kind == "exact":
        return ExactPower(exp, True, cls.variable)
    return Order(cls.kind, exp, cls.variable)
