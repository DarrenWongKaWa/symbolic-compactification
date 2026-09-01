#!/usr/bin/env python3
"""Project frozen Guo flagship records into a human-facing view model.

This script does not adjudicate mathematics.
Statuses are copied from examples/flagship/guo/RESULTS.md.
Encoded left/right strings may be rendered as TeX for display only.

Scientific authority remains:
  symbolic-compactification v0.3.0-alpha @ f1d225e
  examples/flagship/guo/{RESULTS.md, RELATIONS_FROZEN.yaml, expressions/}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import sympy as sp
import yaml

HERE = Path(__file__).resolve().parent
SOFTWARE_COMMIT = "f1d225e46eec3aac17381fb2f7618fa830a8ec79"
SOFTWARE_TAG = "v0.3.0-alpha"
ENGINE = "python_sympy_exact_v1 0.3.0"

# Frozen RESULTS.md summary (copied, not recomputed from engine).
FROZEN_SUMMARY = {
    "numbered_equations_inventoried": "189/189",
    "derivation_relations": 146,
    "EXACT_ZERO": 32,
    "ZERO_UNDER_SUBSTITUTION": 21,
    "CERTIFIED_BY_RULE": 11,
    "UNKNOWN_REMAINDER_summary_line": 17,
    "STRUCTURAL": 47,
    "UNSUPPORTED": 18,
    "NONZERO": 0,
    "false_promotion": "0/155",
}

IDENT = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
RESERVED = {
    "I", "pi", "E", "oo", "Rational", "Abs", "diff", "Integer",
    "True", "False", "and", "or", "not",
}
LOCALS = {
    "Rational": sp.Rational,
    "I": sp.I,
    "pi": sp.pi,
    "E": sp.E,
    "oo": sp.oo,
    "Abs": sp.Abs,
    "diff": sp.diff,
}

REGRESSION_RESIDUAL_FILE = {
    "D.K1A-regroup": "R_K1A_regroup.txt",
    "D.metric-pair": "R_metric_pair.txt",
    "D.K1A-metric-subst": "R_K1A_metric.txt",
    "D.TA-prefactor": "R_TA_prefactor.txt",
    "D.TBgeo-eps21": "R_TBgeo_eps21.txt",
    "D.TA-TBgeo-cancel": "R_TA_TBgeo.txt",
    "D.C12-regroup": "R_C12_regroup.txt",
    "D.Vab-expand": "R_Vab_expand.txt",
    "D.Vab-eps21": "R_Vab_eps21.txt",
    "D.A-antisym": "R_A_antisym.txt",
    "D.A-to-Omega": "R_A_to_Omega.txt",
    "D.sigma-m1-Ii": "R_sigma_m1_Ii.txt",
    "D.Omega2-relabel": "R_Omega2_relabel.txt",
    "D.leibniz-product-rule": "R_leibniz_product_rule.txt",
    "D.T0-local-sign": "R_T0_local_sign.txt",
    "D.T0T1-regroup": "R_T0T1_regroup.txt",
    "D.geo-T2-subst": "R_geo_T2_subst.txt",
    "D.eps21-symmetrize": "R_eps21_symmetrize.txt",
    "D.compact-nbar": "R_compact_nbar.txt",
}

SYMBOL_TEX = {
    "e12": r"\epsilon_{12}",
    "e21": r"\epsilon_{21}",
    "fnp": r"f_{n}'",
    "f0np": r"f_{0,n}'",
    "f01p": r"f_{0,1}'",
    "f02p": r"f_{0,2}'",
    "f1p": r"f_{1}'",
    "f2p": r"f_{2}'",
    "f4": r"f_{n}^{(4)}",
    "f04": r"f_{0,n}^{(4)}",
    "f13": r"f_{1}^{(3)}",
    "f23": r"f_{2}^{(3)}",
    "fn2": r"f_{n}^{(2)}",
    "f1": r"f_{1}",
    "f2": r"f_{2}",
    "gab": r"g_{ab}",
    "gac": r"g_{ac}",
    "gbc": r"g_{bc}",
    "Gab": r"G^{ab}",
    "Gac": r"G^{ac}",
    "Gbc": r"G^{bc}",
    "Oab1": r"\Omega_{ab}^{1}",
    "Oac1": r"\Omega_{ac}^{1}",
    "Oab2": r"\Omega_{ab}^{2}",
    "Oac2": r"\Omega_{ac}^{2}",
    "da_vbc": r"\partial_a(v^{b}v^{c})",
    "dae12": r"\partial_a\epsilon_{12}",
    "dagbc": r"\partial_a g_{bc}",
    "dag": r"\partial_a g",
    "kernel": r"K",
    "va": r"v^{a}",
    "vb": r"v^{b}",
    "vc": r"v^{c}",
}

FEATURED_OVERVIEW = [
    "Eq. (D-59) -> Eq. (D-60)",
    "Eq. (D-66) -> Eq. (D-67)",
    "Eq. (D-114) -> Eq. (D-119)",
    "Eq. (D-57)",
]

CHAINS = [
    {
        "id": "d-gamma",
        "section": "D",
        "title": r"Small-\(\Gamma\) expansion of \(\sigma_{abc}\)",
        "summary": (
            r"The author writes a Taylor expansion of the DC conductivity in "
            r"\(\Gamma\), including an explicit \(O(\Gamma)\) remainder. "
            r"Coefficient identities are recorded separately; the enclosing "
            r"remainder is not certified."
        ),
        "featured": True,
        "relation_displays": ["Eq. (D-57)"],
    },
    {
        "id": "d-k1a-ta",
        "section": "D",
        "title": r"Geometric \(T_A^{(-2)}\) from \(K_{1A}\)",
        "summary": (
            r"The paper regroups \(K_{1A}\), inserts the metric-velocity "
            r"identity, and simplifies the prefactor that produces "
            r"\(T_A^{(-2)}\)."
        ),
        "featured": True,
        "relation_displays": [
            "Eq. (D-59) -> Eq. (D-60)",
            "Eq. (D-60)",
            "Eq. (D-60) -> Eq. (D-61)",
        ],
    },
    {
        "id": "d-tbgeo",
        "section": "D",
        "title": r"Geometric \(T_{B,\mathrm{geo}}^{(-2)}\)",
        "summary": (
            r"The geometric piece of \(T_B^{(-2)}\) is first written with both "
            r"\(\epsilon_{12}\) and \(\epsilon_{21}\), then rewritten with "
            r"the paper identity \(\epsilon_{21}=-\epsilon_{12}\)."
        ),
        "featured": True,
        "relation_displays": [
            "Eq. (D-64) -> Eq. (D-66)",
            "Eq. (D-66) -> Eq. (D-67)",
        ],
    },
    {
        "id": "d-cancel",
        "section": "D",
        "title": r"Cancellation \(T_A^{(-2)}+T_{B,\mathrm{geo}}^{(-2)}\)",
        "summary": (
            r"After the two geometric pieces are in matching form, their sum "
            r"is recorded as identically zero. That cancellation uses the "
            r"already-substituted \(T_{B,\mathrm{geo}}\) of Eq. (D-67)."
        ),
        "featured": True,
        "relation_displays": [
            "Eqs. (D-61), (D-67) -> Eq. (D-68)",
        ],
    },
    {
        "id": "d-sigma-m1",
        "section": "D",
        "title": r"\(\sigma^{(-1)}\) toward the Berry-curvature dipole",
        "summary": (
            r"Appendix D rewrites the \(\Gamma^{-1}\) kernel through "
            r"\(V_{ab}\) and \(\Omega\), then compactifies with "
            r"\(\Omega^{2}=-\Omega^{1}\)."
        ),
        "featured": False,
        "layout": "list",
        "relation_displays": [
            "Eq. (D-73)",
            "Eq. (D-73) (second equality)",
            "Eq. (D-74)",
            "Eq. (D-74) -> Eq. (D-75)",
            "Eq. (D-71) -> Eq. (D-72)",
            "Eqs. (D-72), (D-75) -> Eq. (D-76)",
            "Eqs. (D-70), (D-76) -> Eq. (D-77)",
            "Eq. (D-77) -> Eq. (D-78)",
        ],
    },
    {
        "id": "d-t0-ibp",
        "section": "D",
        "title": r"\(T_0\) to a Fermi-surface form",
        "summary": (
            r"A local quotient-rule identity produces Eq. (D-114). "
            r"The subsequent Brillouin-zone integration by parts is not an "
            r"engine ZERO of the global integral; it is certified by a local "
            r"Leibniz identity plus a declared torus-periodicity rule."
        ),
        "featured": True,
        "relation_displays": [
            "Eq. (D-113) -> Eq. (D-114)",
            "Eq. (D-114) -> Eq. (D-119)",
        ],
    },
    {
        "id": "d-compact-geo",
        "section": "D",
        "title": r"Compact two-band \(\sigma^{\mathrm{geo}}\)",
        "summary": (
            r"The geometric remainder is symmetrized with "
            r"\(\epsilon_{21}=-\epsilon_{12}\) and then written in the "
            r"compact \(n,\bar n\) form using \(f_n'=2f_{0,n}'\)."
        ),
        "featured": False,
        "relation_displays": [
            "Eq. (D-125) -> Eq. (D-126)",
            "Eq. (D-126) -> Eq. (D-127)",
        ],
    },
    {
        "id": "main-from-d",
        "section": "main",
        "title": r"Main-text formulae reported from Appendix D",
        "summary": (
            r"Several numbered main-text equations are the published "
            r"presentation of appendix results, including the compact "
            r"mapping \(f_n'=2f_{0,n}'\)."
        ),
        "featured": True,
        "layout": "list",
        "relation_displays": [
            "Eq. (1)",
            "Eq. (D-57) -> Eq. (1)",
            "Eq. (D-69) -> Eq. (2)",
            "Eq. (D-78) -> Eq. (3)",
            "Eq. (4)",
            "Eq. (D-117) -> Eq. (5)",
            "Eq. (D-127) -> Eq. (6)",
            "Eq. (7) -> Eq. (8)",
        ],
    },
]

SECTIONS = [
    {
        "id": "main",
        "title": "Main text",
        "summary": (
            r"The main text reports the \(\Gamma\) expansion of \(\sigma_{abc}\) "
            r"and the compact kinetic and geometric formulae. Several displayed "
            r"equations are the \(f_0\) form of appendix results."
        ),
    },
    {
        "id": "A",
        "title": "Appendix A",
        "summary": (
            r"Appendix A defines the open-system Hamiltonian and expands the "
            r"NESS density matrix in the driving perturbation. Bath integrals "
            r"that produce polygamma functions are recorded; they are not "
            r"lowered to exact local residuals in this audit."
        ),
    },
    {
        "id": "B",
        "title": "Appendix B",
        "summary": (
            r"Appendix B expands the Peierls substitution and the current, "
            r"then forms \(\sigma_{abc}(\omega_1,\omega_2)\) and takes the "
            r"DC limit. Remainder and limit claims stay at their frozen statuses."
        ),
    },
    {
        "id": "C",
        "title": "Appendix C",
        "summary": (
            r"Appendix C expands the second-order kernels in \(\Gamma\). "
            r"Those expansions are inventoried as remainder claims. Finite "
            r"coefficient identities are not a general remainder certificate."
        ),
    },
    {
        "id": "D",
        "title": "Appendix D",
        "summary": (
            r"Appendix D expands the nonlinear conductivity in powers of "
            r"\(\Gamma\) and reorganizes the \(\Gamma^{-2}\), \(\Gamma^{-1}\), "
            r"and \(\Gamma^{0}\) contributions into kinetic and geometric terms."
        ),
    },
    {
        "id": "E",
        "title": "Appendix E",
        "summary": (
            r"Appendix E repeats the DC calculation for a generic multiband "
            r"model. Several steps are definitions or integration-by-parts "
            r"parents certified by rule rather than by a global integral ZERO."
        ),
    },
    {
        "id": "F",
        "title": "Appendix F",
        "summary": (
            r"Appendix F recovers the DC conductivity from the low-frequency "
            r"limit of second-harmonic generation. The SHG \(\Gamma\) expansion "
            r"is an author-declared remainder claim."
        ),
    },
    {
        "id": "G",
        "title": "Appendix G",
        "summary": (
            r"Appendix G compares the fermionic-bath model with RTA/IFR. "
            r"The comparison uses additional approximations; those steps are "
            r"not promoted to engine ZERO."
        ),
    },
]

LEGEND = [
    {
        "status": "EXACT_ZERO",
        "meaning": "Encoded direct residual simplified to exact zero.",
        "not": "Not a statement that the whole paper is verified.",
    },
    {
        "status": "ZERO_UNDER_SUBSTITUTION",
        "meaning": (
            "Direct printed-form residual was not zero; after an explicit "
            "source-grounded substitution or identity, the residual was exactly zero."
        ),
        "not": "Not an unconditional engine ZERO.",
    },
    {
        "status": "CERTIFIED_BY_RULE",
        "meaning": (
            "A local machine-checkable identity plus an explicitly declared "
            "mathematical rule or domain supports the parent step. "
            "The parent is not engine ZERO."
        ),
        "not": "Not visually collapsed into ZERO.",
    },
    {
        "status": "UNKNOWN_REMAINDER",
        "meaning": (
            "Finite or local checks do not certify the stated asymptotic remainder."
        ),
        "not": "Not a claim that the expansion is false.",
    },
    {
        "status": "UNKNOWN",
        "meaning": (
            "A recorded limit or similar claim is not certified by the frozen system."
        ),
        "not": (
            "Not merged into UNKNOWN_REMAINDER in this presentation, even though "
            "RESULTS.md's summary line adds these two rows into its "
            "UNKNOWN_REMAINDER: 17 count."
        ),
    },
    {
        "status": "STRUCTURAL",
        "meaning": "Definition, bookkeeping, or no equality claim to verify.",
        "not": "Not a failed check.",
    },
    {
        "status": "UNSUPPORTED",
        "meaning": "The current verifier cannot honestly lower the claimed relation.",
        "not": "Not a refutation of the paper.",
    },
    {
        "status": "NONZERO",
        "meaning": (
            "An exact direct check refuted the encoded equality under the "
            "current assumptions."
        ),
        "not": (
            "On this paper the frozen final count is NONZERO = 0. Direct NONZERO "
            "before a source-grounded substitution is part of "
            "ZERO_UNDER_SUBSTITUTION, not a paper error by itself."
        ),
    },
]

ROLE_BY_DISPLAY = {
    "Eq. (D-57)": (
        r"This is the author-declared small-\(\Gamma\) expansion of the DC "
        r"conductivity, including an \(O(\Gamma)\) remainder."
    ),
    "Eq. (1)": (
        r"Main-text display of the same \(\Gamma\) expansion that Appendix D "
        r"writes as Eq. (D-57)."
    ),
    "Eq. (D-57) -> Eq. (1)": (
        r"Bookkeeping identification of the appendix expansion with the "
        r"main-text numbered display."
    ),
    "Eq. (D-59) -> Eq. (D-60)": (
        r"This step regroups \(K_{1A}\) before the metric-velocity identity "
        r"is applied."
    ),
    "Eq. (D-60)": (
        r"The regrouped \(K_{1A}\) is rewritten by substituting the "
        r"metric-velocity pair."
    ),
    "Eq. (D-60) -> Eq. (D-61)": (
        r"Prefactor simplification that produces the geometric piece "
        r"\(T_A^{(-2)}\)."
    ),
    "Eq. (D-64) -> Eq. (D-66)": (
        r"The geometric part of \(T_B^{(-2)}\) is written in two-band form."
    ),
    "Eq. (D-66) -> Eq. (D-67)": (
        r"This step rewrites the geometric part of \(T_B^{(-2)}\) before its "
        r"cancellation with \(T_A^{(-2)}\)."
    ),
    "Eqs. (D-61), (D-67) -> Eq. (D-68)": (
        r"The two geometric pieces are added; the paper claims they cancel."
    ),
    "Eq. (D-113) -> Eq. (D-114)": (
        r"A local differential identity recognizes \(T_0\) as a total "
        r"\(k\)-derivative (quotient rule) after substituting "
        r"\(v_2^a-v_1^a=-\partial_a\epsilon_{12}\)."
    ),
    "Eq. (D-114) -> Eq. (D-119)": (
        r"The paper integrates \(T_0\) by parts over the Brillouin zone."
    ),
    "Eq. (D-69) -> Eq. (2)": (
        r"Main-text Eq. (2) is the \(f_0\) form of appendix Eq. (D-69), "
        r"using the convention \(f_n'=2f_{0,n}'\)."
    ),
    "Eq. (D-126) -> Eq. (D-127)": (
        r"Compact \(n,\bar n\) form of the geometric conductivity, again "
        r"using \(f_n'=2f_{0,n}'\)."
    ),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def split_md_row(line: str) -> list[str]:
    parts = re.split(r"(?<!\\)\|", line.strip())
    parts = [p.strip().replace(r"\|", "|") for p in parts]
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts


def parse_results_table(text: str) -> list[dict]:
    rows = []
    in_table = False
    for line in text.splitlines():
        if line.startswith("| Eq. relation"):
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table:
            if not line.startswith("|"):
                break
            parts = split_md_row(line)
            if len(parts) < 7:
                raise SystemExit(f"RESULTS row has {len(parts)} cells: {line[:80]}")
            rows.append(
                {
                    "display": parts[0],
                    "cue": parts[1],
                    "move": parts[2],
                    "direct": parts[3],
                    "condition": parts[4],
                    "conditional": parts[5],
                    "final": parts[6],
                }
            )
    return rows


def detect_functions(text: str) -> list[str]:
    found = []
    for m in re.finditer(r"\b([A-Za-z][A-Za-z0-9_]*)\s*\(", text):
        name = m.group(1)
        if name not in LOCALS and name not in found:
            found.append(name)
    return found


def free_names(*texts: str, functions: list[str] | None = None) -> list[str]:
    names: set[str] = set()
    fn = set(functions or [])
    for t in texts:
        if not t:
            continue
        names |= set(IDENT.findall(t))
    names -= RESERVED
    names -= fn
    return sorted(names)


def auto_symbol_tex(name: str) -> str:
    if name in SYMBOL_TEX:
        return SYMBOL_TEX[name]
    m = re.fullmatch(r"v(\d+)(\d+)([abc])", name)
    if m:
        return rf"v_{{{m.group(1)}{m.group(2)}}}^{{{m.group(3)}}}"
    m = re.fullmatch(r"v(\d+)([abc])", name)
    if m:
        return rf"v_{{{m.group(1)}}}^{{{m.group(2)}}}"
    m = re.fullmatch(r"v(\d+)\1([abc])([abc])", name)
    if m:
        return rf"v_{{{m.group(1)}{m.group(1)}}}^{{{m.group(2)}{m.group(3)}}}"
    m = re.fullmatch(r"v(\d+)(\d+)([abc])([abc])", name)
    if m:
        return rf"v_{{{m.group(1)}{m.group(2)}}}^{{{m.group(3)}{m.group(4)}}}"
    m = re.fullmatch(r"A(\d+)(\d+)([abc])", name)
    if m:
        return rf"A_{{{m.group(1)}{m.group(2)}}}^{{{m.group(3)}}}"
    m = re.fullmatch(r"A(\d+)([abc])", name)
    if m:
        return rf"A_{{{m.group(1)}}}^{{{m.group(2)}}}"
    return name


def parse_expr(text: str):
    functions = detect_functions(text)
    loc = dict(LOCALS)
    for fname in functions:
        loc[fname] = sp.Function(fname)
    for n in free_names(text, functions=functions):
        loc[n] = sp.Symbol(n)
    return sp.sympify(text, locals=loc), functions


def latex_expr(expr: sp.Expr, extra_names: list[str] | None = None) -> str:
    names = {}
    for s in expr.free_symbols:
        names[s] = auto_symbol_tex(str(s))
    for n in extra_names or []:
        names[sp.Symbol(n)] = auto_symbol_tex(n)
    tex = sp.latex(expr, symbol_names=names)
    tex = tex.replace(r"\operatorname{diff}", r"\partial")
    return tex


def project_encoding(text: str | None) -> dict | None:
    if not text:
        return None
    out = {
        "encoding": text,
        "tex": None,
        "projection_ok": False,
        "projection_error": None,
    }
    try:
        expr, _ = parse_expr(text)
        out["tex"] = latex_expr(expr)
        out["projection_ok"] = True
    except Exception as exc:  # noqa: BLE001
        out["projection_error"] = type(exc).__name__
    return out


def apply_subst_expr(expr: sp.Expr, subst: dict[str, str], functions: list[str]):
    e = expr
    items = sorted(subst.items(), key=lambda kv: -len(kv[0]))
    for k, v in items:
        ve, _ = parse_expr(v)
        try:
            ks = sp.Symbol(k)
            if ks in e.free_symbols:
                e = e.subs(ks, ve)
                continue
        except Exception:
            pass
        ke, _ = parse_expr(k)
        e2 = e.xreplace({ke: ve})
        if e2 == e:
            e2 = e.subs(ke, ve)
        if e2 == e:
            e2 = sp.expand(e).xreplace({sp.expand(ke): ve})
        e = e2
    return e


def residual_projection(left: str, right: str, subst: dict | None, frozen_direct: str) -> dict:
    """TeX projection of encoded left-right. Does not assign a status."""
    rec = {
        "encoding_left": left,
        "encoding_right": right,
        "residual_encoding": None,
        "residual_tex": None,
        "residual_tex_compact": None,
        "residual_tex_full": None,
        "projection_ok": False,
        "projection_error": None,
        "note": (
            "Residual TeX is a projection of frozen encodings for display. "
            "The scientific verdict is the frozen RESULTS.md status, not this projection."
        ),
    }
    try:
        L, fn_l = parse_expr(left)
        R, fn_r = parse_expr(right)
        functions = sorted(set(fn_l) | set(fn_r))
        raw = sp.expand(L - R)
        rec["residual_encoding"] = str(raw)
        rec["residual_tex_full"] = latex_expr(raw)
        compact = sp.factor(raw)
        if sp.expand(compact - raw) != 0:
            compact = sp.simplify(raw)
        rec["residual_tex_compact"] = latex_expr(compact)
        if frozen_direct == "ZERO":
            rec["residual_tex"] = "0"
        elif frozen_direct == "NONZERO":
            shown = compact if len(str(compact)) <= len(str(raw)) else raw
            shown_tex = latex_expr(shown)
            if shown == 0 or shown_tex.strip() == "0":
                rec["residual_tex"] = rec["residual_tex_full"]
                rec["note"] += (
                    " Compact projection collapsed; full expanded encoding is shown. "
                    "Frozen direct status remains NONZERO."
                )
            else:
                rec["residual_tex"] = shown_tex
        else:
            rec["residual_tex"] = rec["residual_tex_compact"]
        rec["projection_ok"] = True
        if subst and frozen_direct == "NONZERO":
            Lc = apply_subst_expr(L, subst, functions)
            Rc = apply_subst_expr(R, subst, functions)
            cond = sp.expand(Lc - Rc)
            rec["conditional_residual_encoding"] = str(cond)
            rec["conditional_residual_tex_projected"] = latex_expr(sp.simplify(cond))
    except Exception as exc:  # noqa: BLE001
        rec["projection_error"] = f"{type(exc).__name__}: {exc}"
    return rec


def public_eq(n: str) -> str:
    return f"Eq. ({n})"


def public_list(nums: list[str]) -> list[str]:
    return [public_eq(n) for n in nums if n]


def extract_condition_tex(condition: str) -> str | None:
    if not condition or condition == "none":
        return None
    parts = re.findall(r"\$([^$]+)\$", condition)
    if not parts:
        return None
    return parts[0]


def section_id_of(sources: list[str], targets: list[str]) -> str:
    letters = []
    has_main = False
    for n in list(sources) + list(targets):
        if not n:
            continue
        if n[0].isdigit():
            has_main = True
        elif n[0] in "ABCDEFG" and (len(n) == 1 or n[1] == "-"):
            letters.append(n[0])
    letters = sorted(set(letters))
    if has_main and not letters:
        return "main"
    if has_main and letters:
        return "main"
    if len(letters) == 1:
        return letters[0]
    if letters:
        tletters = []
        for n in targets:
            if n and n[0] in "ABCDEFG":
                tletters.append(n[0])
        if tletters:
            return tletters[0]
        return letters[0]
    return "D"


def presentation_reason(row: dict, yaml_rel: dict) -> str | None:
    if row["direct"] != "NONZERO":
        return None
    if yaml_rel.get("subst") and row["conditional"] == "ZERO" and row["final"] == "ZERO_UNDER_SUBSTITUTION":
        return "MISSING_EXPLICIT_SUBSTITUTION"
    if row["final"] == "NONZERO":
        return "GENUINE_CONTRADICTION"
    return None


def human_explanation(row: dict, yaml_rel: dict, reason: str | None) -> str:
    final = row["final"]
    display = row["display"]
    if display in ROLE_BY_DISPLAY and final in {"UNKNOWN_REMAINDER", "CERTIFIED_BY_RULE", "ZERO_UNDER_SUBSTITUTION", "EXACT_ZERO"}:
        pass
    if final == "EXACT_ZERO":
        return (
            "The encoded expressions are exactly symbolically equivalent under "
            "the recorded assumptions."
        )
    if final == "ZERO_UNDER_SUBSTITUTION":
        cond = yaml_rel.get("condition") or row["condition"]
        body = (
            f"The printed forms are not an unconditional identity because the "
            f"recorded condition ({cond}) has not yet been applied. After that "
            f"source-grounded substitution, the frozen conditional check is ZERO. "
            f"The step is exact under the stated identity; it is not an "
            f"unconditional engine ZERO."
        )
        if reason == "MISSING_EXPLICIT_SUBSTITUTION":
            return body
        return body
    if final == "CERTIFIED_BY_RULE":
        return (
            "A local machine-checkable identity (Leibniz / product rule) is "
            "recorded as ZERO on the parent row. The parent step additionally "
            "uses the declared rule that the Brillouin zone is a periodic torus. "
            "The engine did not evaluate the global Brillouin-zone integral to "
            "ZERO. Parent status is CERTIFIED_BY_RULE, not engine ZERO."
        )
    if final == "UNKNOWN_REMAINDER":
        return (
            "The author declares an asymptotic remainder. Finite coefficient "
            "identities may be checked separately. No general remainder "
            "certificate is available in the frozen system. This is not a claim "
            "that the expansion is false. It is a statement that the current "
            "evidence does not certify the enclosing remainder."
        )
    if final == "UNKNOWN":
        return (
            "The frozen record does not certify this limit (or analogous) claim. "
            "UNKNOWN is not a promotion, and it is not reclassified as "
            "UNKNOWN_REMAINDER in this presentation."
        )
    if final == "STRUCTURAL":
        return (
            "This relation is a definition or bookkeeping step. There is no "
            "equality claim for the engine to verify."
        )
    if final == "UNSUPPORTED":
        return (
            "The current verifier cannot honestly lower the claimed relation "
            "to an exact local check."
        )
    if final == "NONZERO":
        return (
            "An exact direct check refuted the encoded equality under the "
            "recorded assumptions."
        )
    return (
        "Status copied from the frozen RESULTS.md row. No additional causal "
        "attribution is certified."
    )


def why_direct_failed(row: dict, yaml_rel: dict, reason: str | None) -> str | None:
    if row["direct"] != "NONZERO":
        return None
    if reason == "MISSING_EXPLICIT_SUBSTITUTION":
        cond = yaml_rel.get("condition") or row["condition"]
        return (
            f"The printed forms are not an unconditional identity because "
            f"{cond} has not yet been applied."
        )
    if reason == "GENUINE_CONTRADICTION":
        return (
            "The encoded equality is refuted under the recorded assumptions; "
            "no source-grounded substitution in the frozen record removes the residual."
        )
    return (
        "Why direct check failed: exact residual is nonzero under the encoded "
        "assumptions; no stronger causal attribution is certified."
    )


def interpretation(row: dict) -> str:
    final = row["final"]
    mapping = {
        "EXACT_ZERO": "Direct encoded residual is exact zero under the recorded assumptions.",
        "ZERO_UNDER_SUBSTITUTION": (
            "The step is exact under the stated upstream identity. "
            "It is not an unconditional engine ZERO."
        ),
        "CERTIFIED_BY_RULE": (
            "Local child identity is ZERO; the parent uses an explicit rule/domain. "
            "Do not read this as parent ZERO."
        ),
        "UNKNOWN_REMAINDER": (
            "This is not a claim that the expansion is false. "
            "It is a statement that the current evidence does not certify the enclosing remainder."
        ),
        "UNKNOWN": "The frozen system does not certify this claim.",
        "STRUCTURAL": "No equality was posed for verification.",
        "UNSUPPORTED": "Not lowered; not refuted.",
        "NONZERO": "Encoded equality fails under the recorded assumptions.",
    }
    return mapping.get(final, "See frozen RESULTS.md.")


def condition_authority(row: dict, yaml_rel: dict) -> dict:
    cond = yaml_rel.get("condition") or row["condition"] or "none"
    subst = yaml_rel.get("subst")
    if cond == "none" and not subst:
        return {
            "text": "none",
            "tex": None,
            "kind": "none",
            "authority": "No extra condition is recorded on this row.",
        }
    if subst:
        return {
            "text": cond,
            "tex": extract_condition_tex(cond),
            "kind": "source-grounded substitution",
            "authority": (
                "Source-grounded substitution recorded on the frozen relation "
                "before verification. This presentation does not invent the condition."
            ),
            "subst_encoding": subst,
        }
    if "author-declared" in cond:
        return {
            "text": cond,
            "tex": extract_condition_tex(cond),
            "kind": "author-declared remainder",
            "authority": (
                "Author-declared remainder or approximation. "
                "Author-declared is not machine-certified."
            ),
        }
    if "Brillouin" in cond or "torus" in cond or "Leibniz" in cond:
        return {
            "text": cond,
            "tex": None,
            "kind": "declared rule / domain",
            "authority": (
                "Declared mathematical rule and domain on the frozen parent row "
                "(periodic Brillouin-zone torus; local Leibniz identity checked exactly). "
                "Rule-certified is not engine ZERO."
            ),
            "rule_ids": ["BZ_TORUS_PERIODICITY", "BRILLOUIN_ZONE_TORUS"],
        }
    return {
        "text": cond,
        "tex": extract_condition_tex(cond),
        "kind": "recorded condition",
        "authority": "Copied from the frozen relation record.",
    }


def build(flagship: Path) -> dict:
    results_path = flagship / "RESULTS.md"
    yaml_path = flagship / "RELATIONS_FROZEN.yaml"
    expr_dir = flagship / "expressions"
    results_text = results_path.read_text()
    table = parse_results_table(results_text)
    frozen = yaml.safe_load(yaml_path.read_text())
    yaml_rels = frozen["relations"]
    by_display = {r["display"]: r for r in yaml_rels}

    missing = [r["display"] for r in table if r["display"] not in by_display]
    if missing:
        raise SystemExit(f"RESULTS displays missing from YAML: {missing[:5]}")

    helpers = [r for r in yaml_rels if r.get("helper")]
    public_yaml = [r for r in yaml_rels if not r.get("helper")]
    if len(public_yaml) != 146 or len(table) != 146:
        raise SystemExit(f"count mismatch yaml={len(public_yaml)} table={len(table)}")

    relations = []
    for row in table:
        y = by_display[row["display"]]
        if y.get("helper"):
            raise SystemExit("helper leaked into RESULTS table")
        reason = presentation_reason(row, y)
        left, right = y.get("left"), y.get("right")
        residual = None
        if y.get("executable") and left is not None and right is not None:
            residual = residual_projection(left, right, y.get("subst"), row["direct"])
            reg = y.get("regression")
            fname = REGRESSION_RESIDUAL_FILE.get(reg)
            if fname and (expr_dir / fname).exists():
                residual["frozen_residual_file"] = fname
                residual["frozen_residual_encoding"] = (expr_dir / fname).read_text().strip()
        before = project_encoding(left) if left is not None else None
        after = project_encoding(right) if right is not None else None
        sources = y.get("sources") or []
        targets = y.get("targets") or []
        rec = {
            "id": y["internal_id"],
            "public_display": row["display"].replace("->", "→"),
            "public_from": public_list(sources),
            "public_to": public_list(targets),
            "sources": sources,
            "targets": targets,
            "section": section_id_of(sources, targets),
            "role": ROLE_BY_DISPLAY.get(
                row["display"],
                f"Recorded {row['move']} relating {row['display'].replace('->', '→')}.",
            ),
            "math_summary_tex": y.get("cue") or row["cue"],
            "author_move": row["move"],
            "claimed_type": y.get("claimed"),
            "author_source_anchor": {
                "prose_paraphrase": y.get("prose"),
                "tex_lines": y.get("tex_lines") or [],
                "source": "arXiv:2511.16422v2 main.tex (Route A numbering authority)",
            },
            "before": before,
            "after": after,
            "direct": {
                "verdict": row["direct"],
                "residual_tex": (residual or {}).get("residual_tex"),
                "residual_tex_compact": (residual or {}).get("residual_tex_compact"),
                "residual_tex_full": (residual or {}).get("residual_tex_full"),
            },
            "condition": condition_authority(row, y),
            "conditional": {
                "verdict": row["conditional"],
                "residual_tex": (
                    "0"
                    if row["conditional"] == "ZERO"
                    else None
                ),
            },
            "final_status": row["final"],
            "presentation_reason": reason,
            "why_direct_nonzero": why_direct_failed(row, y, reason),
            "human_explanation": human_explanation(row, y, reason),
            "interpretation": interpretation(row),
            "executable": bool(y.get("executable")),
            "helper": False,
            "featured": row["display"] in FEATURED_OVERVIEW,
            "technical_provenance": {
                "internal_id": y["internal_id"],
                "regression": y.get("regression"),
                "claimed": y.get("claimed"),
                "parent_status_field": y.get("parent_status"),
                "executable": bool(y.get("executable")),
                "engine": ENGINE,
                "software": f"{SOFTWARE_TAG} @ {SOFTWARE_COMMIT}",
                "frozen_left_encoding": left,
                "frozen_right_encoding": right,
                "frozen_subst_encoding": y.get("subst"),
                "residual_projection": residual,
                "results_direct": row["direct"],
                "results_conditional": row["conditional"],
                "results_final": row["final"],
            },
        }
        if row["final"] == "CERTIFIED_BY_RULE":
            rec["rule_certification"] = {
                "claimed_move": row["move"],
                "local_identity": r"\(\partial_k(uv)=(\partial_k u)v+u(\partial_k v)\)",
                "local_machine_result": "ZERO",
                "local_machine_result_source": (
                    "Copied from the parent RESULTS.md conditional cell: "
                    f"{row['conditional']}"
                ),
                "rule_domain": ["BZ_TORUS_PERIODICITY", "BRILLOUIN_ZONE_TORUS"],
                "parent_status": "CERTIFIED_BY_RULE",
                "engine_did_not_evaluate_global_integral_to_zero": True,
            }
        if row["display"] in {"Eq. (D-57)", "Eq. (1)", "Eq. (D-57) -> Eq. (1)"}:
            rec["remainder_display_tex"] = (
                r"\sigma_{abc}=\Gamma^{-2}\sigma^{(-2)}"
                r"+\Gamma^{-1}\sigma^{(-1)}"
                r"+\sigma^{(0)}+O(\Gamma)"
            )
        rt = (rec["direct"] or {}).get("residual_tex") or ""
        if rec["why_direct_nonzero"] and rt and rt != "0":
            extra = []
            if r"\epsilon_{12} + \epsilon_{21}" in rt or r"\epsilon_{21} + \epsilon_{12}" in rt:
                extra.append(
                    r" The direct residual retains the factor associated with "
                    r"\(\epsilon_{12}+\epsilon_{21}\)."
                )
            if r"2 f_{0,n}' - f_{n}'" in rt or r"f_{n}' - 2 f_{0,n}'" in rt:
                extra.append(
                    r" The direct residual retains the factor associated with "
                    r"\(f_n'-2f_{0,n}'\)."
                )
            rec["why_direct_nonzero"] += "".join(extra)
        relations.append(rec)

    helper_out = []
    for y in helpers:
        helper_out.append(
            {
                "id": y["internal_id"],
                "public_display": "local Leibniz / product-rule identity",
                "role": (
                    r"Local identity used by Brillouin-zone integration-by-parts "
                    r"parents. This is not a numbered-equation row in RESULTS.md."
                ),
                "math_summary_tex": y.get("cue"),
                "author_move": y.get("move"),
                "before": project_encoding(y.get("left")),
                "after": project_encoding(y.get("right")),
                "machine_result_recorded_on_parents": "ZERO",
                "machine_result_source": (
                    "Parent RESULTS.md conditional cells say "
                    "'local Leibniz child ZERO'. This helper is not independently "
                    "re-adjudicated here."
                ),
                "helper": True,
                "technical_provenance": {
                    "internal_id": y["internal_id"],
                    "regression": y.get("regression"),
                    "frozen_left_encoding": y.get("left"),
                    "frozen_right_encoding": y.get("right"),
                    "not_a_numbered_equation_row": True,
                },
            }
        )

    by_pub = {r["public_display"].replace("→", "->"): r for r in relations}
    # also key original
    by_orig = {r["public_display"]: r for r in relations}

    def rel_by_display(display: str) -> dict:
        if display in by_pub:
            return by_pub[display]
        alt = display.replace("->", "→")
        if alt in by_orig:
            return by_orig[alt]
        raise SystemExit(f"chain display not found: {display}")

    chains = []
    for spec in CHAINS:
        steps = []
        for d in spec["relation_displays"]:
            rel = rel_by_display(d)
            steps.append(
                {
                    "relation_id": rel["id"],
                    "public_display": rel["public_display"],
                    "from": rel["public_from"],
                    "to": rel["public_to"],
                    "move": rel["author_move"],
                    "math_summary_tex": rel["math_summary_tex"],
                    "final_status": rel["final_status"],
                    "condition_tex": rel["condition"].get("tex"),
                }
            )
        chains.append(
            {
                "id": spec["id"],
                "section": spec["section"],
                "title": spec["title"],
                "summary": spec["summary"],
                "featured": spec["featured"],
                "layout": spec.get("layout", "flow"),
                "steps": steps,
            }
        )

    table_counts = Counter(r["final_status"] for r in relations)
    direct_counts = Counter(r["direct"]["verdict"] for r in relations)
    if table_counts["EXACT_ZERO"] != 32:
        raise SystemExit(f"EXACT_ZERO {table_counts['EXACT_ZERO']} != 32")
    if table_counts["ZERO_UNDER_SUBSTITUTION"] != 21:
        raise SystemExit("ZERO_UNDER_SUBSTITUTION mismatch")
    if table_counts["CERTIFIED_BY_RULE"] != 11:
        raise SystemExit("CERTIFIED_BY_RULE mismatch")
    if table_counts["NONZERO"] != 0:
        raise SystemExit("NONZERO final mismatch")
    if table_counts["STRUCTURAL"] != 47:
        raise SystemExit("STRUCTURAL mismatch")
    if table_counts["UNSUPPORTED"] != 18:
        raise SystemExit("UNSUPPORTED mismatch")
    n_exec = sum(1 for r in relations if r["executable"])
    if n_exec != 53:
        raise SystemExit(f"executable {n_exec} != 53")

    overview = []
    for d in FEATURED_OVERVIEW:
        rel = rel_by_display(d)
        evidence = {
            "EXACT_ZERO": "direct exact residual",
            "ZERO_UNDER_SUBSTITUTION": "substitution + exact child",
            "CERTIFIED_BY_RULE": "local ZERO + periodicity rule",
            "UNKNOWN_REMAINDER": "no remainder certificate",
        }[rel["final_status"]]
        overview.append(
            {
                "relation_id": rel["id"],
                "public_display": rel["public_display"],
                "what_happens": rel["math_summary_tex"],
                "evidence": evidence,
                "final_status": rel["final_status"],
            }
        )

    payload = {
        "schema": "HumanAuditPresentationV1",
        "not_scientific_authority": True,
        "authority": {
            "html_role": "human-readable projection of frozen machine evidence",
            "scientific_authority": "frozen machine records / JSON / YAML / RESULTS.md",
            "software": SOFTWARE_TAG,
            "commit": SOFTWARE_COMMIT,
            "engine": ENGINE,
            "paper_source": "arXiv:2511.16422v2",
            "results_path": "examples/flagship/guo/RESULTS.md",
            "relations_path": "examples/flagship/guo/RELATIONS_FROZEN.yaml",
            "results_sha256": sha256_file(results_path),
            "relations_sha256": sha256_file(yaml_path),
        },
        "paper": {
            "short": "Guo et al., PRL 136, 206303",
            "title": "Dissipation-Shaped Quantum Geometry in Nonlinear Transport",
            "authors": "Zhichao Guo, Xing-Yuan Liu, Hua Wang, Li-kun Shi, Kai Chang",
            "journal": "Phys. Rev. Lett. 136, 206303 (2026)",
            "arxiv": "2511.16422v2",
            "arxiv_abs": "https://arxiv.org/abs/2511.16422v2",
        },
        "coverage": {
            "numbered_equations": 189,
            "inventoried": 189,
            "inventory_label": "189 / 189 numbered equations inventoried",
            "inventory_note": (
                "Complete inventory coverage does not mean every equation was certified."
            ),
            "source_grounded_relations": 146,
            "executable_relations": 53,
            "leibniz_helper_not_a_numbered_row": 1,
            "table_counts": dict(table_counts),
            "direct_counts": dict(direct_counts),
            "results_md_summary": FROZEN_SUMMARY,
            "summary_line_note": (
                "RESULTS.md summary writes UNKNOWN_REMAINDER: 17 by adding "
                "UNKNOWN_REMAINDER rows (15) and UNKNOWN limit rows (2). "
                "This presentation copies per-row statuses and does not merge them."
            ),
            "false_promotion": {"false": 0, "controls": 155},
        },
        "legend": LEGEND,
        "sections": SECTIONS,
        "featured_overview": overview,
        "chains": chains,
        "relations": relations,
        "helper_identities": helper_out,
        "forbidden_readings": [
            "189 equations verified",
            "paper proved",
            "full paper verified",
            "CERTIFIED_BY_RULE means ZERO",
            "conditional ZERO means unconditional ZERO",
            "UNKNOWN means likely true",
            "author-declared means machine-certified",
        ],
    }
    return payload


FORBIDDEN_SNIPPETS = [
    "189 equations verified",
    "paper proved",
    "full paper verified",
    "2**f01p",
    "D-67 compact",
    "CERTIFIED_UNDER_DECLARED_APPROXIMATION",
]


def qa_payload(payload: dict) -> list[str]:
    issues = []
    scan = dict(payload)
    scan.pop("forbidden_readings", None)
    blob = json.dumps(scan)
    for s in FORBIDDEN_SNIPPETS:
        if s in blob:
            issues.append(f"forbidden snippet present: {s}")
    cov = payload["coverage"]
    if cov["inventoried"] != 189 or cov["numbered_equations"] != 189:
        issues.append("inventory counts")
    if "verified" in cov["inventory_label"].lower():
        issues.append("inventory label says verified")
    d66 = next(r for r in payload["relations"] if r["id"] and "D-66" in r["public_display"] and "D-67" in r["public_display"])
    if d66["final_status"] != "ZERO_UNDER_SUBSTITUTION":
        issues.append("D-66 status")
    if d66["direct"]["verdict"] != "NONZERO":
        issues.append("D-66 direct")
    if d66["conditional"]["verdict"] != "ZERO":
        issues.append("D-66 conditional")
    if not d66["direct"]["residual_tex"] or d66["direct"]["residual_tex"] == "0":
        issues.append("D-66 residual missing or zero")
    d57 = next(r for r in payload["relations"] if r["public_display"] == "Eq. (D-57)")
    if d57["final_status"] != "UNKNOWN_REMAINDER":
        issues.append("D-57 status")
    d59 = next(r for r in payload["relations"] if r["public_display"] == "Eq. (D-59) → Eq. (D-60)")
    if d59["final_status"] != "EXACT_ZERO":
        issues.append("D-59 status")
    d114 = next(r for r in payload["relations"] if r["public_display"] == "Eq. (D-114) → Eq. (D-119)")
    if d114["final_status"] != "CERTIFIED_BY_RULE":
        issues.append("D-114 status")
    if d114["direct"]["verdict"] != "N/A":
        issues.append("D-114 must not look like engine ZERO")
    # compact mapping must mention f_n' = 2 f_{0,n}'
    r005 = next(r for r in payload["relations"] if r["public_display"] == "Eq. (D-69) → Eq. (2)")
    if "f_n'" not in r005["math_summary_tex"] and "f_n'" not in r005["role"]:
        if "f_{0,n}" not in r005["math_summary_tex"]:
            issues.append("compact mapping notation")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--flagship",
        default="/private/tmp/ssc-v03/examples/flagship/guo",
        help="Path to frozen flagship directory (RESULTS.md + RELATIONS_FROZEN.yaml)",
    )
    ap.add_argument("--out", default=str(HERE))
    args = ap.parse_args()
    flagship = Path(args.flagship)
    outdir = Path(args.out)
    payload = build(flagship)
    issues = qa_payload(payload)
    if issues:
        print("QA failed:", file=sys.stderr)
        for i in issues:
            print(" -", i, file=sys.stderr)
        return 1
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / "report-data.json"
    js_path = outdir / "report-data.js"
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    json_path.write_text(text + "\n")
    js_path.write_text("window.AUDIT_REPORT = " + text + ";\n")
    print("wrote", json_path)
    print("wrote", js_path)
    print("relations", len(payload["relations"]))
    print("table_counts", payload["coverage"]["table_counts"])
    d66 = next(r for r in payload["relations"] if "D-66" in r["public_display"] and "D-67" in r["public_display"])
    print("D-66 residual_tex:", d66["direct"]["residual_tex"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
