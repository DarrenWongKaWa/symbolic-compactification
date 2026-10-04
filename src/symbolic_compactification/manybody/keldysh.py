"""Langreth rules through the Keldysh-space (Larkin-Ovchinnikov) algebra.

On the Keldysh contour a convolution C = A B maps to the product of
upper-triangular matrices

    A -> [[A_R, A_K], [0, A_A]],   A_K = A_less + A_greater,
    A_R - A_A = A_greater - A_less,

with operator (time-convolution) products left noncommutative. Reading off
the components of the matrix product gives the Langreth rules, e.g.

    C_less = A_R B_less + A_less B_A,      C_R = A_R B_R,
    D_less = A_R B_R C_less + A_R B_less C_A + A_less B_A C_A.

``verify_langreth`` expands a claimed component formula in the independent
components (R, A, K) and compares it with the matrix product in the free
algebra, which is an exact decision. The mapping of contour products to
triangular matrices is the Langreth theorem; results are therefore
CERTIFIED_BY_RULE (rule LANGRETH_KELDYSH_ALGEBRA). Pointwise products
A(t,t') B(t,t') (bubbles) are not matrix products and are not handled here.
"""
from __future__ import annotations

from typing import Iterable, Mapping

import sympy

from ..models import AdapterError
from ._common import CERTIFIED_BY_RULE, NONZERO, UNKNOWN, certificate_hash, text_hash
from .noncommutative import OperatorSpace, free_algebra_residual

LANGRETH_KELDYSH_ALGEBRA = "LANGRETH_KELDYSH_ALGEBRA"
COMPONENTS = ("R", "A", "K", "less", "greater")


def _component_names(functions: Iterable[str]) -> list[str]:
    return [f"{f}_{c}" for f in functions for c in COMPONENTS]


def _matrix(space: OperatorSpace, name: str) -> sympy.Matrix:
    o = space.ops
    return sympy.Matrix([[o[f"{name}_R"], o[f"{name}_K"]], [0, o[f"{name}_A"]]])


def _to_independent(space: OperatorSpace, functions: Iterable[str]) -> dict:
    """less/greater in terms of R, A, K."""
    o, subs = space.ops, {}
    for f in functions:
        R, A, K = o[f"{f}_R"], o[f"{f}_A"], o[f"{f}_K"]
        subs[o[f"{f}_less"]] = (K - R + A) / 2
        subs[o[f"{f}_greater"]] = (K + R - A) / 2
    return subs


def _component(matrix: sympy.Matrix, component: str) -> sympy.Expr:
    R, A, K = matrix[0, 0], matrix[1, 1], matrix[0, 1]
    return {"R": R, "A": A, "K": K, "less": (K - R + A) / 2,
            "greater": (K + R - A) / 2}[component]


def verify_langreth(product: Iterable[str], component: str, claim: str) -> Mapping:
    """Check  (product)_component == claim  on the Keldysh contour.

    ``product`` lists contour functions in order, e.g. ["A", "B", "C"] for
    D = A B C. ``claim`` uses names like A_R, B_less, C_A, A_K, B_greater.
    """
    product = list(product)
    inputs = {"rule": LANGRETH_KELDYSH_ALGEBRA, "product": product,
              "component": component, "claim_sha256": text_hash(claim)}
    if component not in COMPONENTS or not product or len(set(product)) != len(product):
        return {**inputs, "status": UNKNOWN, "reasons": ["LANGRETH_SPEC_INVALID"]}
    try:
        space = OperatorSpace(_component_names(product))
        claimed = space.parse(claim)
    except AdapterError as exc:
        return {**inputs, "status": UNKNOWN, "reasons": [f"PARSE_FAILED:{exc.code}"]}
    total = sympy.eye(2)
    for name in product:
        total = total * _matrix(space, name)
    exact = _component(total, component)
    residual = free_algebra_residual(exact, claimed.subs(_to_independent(space, product)))
    if residual == 0:
        cert = {**inputs, "status": CERTIFIED_BY_RULE}
        return {**cert, "reasons": [], "certificate_hash": certificate_hash(cert)}
    commuting = sympy.expand(residual.xreplace(
        {x: sympy.Symbol(x.name) for x in residual.free_symbols if not x.is_commutative}))
    if commuting == 0:
        # wrong only in the order of factors: right for commuting scalars (a single
        # level in the steady state), wrong for matrices and time convolutions
        return {**inputs, "status": UNKNOWN, "reasons": ["LANGRETH_ORDER_ONLY"],
                "residual": str(sympy.expand(residual))[:2000]}
    return {**inputs, "status": NONZERO, "reasons": ["LANGRETH_COMPONENT_MISMATCH"],
            "residual": str(sympy.expand(residual))[:2000]}
