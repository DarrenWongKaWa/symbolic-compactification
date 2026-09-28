#!/usr/bin/env python3
"""Benchmark v1, part 2: derivation chains from Guo et al., arXiv:2511.16422
(public). Steps are taken from Supplementary Secs. A and C.

Ground truth is numerical: bath integrals by quadrature, Taylor coefficients
in w by a Cauchy contour integral (which avoids removable singularities at
w = 0), and O(Gamma) claims by the scaling of the remainder. Seeded steps
carry one planted error.
"""
from __future__ import annotations

import mpmath as mp

mp.mp.dps = 25
P = dict(beta=mp.mpf("3.1"), G=mp.mpf("0.23"), mu=mp.mpf("0.12"),
         en=mp.mpf("-0.31"), em=mp.mpf("0.47"), el=mp.mpf("0.09"))


class Guo:
    def __init__(self, beta, G, mu, **_):
        self.b, self.G, self.mu = beta, G, mu

    def f0(self, e):
        return 1 / (mp.exp(self.b * (e - self.mu)) + 1)

    def zp(self, e, G=None):
        G = self.G if G is None else G
        return mp.mpf(1) / 2 + self.b / (2 * mp.pi) * (G + 1j * (e - self.mu))

    def zm(self, e, G=None):
        G = self.G if G is None else G
        return mp.mpf(1) / 2 + self.b / (2 * mp.pi) * (G - 1j * (e - self.mu))

    def fp(self, e):
        return mp.mpf(1) / 2 + 1j / mp.pi * mp.digamma(self.zp(e))

    def fm(self, e):
        return mp.mpf(1) / 2 - 1j / mp.pi * mp.digamma(self.zm(e))

    def rho0(self, e):
        return (self.fp(e) + self.fm(e)) / 2

    # --- bath-integral definitions (Eqs. SM_rho0, SM_rho1, SM_rho2)
    def lor(self, wb):
        return 2 * self.G / (wb ** 2 + self.G ** 2) / (2 * mp.pi)

    def bath(self, g):
        return mp.quad(lambda wb: self.lor(wb) * g(wb), [-mp.inf, -1, 0, 1, mp.inf])

    def rho0_bath(self, e):
        return self.bath(lambda wb: self.f0(e + wb))

    def rho1_bath(self, em, en, w):
        G = self.G
        return self.bath(lambda wb: (self.f0(en + wb) - self.f0(em - wb)) / (w + wb + (en - em) + 1j * G))

    def rho2_bath(self, em, el, en, w1, w2):
        G = self.G
        enm, elm, enl = en - em, el - em, en - el

        def g(wb):
            return (self.f0(em - wb) / ((w1 + w2 + wb + enm + 1j * G) * (w1 + wb + elm + 1j * G))
                    + self.f0(en + wb) / ((w1 + w2 + wb + enm + 1j * G) * (w2 + wb + enl + 1j * G))
                    - self.f0(el + wb) / ((w1 + wb + elm + 1j * G) * (w2 - wb + enl + 1j * G)))
        return self.bath(g)

    # --- residue forms (Eqs. rho_0_supp, tilde-rho_1_supp, tilde-rho_2_supp)
    def rp1(self, w, em, en, seeded=False):
        shifted = em + w if seeded else em - w
        return 1j * self.G * (self.fp(en) - self.fp(shifted)) / (w + en - em)

    def rm1(self, w, em, en):
        return 1j * self.G * (self.fm(en + w) - self.fm(em)) / (w + en - em)

    def rho1_res(self, em, en, w, seeded=False):
        d = w + en - em + 2j * self.G
        return (self.rho0(en) - self.rho0(em) + self.rp1(w, em, en, seeded) + self.rm1(w, em, en)) / d

    def rho2_res(self, em, el, en, w1, w2):
        s = w1 + w2 + en - em
        rp2 = (self.rp1(w2, el, en) - self.rp1(w1, em - w2, el - w2)) / s
        rm2 = (self.rm1(w2, el + w1, en + w1) - self.rm1(w1, em, el)) / s
        return (self.rho1_res(el, en, w2) - self.rho1_res(em, el, w1) + rp2 + rm2) / (s + 2j * self.G)


def taylor_coeff(func, k, radius):
    """k-th Taylor coefficient at 0 by the Cauchy integral on |w| = radius."""
    val = mp.quad(lambda t: func(radius * mp.expj(t)) * mp.expj(-k * t), [0, mp.pi, 2 * mp.pi])
    return val / (2 * mp.pi * radius ** k)


