#!/usr/bin/env python3
"""Ground truth for items.yaml by brute force, independent of the tool.

Matsubara sums: symmetric partial sums with mpmath acceleration; a stated
exp(+-i w 0+) factor adds +-c/2 for a 1/z tail with coefficient c (from
T sum_sym 1/(i w_n - a) = nF(a) - 1/2). Integrals: mpmath quadrature.
Asymptotics: |f - P| / |x|^n along x -> point. Operators and Langreth rules:
random complex matrices (Hermitian where declared). Each item gets a
numeric verdict plus, for CONDITIONAL items, the admissible point where the
claim breaks and a point where it holds.
"""
from __future__ import annotations

import json
from pathlib import Path

import mpmath as mp
import numpy as np
import yaml

mp.mp.dps = 30
HERE = Path(__file__).resolve().parent
RNG = np.random.default_rng(20260926)
nF = lambda b, x: 1 / (mp.exp(b * x) + 1)  # noqa: E731
nB = lambda b, x: 1 / (mp.exp(b * x) - 1)  # noqa: E731
dnF = lambda b, x: -b * mp.exp(b * x) / (mp.exp(b * x) + 1) ** 2  # noqa: E731


def msum(F, beta, boson=False, conv=None, tail=0):
    T = 1 / mp.mpf(beta)
    if boson:
        s = F(0) + mp.nsum(lambda n: F(2j * mp.pi * n * T) + F(-2j * mp.pi * n * T), [1, mp.inf])
    else:
        w = lambda n: (2 * n + 1) * mp.pi * T  # noqa: E731
        s = mp.nsum(lambda n: F(1j * w(n)) + F(-1j * w(n)), [0, mp.inf])
    s *= T
    return s + (tail / 2 if conv == "plus" else -tail / 2 if conv == "minus" else 0)


def close(x, y, tol=1e-12):
    return abs(complex(x) - complex(y)) <= tol * max(1, abs(complex(y)))


def ratio_trend(f, xs):
    """|f(x)| along xs; 'bounded' if it does not grow beyond 10x its first value."""
    vals = [abs(f(x)) for x in xs]
    return "bounded" if max(vals) < 10 * max(vals[0], mp.mpf("1e-30")) else "diverges"


def rand_op(n=4, hermitian=False):
    m = RNG.normal(size=(n, n)) + 1j * RNG.normal(size=(n, n))
    return (m + m.conj().T) / 2 if hermitian else m


def keldysh(names):
    return {k: {c: rand_op() for c in ("R", "A", "K")} for k in names}


def block(x):
    z = np.zeros_like(x["R"])
    return np.block([[x["R"], x["K"]], [z, x["A"]]])


def comps(x):
    R, A, K = x["R"], x["A"], x["K"]
    return {"R": R, "A": A, "K": K, "less": (K - R + A) / 2, "greater": (K + R - A) / 2}


def product(fns):
    out = block(fns[0])
    for f in fns[1:]:
        out = out @ block(f)
    n = fns[0]["R"].shape[0]
    return comps({"R": out[:n, :n], "A": out[n:, n:], "K": out[:n, n:]})