def close(a, b, tol):
    return abs(a - b) <= tol * max(1, abs(b))


def bounded(vals):
    return max(abs(v) for v in vals) < 10 * max(abs(vals[0]), mp.mpf("1e-30"))


g = Guo(**P)
R = min(P["G"], abs(P["em"] - P["en"])) / 4


def g1_1():
    e = P["en"]
    return close(g.rho0_bath(e), g.rho0(e), mp.mpf("1e-15"))


def g1_2():
    e = P["em"]
    small = Guo(P["beta"], mp.mpf("1e-12"), P["mu"])
    return close(small.rho0(e), small.f0(e), mp.mpf("1e-9"))


def g1_3(seeded=True):
    em, en, w = P["em"], P["en"], mp.mpf("0.061")
    return close(g.rho1_bath(em, en, w), g.rho1_res(em, en, w, seeded=seeded), mp.mpf("1e-12"))


def g1_4():
    em, el, en = P["em"], P["el"], P["en"]
    w1, w2 = mp.mpf("0.071"), mp.mpf("-0.043")
    return close(g.rho2_bath(em, el, en, w1, w2), g.rho2_res(em, el, en, w1, w2), mp.mpf("1e-10"))


def c_nn(model, e):
    b, G = model.b, model.G
    zp, zm = model.zp(e), model.zm(e)
    return b / (96 * mp.pi ** 4 * G ** 2) * (
        6 * mp.pi ** 2 * (mp.polygamma(1, zp) + mp.polygamma(1, zm))
        - 3 * mp.pi * b * G * (mp.polygamma(2, zp) + mp.polygamma(2, zm))
        + (b * G) ** 2 * (mp.polygamma(3, zp) + mp.polygamma(3, zm)))


def g2_1():
    e = P["en"]
    coeff = taylor_coeff(lambda w: g.rho1_res(e, e, w), 2, R)
    return close(coeff, c_nn(g, e), mp.mpf("1e-10"))


def g2_2(seeded=True):
    e, den = P["en"], (192 if seeded else 384)
    vals = []
    for G in (mp.mpf("1e-2"), mp.mpf("1e-3"), mp.mpf("1e-4")):
        s = Guo(P["beta"], G, P["mu"])
        z0p, z0m = s.zp(e, 0), s.zm(e, 0)
        lead = s.b / (16 * mp.pi ** 2) * (mp.polygamma(1, z0p) + mp.polygamma(1, z0m))
        const = s.b ** 3 / (den * mp.pi ** 4) * (mp.polygamma(3, z0p) + mp.polygamma(3, z0m))
        vals.append((c_nn(s, e) - lead / G ** 2 - const) / G)
    return bounded(vals)


def c_nm(model, en, em):
    b, G, e = model.b, model.G, en - em
    zpn, zpm, zmn, zmm = model.zp(en), model.zp(em), model.zm(en), model.zm(em)
    pre = 1j / (8 * mp.pi ** 3 * e ** 3 * (2j * G - e) ** 2)
    return pre * (4 * mp.pi ** 2 * (2 * G + 1j * e) ** 2
                  * (-mp.digamma(zpn) + mp.digamma(zpm) + mp.digamma(zmn) - mp.digamma(zmm))
                  + 8 * mp.pi * b * G * e * (1j * G - e) * (mp.polygamma(1, zpn) + mp.polygamma(1, zmm))
                  + b ** 2 * G * e ** 2 * (2 * G + 1j * e) * (mp.polygamma(2, zpn) + mp.polygamma(2, zmm)))


def g2_3():
    en, em = P["en"], P["em"]
    # C^{(1,2)}_{nm} is the w^2 coefficient of rho1_{nm}(w) (first index n)
    coeff = taylor_coeff(lambda w: g.rho1_res(en, em, w), 2, R)
    return close(coeff, c_nm(g, en, em), mp.mpf("1e-10"))


def g2_4():
    en, em = P["en"], P["em"]
    vals = []
    for G in (mp.mpf("1e-2"), mp.mpf("1e-3"), mp.mpf("1e-4")):
        s = Guo(P["beta"], G, P["mu"])
        lim = -1j / (2 * mp.pi * (en - em) ** 3) * (
            mp.digamma(s.zm(en, 0)) - mp.digamma(s.zp(en, 0)) - mp.digamma(s.zm(em, 0)) + mp.digamma(s.zp(em, 0)))
        vals.append((c_nm(s, en, em) - lim) / G)
    return bounded(vals)


def g2_5():
    e = P["en"]
    coeff = taylor_coeff(lambda w: g.rho2_bath(e, e, e, w, -w), 2, P["G"] / 4)
    rhs = 1j * g.b ** 4 / (768 * mp.pi ** 5) * (mp.polygamma(4, g.zp(e)) - mp.polygamma(4, g.zm(e)))
    return close(coeff, rhs, mp.mpf("1e-8"))


STEPS = [
    ("G1.1", g1_1, "rho0_n = int dw_b/(2 pi) 2G/(w_b^2+G^2) f0(e_n + w_b) = (f_+(e_n) + f_-(e_n))/2, with f_pm(e) = 1/2 pm (i/pi) psi(1/2 pm i beta (e mp iG - mu)/(2 pi))", "residue theorem on the Lorentzian-weighted bath integral"),
    ("G1.2", g1_2, "lim_{G->0} rho0_n = 1/(1 + exp(beta (e_n - mu)))", "the Lorentzian tends to a delta function"),
    ("G1.3", g1_3, "rho1_mn(w) (bath integral Eq. SM_rho1) = [rho0_n - rho0_m + r_+ + r_-]/(w + e_nm + 2iG), r_+ = iG (f_+(e_n) - f_+(e_m + w))/(w + e_nm), r_- = iG (f_-(e_n + w) - f_-(e_m))/(w + e_nm)", "close the w_b contour; residues of the Lorentzian and of f0"),
    ("G1.4", g1_4, "rho2_mln(w1,w2) (bath integral Eq. SM_rho2) equals the residue form of Eq. (tilde-rho_2_supp) with r_pm^(2) built from r_pm^(1) at shifted arguments", "same contour argument applied to the three terms"),
    ("G2.1", g2_1, "C^(1,2)_nn = [w^2] rho1_nn(w) = beta/(96 pi^4 G^2) [6 pi^2 (psi1(z+) + psi1(z-)) - 3 pi beta G (psi2(z+) + psi2(z-)) + (beta G)^2 (psi3(z+) + psi3(z-))], z_pm = 1/2 + beta(G pm i(e_n - mu))/(2 pi)", "Taylor-expand the residue form at coincident labels"),
    ("G2.2", g2_2, "C^(1,2)_nn = (1/G^2) [beta/(16 pi^2) sum_pm psi1(z0_pm)] + [beta^3/(192 pi^4) sum_pm psi3(z0_pm)] + O(G), z0_pm = 1/2 pm i beta (e_n - mu)/(2 pi)", "expand the polygammas around G = 0"),
    ("G2.3", g2_3, "C^(1,2)_nm = i/(8 pi^3 e_nm^3 (2iG - e_nm)^2) [4 pi^2 (2G + i e_nm)^2 (-psi0(z_n+) + psi0(z_m+) + psi0(z_n-) - psi0(z_m-)) + 8 pi beta G e_nm (iG - e_nm)(psi1(z_n+) + psi1(z_m-)) + beta^2 G e_nm^2 (2G + i e_nm)(psi2(z_n+) + psi2(z_m-))]", "Taylor-expand the residue form at distinct labels"),
    ("G2.4", g2_4, "C^(1,2)_nm = -i/(2 pi e_nm^3) [psi0(z0_n-) - psi0(z0_n+) - psi0(z0_m-) + psi0(z0_m+)] + O(G)", "set G = 0 in the closed form"),
    ("G2.5", g2_5, "C^(2,2)_nnn = [w^2] rho2_nnn(w,-w) = i beta^4/(768 pi^5) [psi4(z_n+) - psi4(z_n-)]", "Taylor-expand the second-order kernel at coincident labels"),
]
SEEDED = {"G1.3", "G2.2"}


def ground_truth() -> dict[str, bool]:
    with mp.workdps(25):
        return {sid: fn() for sid, fn, _, _ in STEPS}


if __name__ == "__main__":
    truth = ground_truth()
    for sid, ok in truth.items():
        print(f"{sid:5s} {'VALID' if ok else 'INVALID':8s} {'seeded' if sid in SEEDED else ''}")
    for sid, fn in (("G1.3", g1_3), ("G2.2", g2_2)):
        print(sid, "original valid:", fn(seeded=False))