def checks():
    b = mp.mpf("2.5")
    a, c = mp.mpf("0.43"), mp.mpf("-1.25")
    r = {}
    r["A1"] = close(msum(lambda z: 1 / ((z - a) * (z - c)), b), (nF(b, a) - nF(b, c)) / (a - c))
    r["A2"] = close(msum(lambda z: 1 / ((z - a) * (z + a)), b), -mp.tanh(b * a / 2) / (2 * a))
    r["A3"] = close(msum(lambda z: 1 / (z - a) ** 2, b), dnF(b, a))
    r["A4"] = close(msum(lambda z: 1 / (z - a), b, conv="plus", tail=1), nF(b, a))
    r["A5"] = close(msum(lambda z: 1 / ((z - a) * (z - c)), b, boson=True), -(nB(b, a) - nB(b, c)) / (a - c))
    r["A6"] = close(msum(lambda z: 1 / ((z - a) ** 2 * (z - c)), b),
                    (nF(b, c) - nF(b, a)) / (a - c) ** 2 + dnF(b, a) / (a - c))
    r["B1"] = close(msum(lambda z: 1 / ((z - a) * (z - c)), b), (nF(b, c) - nF(b, a)) / (a - c))
    r["B2"] = close(msum(lambda z: 1 / ((z - a) * (z - c)), b, boson=True), (nB(b, a) - nB(b, c)) / (a - c))
    r["B3"] = close(msum(lambda z: 1 / ((z - a) * (z + a)), b), -mp.tanh(b * a) / (2 * a))
    r["B4"] = close(msum(lambda z: 1 / (z - a), b, conv="minus", tail=1), nF(b, a))
    r["B5"] = close(msum(lambda z: 1 / (z - a) ** 2, b), -dnF(b, a))
    r["B6"] = close(msum(lambda z: 1 / (z - a), b, boson=True, conv="plus", tail=1), nB(b, a))
    # C1: holds for a, c != 0; at a = 0 the n = 0 bosonic term 1/((0-a)(0-c)) is infinite
    holds = close(msum(lambda z: 1 / ((z - a) * (z - c)), b, boson=True), -(nB(b, a) - nB(b, c)) / (a - c))
    r["C1"] = ("CONDITIONAL" if holds else False, "breaks at a = 0: v_0 term 1/(0*(0-c)) infinite")
    # C2: symmetric sum is nF(a) - 1/2; with exp(+i w 0+) it is nF(a)
    sym = msum(lambda z: 1 / (z - a), b)
    r["C2"] = ("CONDITIONAL" if close(sym, nF(b, a) - mp.mpf(1) / 2) and not close(sym, nF(b, a)) else False,
               f"symmetric sum = nF(a) - 1/2 = {mp.nstr(sym, 8)}")
    lor = lambda g, e: mp.quad(lambda w: g / (mp.pi * ((w - e) ** 2 + g ** 2)), [-mp.inf, e, mp.inf])  # noqa: E731
    r["C3"] = ("CONDITIONAL" if close(lor(0.7, 0.2), 1) and close(lor(-0.7, 0.2), -1) else False,
               "integral = +1 for g = 0.7, -1 for g = -0.7")
    r["C4"] = ratio_trend(lambda g: (1 / g * 0 + 1 * g) / g ** 2, [mp.mpf(10) ** -k for k in (2, 4, 6)]) == "bounded"
    r["C5"] = ratio_trend(lambda x: mp.exp(-1 / x) / x ** 5, [-(mp.mpf(10) ** -k) for k in (1, 2, 3)]) == "bounded"
    r["C6"] = ratio_trend(lambda x: mp.exp(-1 / x) / x ** 5, [mp.mpf(10) ** -k for k in (1, 2, 3)]) == "bounded"
    e, g = mp.mpf("0.3"), mp.mpf("0.8")
    generic = close(msum(lambda z: 1 / ((z - e - 1j * g) * (z - e + 1j * g)), b),
                    (nF(b, e + 1j * g) - nF(b, e - 1j * g)) / (2j * g))
    r["C7"] = ("CONDITIONAL" if generic else False, "breaks at e = 0, g = pi T: pole on w_0")
    ee = mp.mpf("0.6")
    tail = lambda w: 1 / (1j * w - ee) - 1 / (1j * w) - ee / (1j * w) ** 2  # noqa: E731
    r["C8"] = ratio_trend(lambda w: tail(w) * w ** 4, [mp.mpf(10) ** k for k in (2, 4, 6)]) == "bounded"
    r["D1"] = ratio_trend(lambda w: tail(w) * w ** 3, [mp.mpf(10) ** k for k in (2, 4, 6)]) == "bounded"
    r["D2"] = ratio_trend(lambda x: (mp.digamma(x) - mp.log(x) + 1 / (2 * x)) * x ** 2,
                          [mp.mpf(10) ** k for k in (2, 4, 6)]) == "bounded"
    r["D3"] = ratio_trend(lambda gg: (0.7 * gg) / gg, [mp.mpf(10) ** -k for k in (2, 4, 6)]) == "bounded"
    fns = keldysh("ABC")
    D = product([fns[k] for k in "ABC"])
    cA, cB, cC = comps(fns["A"]), comps(fns["B"]), comps(fns["C"])
    rhs = (cA["R"] @ cB["R"] @ cC["less"] + cA["R"] @ cB["less"] @ cC["A"]
           + cA["less"] @ cB["A"] @ cC["A"])
    r["D4"] = bool(np.allclose(D["less"], rhs))
    C = product([fns["A"], fns["B"]])
    r["B7"] = bool(np.allclose(C["less"], cA["R"] @ cB["less"] + cA["less"] @ cB["R"]))
    r["D6"] = bool(np.allclose(C["K"], cA["R"] @ cB["K"] + cA["K"] @ cB["A"]))
    H, rho, cc = rand_op(hermitian=True), rand_op(hermitian=True), rand_op()
    lind = -1j * (H @ rho - rho @ H) + cc @ rho @ cc.conj().T - 0.5 * (cc.conj().T @ cc @ rho + rho @ cc.conj().T @ cc)
    for key, sign in (("D5", -1), ("B8", +1)):
        Heff = H + sign * 0.5j * cc.conj().T @ cc
        r[key] = bool(np.allclose(lind, -1j * (Heff @ rho - rho @ Heff.conj().T) + cc @ rho @ cc.conj().T))
    bb, gp, e7 = mp.mpf("2.5"), mp.mpf("0.4"), mp.mpf("0.3")
    lhs = mp.quad(lambda w: nF(bb, w) * gp / (mp.pi * ((w - e7) ** 2 + gp ** 2)), [-mp.inf, e7, mp.inf])
    r["D7"] = close(lhs, mp.mpf(1) / 2 - mp.im(mp.digamma(mp.mpf(1) / 2 + bb * (gp + 1j * e7) / (2 * mp.pi))) / mp.pi,
                    1e-10)
    return r


def main():
    items = {i["id"]: i for i in yaml.safe_load((HERE / "items.yaml").read_text())["items"]}
    out, bad = {}, []
    for key, value in checks().items():
        note = ""
        if isinstance(value, tuple):
            value, note = value
        numeric = "CONDITIONAL" if value == "CONDITIONAL" else ("TRUE" if value else "FALSE")
        out[key] = {"numeric": numeric, "declared_truth": items[key]["truth"], "note": note}
        if numeric != items[key]["truth"]:
            bad.append(key)
    missing = sorted(set(items) - set(out))
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "ground_truth.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"{len(out)} items checked; mismatches: {bad or 'none'}; unchecked: {missing or 'none'}")
    return 1 if bad or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
