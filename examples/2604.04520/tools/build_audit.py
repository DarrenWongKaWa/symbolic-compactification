#!/usr/bin/env python3
"""Emit canonical audit.json for arXiv:2604.04520 (Anan, Kitamura, Morimoto).

Statuses are conservative. This file does not run the exact engine.
ZERO_UNDER_SUBSTITUTION for 2×2 unitarity is copied from the V1 frozen
RESULTS row; it is not restamped here.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INV = json.loads((ROOT / "input" / "inventory.json").read_text())

WARNINGS = [
    "Local residual 0 is not a paper pass.",
    "Silence from non-submission is not a pass.",
    "Finite Laurent/Taylor coefficients do not prove an O(·) remainder bound.",
    "Human accept/reject does not convert a parent claim into machine Exact.",
    "Numerical agreement with a model is not an analytic proof of Eq. (5).",
]


def edge(**kw):
    required = (
        "id",
        "from_eq",
        "to_eq",
        "transformation",
        "assumptions",
        "verification_method",
        "status",
        "locator",
        "supports_claims",
    )
    for k in required:
        if k not in kw:
            raise SystemExit(f"edge missing {k}")
    kw.setdefault("source_tex", None)
    kw.setdefault("target_tex", None)
    kw.setdefault("evidence", None)
    kw.setdefault("note", None)
    kw.setdefault("load_bearing", False)
    return kw


def obligation(**kw):
    for k in (
        "id",
        "priority",
        "claim_used",
        "why_not_certified",
        "paper_evidence",
        "reviewer_must_decide",
        "blocks",
        "status",
    ):
        if k not in kw:
            raise SystemExit(f"obligation missing {k}")
    kw.setdefault("actions", ["Accept assumption/reasoning", "Reject", "Needs derivation"])
    return kw


def build() -> dict:
    eq_index = {e["id"]: e for e in INV["equations"]}

    claims = [
        {
            "id": "C1",
            "statement": (
                "Nonreciprocal current can arise in time-reversal symmetric "
                "Bloch electrons when finite dissipation enables interband processes."
            ),
            "locator": "Introduction; Discussion; abstract",
            "supporting_equations": ["(1)", "(4)", "(5)"],
            "appendix_chain": ["A", "B", "D"],
            "assumptions": ["TR symmetry", "inversion breaking", "finite Γ", "Bloch electrons"],
            "status": "HUMAN_REVIEW",
            "unresolved": ["O1", "O2"],
            "downstream": "Motivates the Green-function formula and the geometric conductivity (C2).",
            "blockers": [
                "Conceptual claim. The S-matrix unitarity argument is local algebra "
                "under S†S=I; the physical leap from non-unitarity to interband DC "
                "current is not a compiled residual."
            ],
        },
        {
            "id": "C2",
            "statement": (
                r"In TR-symmetric systems the longitudinal conductivity is "
                r"geometric: \(\sigma^{\alpha\alpha\alpha}\) is built from the "
                r"shift vector \(R_{ab}\) and Berry connections, Eq. (5), "
                r"starting from the Green-function kernel Eq. (4)."
            ),
            "locator": "Results, Eqs. (4)–(5); Appendix D (app:derivationSigma2)",
            "supporting_equations": ["(3)", "(4)", "(5)", "C-1", "C-2", "D-1"],
            "appendix_chain": [
                "Eq. (4) Green kernel",
                "Appendix C: static σ from ∂ω²K and band-basis I^(1,2,3)",
                "Appendix D: μ=β=α → Σ^{ααα}",
                "TR identities on ∂H, ∂²H",
                "antisymmetrization 𝒜 of Green products",
                "shift-vector rewrite",
                "H^α_ab = ξ_ab i A_ab → Eq. (5)",
            ],
            "assumptions": [
                "TR: [T,H(k)]=0 with T=KU(k→−k)",
                "no band degeneracy",
                "Bloch periodicity",
                "constant Γ in G^{R,A}=(ε+μ−H±iΓ)^{-1}",
                "velocity gauge",
            ],
            "status": "GAP",
            "unresolved": ["O1", "O5", "O6", "O7"],
            "downstream": "C3–C5 all quote Eq. (5). If C2 fails, the scaling and numerics lose their analytic parent.",
            "blockers": [
                "The Appendix D algebra (antisymmetrization, shift-vector identity, "
                "H=ξ i A substitution) is not compiled as local A−B=0.",
                "TR matrix-element identities are representation-theoretic, not a "
                "checked residual.",
            ],
        },
        {
            "id": "C3",
            "statement": (
                r"For an insulator/semiconductor (\(\mu\) in the gap) at low \(T\) "
                r"(\(\Gamma\ll\xi_{\min}\), \(\beta\Gamma\gg 2\pi\)), "
                r"\(D^{(2,3)}=O(\Gamma^2)+O(\Gamma^3)\), so \(\sigma^{\alpha\alpha\alpha}=O(\Gamma^2)\)."
            ),
            "locator": "Results, Eqs. (8)–(9); Appendix D kernels",
            "supporting_equations": ["(6)", "(7)", "(8)", "(9)"],
            "appendix_chain": ["D (kernels already in main text)", "digamma \(\psi(z)\sim\log z\)"],
            "assumptions": [
                r"\(\mu\) inside the gap so \(\xi_{\min}\le|\xi_a|\) for all bands",
                r"\(\Gamma\ll\xi_{\min}\)",
                r"\(\beta\Gamma\gg 2\pi\)",
                r"\(\psi(z)\sim\log z\)",
                "no degeneracy",
            ],
            "status": "ASYMPTOTIC_UNCERTIFIED",
            "unresolved": ["O8"],
            "downstream": "Rice–Mele semiconducting \(\Gamma^2\) curves (C5) are consistency checks of this scaling.",
            "blockers": [
                "Finite displayed terms do not prove the O(Γ³) remainder.",
            ],
        },
        {
            "id": "C4",
            "statement": (
                r"At high \(T\) (\(\beta\Gamma\ll 2\pi\)), or when \(\mu\) lies in a band, "
                r"the leading piece is \(O(\Gamma)\)."
            ),
            "locator": "Results, Eqs. (10)–(11) and the metallic paragraph",
            "supporting_equations": ["(6)", "(7)", "(10)", "(11)"],
            "appendix_chain": ["same D kernels; no extra appendix identity"],
            "assumptions": [
                r"high-T: \(\beta\Gamma\ll 2\pi\)",
                r"or metallic: some \(\xi_a=0\), so the low-T \(\xi_{\min}\) argument is unavailable",
            ],
            "status": "ASYMPTOTIC_UNCERTIFIED",
            "unresolved": ["O8"],
            "downstream": "Rice–Mele metallic/high-T \(\Gamma^1\) curves (C5).",
            "blockers": [
                "O(Γ²) remainder in Eqs. (10)–(11) is declared, not certified.",
                "Metallic O(Γ) is a domain argument, not a compiled expansion.",
            ],
        },
        {
            "id": "C5",
            "statement": (
                "A 1D Rice–Mele calculation produces \(\sigma^{xxx}(\mu,\Gamma,T)\) "
                "consistent with dissipation-induced geometric current in a TR-symmetric "
                "inversion-broken insulator/metal, and an order estimate for 3D polar semiconductors."
            ),
            "locator": "Model calculation; Figs. 2–3; Appendix E",
            "supporting_equations": ["(5)", "E-1", "E-2", "E-3"],
            "appendix_chain": ["Appendix E order estimation (unnumbered Hamiltonian in main text)"],
            "assumptions": [
                r"Rice–Mele \(H(k)=t_0\cos k\,\sigma_x+\delta t\sin k\,\sigma_y+m\sigma_z\)",
                r"parameters \(m=\delta t=0.1 t_0\) in the figures",
                "TR preserved so Drude and QMD vanish in this model",
            ],
            "status": "NUMERICAL_SUPPORT",
            "unresolved": ["O9"],
            "downstream": "Does not prove Eq. (5). Supports observability claims in the Discussion.",
            "blockers": [
                "Numerical evaluation of a model is consistency, not derivation.",
            ],
        },
    ]

    edges = [
        edge(
            id="E-unitarity",
            from_eq="(1)",
            to_eq="|t_LR|=|t_RL|",
            transformation="exact algebra",
            assumptions=["S†S = SS† = I"],
            verification_method="compiled 2×2 unitarity residual (V1 frozen ZERO_UNDER_SUBSTITUTION)",
            status="EXACT_IF_ASSUMPTIONS",
            locator="Introduction, scattering-matrix paragraph",
            supports_claims=["C1"],
            source_tex=r"S=\begin{pmatrix} r_{LL} & t_{LR}\\ t_{RL} & r_{RR}\end{pmatrix}",
            evidence="V1 RESULTS: S†S=I → |t_LR|=|t_RL| is ZERO_UNDER_SUBSTITUTION. Does not prove that dissipation realises non-unitary S.",
            load_bearing=True,
            note="Only machine-checked algebraic edge in this paper audit.",
        ),
        edge(
            id="E-define-K",
            from_eq="(2)",
            to_eq="(2)",
            transformation="definition",
            assumptions=[],
            verification_method="none",
            status="STRUCTURAL",
            locator="Results, Eq. (2)",
            supports_claims=["C2"],
            source_tex=r"j_\mu^{(2)}(t)=\sum\int \mathcal{K}^{\mu\alpha\beta}(\omega_1,\omega_2)A_\alpha(\omega_1)A_\beta(\omega_2)e^{-i(\omega_1+\omega_2)t}",
        ),
        edge(
            id="E-static-sigma",
            from_eq="(2)",
            to_eq="(3)",
            transformation="substitution",
            assumptions=["velocity gauge A=E/iω", "monochromatic E"],
            verification_method="not compiled",
            status="GAP",
            locator="Results, sentence before Eq. (3); Appendix A",
            supports_claims=["C2"],
            target_tex=r"\sigma^{\mu\alpha\alpha}=\frac12\partial_\omega^2\mathcal{K}^{\mu\alpha\alpha}(\omega,-\omega)|_{\omega=0}",
            load_bearing=True,
            note="The O(ω²) identification is bookkeeping plus gauge vanishing of lower orders (O1).",
        ),
        edge(
            id="E-gauge-vanish",
            from_eq="(2)",
            to_eq="(3)",
            transformation="gauge argument",
            assumptions=["gauge invariance", "Bloch electrons", "static A unphysical"],
            verification_method="none — physical argument",
            status="HUMAN_REVIEW",
            locator="Results after Eq. (3); Appendix A (undifferentiated K and mixed ω1² terms)",
            supports_claims=["C2"],
            load_bearing=True,
            evidence="Author: O(ω^0) and O(ω) of K(ω,−ω) vanish because of gauge invariance.",
        ),
        edge(
            id="E-green-kernel",
            from_eq="(3)",
            to_eq="(4)",
            transformation="cited identity",
            assumptions=["constant Γ", "velocity-gauge vertices H^α=∂_{k_α}H"],
            verification_method="not compiled (Green/Matsubara diagrams live in App. A–B)",
            status="GAP",
            locator="Results, Eq. (4); Appendices A–B",
            supports_claims=["C2"],
            target_tex=r"\mathcal{K}^{\mu\alpha\beta}(\omega,-\omega)\propto\int d\epsilon\,2\Gamma^2(f(\epsilon)-f(\epsilon+\hbar\omega))\,\mathrm{Tr}[\cdots G^R H^\alpha G^A \cdots]",
            load_bearing=True,
        ),
        edge(
            id="E-C-static-from-green",
            from_eq="(3)+(B-16)",
            to_eq="C-1",
            transformation="substitution",
            assumptions=["static limit ω→0 taken before Γ→0"],
            verification_method="not compiled",
            status="GAP",
            locator="Appendix C opening, eq:sigmaMuAlphaBetaGreenFunction",
            supports_claims=["C2"],
            note="Opposite order of limits (Γ→0 first) is injection/shift, Appendix B.",
            load_bearing=True,
        ),
        edge(
            id="E-C-band-basis",
            from_eq="C-1",
            to_eq="C-2",
            transformation="exact algebra",
            assumptions=["spectral representation of G^{R,A}", "no degeneracy later"],
            verification_method="not compiled (trace expansion)",
            status="GAP",
            locator="Appendix C, eq:generalNonReciprocalKernel",
            supports_claims=["C2"],
            load_bearing=True,
        ),
        edge(
            id="E-D-longitudinal",
            from_eq="C-2",
            to_eq="D-1",
            transformation="substitution",
            assumptions=["μ=β=α (longitudinal)", "TR to be imposed next"],
            verification_method="index restriction; not a residual",
            status="STRUCTURAL",
            locator="Appendix D, first paragraph and eq:longitudinalNonReciprocalKernel",
            supports_claims=["C2"],
            load_bearing=True,
            note="Author: derive Eq. (5) from Eq. (C-2) by setting μ and β to α.",
        ),
        edge(
            id="E-D-TR-matrix",
            from_eq="D-1",
            to_eq="D-2",
            transformation="symmetry",
            assumptions=["TR: T=KU(k→−k), [T,H(k)]=0"],
            verification_method="none",
            status="HUMAN_REVIEW",
            locator="Appendix D after D-1, two numbered H-matrix identities",
            supports_claims=["C2"],
            source_tex=r"\langle a|\partial_{k_\alpha}H|b\rangle=-\langle b|\partial_{k_\alpha}H|a\rangle|_{k\to-k}",
            load_bearing=True,
        ),
        edge(
            id="E-D-antisym",
            from_eq="D-2",
            to_eq="D-4",
            transformation="symmetry",
            assumptions=["TR", "coefficients may be antisymmetrized in band indices"],
            verification_method="not compiled",
            status="GAP",
            locator=r"Appendix D, steps marked \(\overset{\mathcal{A}}{=}\)",
            supports_claims=["C2"],
            load_bearing=True,
            note="Green-function monomials are replaced by antisymmetrized equivalents. Local A−B=0 was not encoded.",
        ),
        edge(
            id="E-D-shift",
            from_eq="D-1",
            to_eq="D-8",
            transformation="cited identity",
            assumptions=["TR", "F(a,b) arbitrary in band indices"],
            verification_method="not compiled",
            status="GAP",
            locator="Appendix D, “Using the TR symmetry, for arbitrary F(a,b)”",
            supports_claims=["C2"],
            target_tex=r"\sum H_{ba}^{\alpha\alpha}H_{ab}^\alpha F(a,b)=-i\sum R_{ba}H_{ba}^\alpha H_{ab}^\alpha F+\cdots",
            load_bearing=True,
        ),
        edge(
            id="E-D-to-sigma2",
            from_eq="D-8",
            to_eq="(5)",
            transformation="substitution",
            assumptions=[r"H_{ab}^\alpha=\xi_{ab} i A_{ab}^\alpha", "Eq. (C-1) Green identity"],
            verification_method="not compiled",
            status="GAP",
            locator="Appendix D last sentence: Using H=ξ i A and eq:sigmaMuAlphaBetaGreenFunction we obtain Eq. (5).",
            supports_claims=["C2"],
            load_bearing=True,
            target_tex=r"\sigma^{\alpha\alpha\alpha}=\frac{e^3}{\hbar}\int_{\mathrm{BZ}}\big[\sum_{a\neq b}R_{ab}|A_{ab}|^2 D^{(2)}_{ab}+\sum \Re(A_{ab}A_{bc}A_{ca})D^{(3)}_{abc}\big]",
        ),
        edge(
            id="E-define-D",
            from_eq="(5)",
            to_eq="(6)+(7)",
            transformation="definition",
            assumptions=["no degeneracy"],
            verification_method="none",
            status="STRUCTURAL",
            locator="Results, displays immediately after Eq. (5)",
            supports_claims=["C2", "C3", "C4"],
        ),
        edge(
            id="E-lowT",
            from_eq="(6)+(7)",
            to_eq="(8)+(9)",
            transformation="asymptotic expansion",
            assumptions=[r"μ in gap", r"Γ≪ξ_min", r"βΓ≫2π", r"ψ(z)∼log z"],
            verification_method="declared remainder O(Γ³)",
            status="ASYMPTOTIC_UNCERTIFIED",
            locator="Results, low-temperature insulating paragraph",
            supports_claims=["C3"],
            load_bearing=True,
        ),
        edge(
            id="E-highT",
            from_eq="(6)+(7)",
            to_eq="(10)+(11)",
            transformation="asymptotic expansion",
            assumptions=[r"βΓ≪2π"],
            verification_method="declared remainder O(Γ²)",
            status="ASYMPTOTIC_UNCERTIFIED",
            locator="Results, high-temperature paragraph",
            supports_claims=["C4"],
            load_bearing=True,
        ),
        edge(
            id="E-numeric-RM",
            from_eq="(5)",
            to_eq="Figs. 2–3",
            transformation="numerical evidence",
            assumptions=[
                r"H(k)=t_0\cos k\,\sigma_x+\delta t\sin k\,\sigma_y+m\sigma_z",
                "TR of Rice–Mele",
                r"m=δt=0.1 t_0 in the plots",
            ],
            verification_method="author numerical evaluation; not reproduced here",
            status="NUMERICAL_SUPPORT",
            locator="Model calculation; Fig. colorMapvsMu; Fig. riceMelevsGamma",
            supports_claims=["C5"],
            load_bearing=True,
            note="Shows peaks near the gap and Γ² vs Γ¹ scaling. Does not prove Eq. (5).",
        ),
        edge(
            id="E-order-est",
            from_eq="(5)",
            to_eq="E-1",
            transformation="asymptotic expansion",
            assumptions=["small ω", "3D extension of Rice–Mele"],
            verification_method="not compiled",
            status="ASYMPTOTIC_UNCERTIFIED",
            locator="Appendix E",
            supports_claims=["C5"],
        ),
    ]

    obligations = [
        obligation(
            id="O1",
            priority=1,
            claim_used=(
                r"Gauge invariance removes the \(O(\omega^0)\) and \(O(\omega)\) pieces of "
                r"\(\mathcal{K}(\omega,-\omega)\), so static \(\sigma\) is the \(\omega^2\) term."
            ),
            why_not_certified=(
                "This is a physical gauge/Bloch argument, not a local symbolic identity "
                "A−B=0. Appendix A also invokes that a static vector potential is unphysical."
            ),
            paper_evidence=(
                "Main text after Eq. (3); Appendix A, undifferentiated K and "
                r"\(\partial_{\omega_1}^2\mathcal{K}|_{0,0}\) vanishing."
            ),
            reviewer_must_decide=(
                "Confirm that, under the declared Bloch + velocity-gauge assumptions, "
                "the two leading orders in ω vanish identically so that Eq. (3) is the DC conductivity."
            ),
            blocks=["C2", "E-gauge-vanish", "E-static-sigma"],
            status="HUMAN_REVIEW",
        ),
        obligation(
            id="O5",
            priority=2,
            claim_used=(
                "TR symmetry T=KU(k→−k) implies the two H-matrix identities used to "
                "antisymmetrize the longitudinal kernel."
            ),
            why_not_certified=(
                "Requires the antiunitary representation of TR on Bloch states. "
                "Not encoded as a compiled residual."
            ),
            paper_evidence="Appendix D, two numbered lines after Eq. (D-1).",
            reviewer_must_decide=(
                r"Accept \(\langle a|\partial_\alpha H|b\rangle=-\langle b|\partial_\alpha H|a\rangle|_{k\to-k}\) "
                r"and the corresponding \(\partial^2 H\) identity under the paper's T."
            ),
            blocks=["C2", "E-D-TR-matrix"],
            status="HUMAN_REVIEW",
        ),
        obligation(
            id="O6",
            priority=3,
            claim_used=(
                r"After TR, Green-function monomials may be replaced by antisymmetrized "
                r"equivalents (\(\overset{\mathcal{A}}{=}\))."
            ),
            why_not_certified="Local algebra of the 𝒜 steps was not compiled.",
            paper_evidence="Appendix D, four 𝒜 replacements on G^R, G^A strings.",
            reviewer_must_decide=(
                "Either accept the 𝒜 calculus as written, or request a compiled identity "
                "for each replacement."
            ),
            blocks=["C2", "E-D-antisym"],
            status="GAP",
        ),
        obligation(
            id="O7",
            priority=4,
            claim_used=(
                r"The TR rewrite of \(\sum H_{ba}^{\alpha\alpha}H_{ab}^\alpha F(a,b)\) produces "
                r"the shift vector \(R_{ba}\) and the triple-A term, which become Eq. (5) "
                r"after \(H=\xi i A\)."
            ),
            why_not_certified="Named geometric identity plus substitution; not a machine residual.",
            paper_evidence="Appendix D, F(a,b) display through the last sentence of the appendix.",
            reviewer_must_decide=(
                "Confirm the shift-vector identification and the final substitution that "
                "yields Eq. (5) from Σ^{ααα}."
            ),
            blocks=["C2", "E-D-shift", "E-D-to-sigma2"],
            status="GAP",
        ),
        obligation(
            id="O2",
            priority=5,
            claim_used="Finite Γ is the physically relevant non-unitarity that realises C1.",
            why_not_certified="Phenomenological self-energy; not derived here.",
            paper_evidence="Introduction, imaginary part of the self-energy; constant Γ in G^{R,A}.",
            reviewer_must_decide="Accept constant-Γ relaxation as the dissipation model of the paper.",
            blocks=["C1"],
            status="HUMAN_REVIEW",
        ),
        obligation(
            id="O8",
            priority=6,
            claim_used=r"\(\psi(z)\sim\log z\) plus the stated \(\Gamma,\beta,\xi\) regime justify C3/C4.",
            why_not_certified="Asymptotic remainder. Finite displayed polynomials are not an O(·) proof.",
            paper_evidence="Results, paragraphs containing Eqs. (8)–(11).",
            reviewer_must_decide=(
                "Accept the digamma expansion and domain split (gap vs band, low-T vs high-T) "
                "without a remainder certificate."
            ),
            blocks=["C3", "C4", "E-lowT", "E-highT"],
            status="ASYMPTOTIC_UNCERTIFIED",
        ),
        obligation(
            id="O9",
            priority=7,
            claim_used="Rice–Mele numerics confirm dissipation-induced σ^{xxx} in a TR-symmetric model.",
            why_not_certified="Numerical support, not analytic certification of Eq. (5).",
            paper_evidence="Model calculation; Figs. colorMapvsMu and riceMelevsGamma; Appendix E.",
            reviewer_must_decide=(
                "Treat the figures as consistency in one 1D model (and an order-of-magnitude "
                "3D estimate), not as a proof of the geometric formula."
            ),
            blocks=["C5"],
            status="NUMERICAL_SUPPORT",
        ),
        obligation(
            id="O3",
            priority=8,
            claim_used="No band degeneracy.",
            why_not_certified="Standing assumption; poles merge if bands coincide (Appendix C).",
            paper_evidence="Results after Eq. (5); Appendix C ‘we assume that there are no degeneracies’.",
            reviewer_must_decide="Accept the nondegeneracy hypothesis for the geometric formula and the clean-limit cases.",
            blocks=["C2", "C3"],
            status="HUMAN_REVIEW",
        ),
    ]

    numerical = [
        {
            "id": "N1",
            "evidence_type": "NUMERICAL_SUPPORT",
            "quantity": r"\(\sigma^{xxx}(\mu,\Gamma,\beta)\) in 1D Rice–Mele",
            "supports": "C3/C4 scaling and C2’s claim that TR-symmetric inversion-broken crystals can carry this current",
            "regime": r"\(m=\delta t=0.1 t_0\); semiconducting \(\mu=0\); metallic \(\mu=0.15 t_0\)",
            "proves": False,
            "proves_not": "Does not prove Eq. (5), the Appendix D identities, or remainder bounds.",
            "locator": "Figs. 2–3 (colorMapvsMu, riceMelevsGamma)",
        }
    ]

    summary = {
        "title": "Nonreciprocal current induced by dissipation in time-reversal symmetric systems",
        "authors": "Anan, Kitamura, Morimoto",
        "arxiv": "2604.04520",
        "overall_state": "AUDIT_INCOMPLETE",
        "claim_count": len(claims),
        "equation_inventory": INV["v2"],
        "relations_reconstructed": len(edges),
        "machine_certified_edges": sum(
            1 for e in edges if e["status"] in {"EXACT", "EXACT_IF_ASSUMPTIONS"}
        ),
        "assumption_dependent_edges": sum(
            1 for e in edges if e["status"] in {"EXACT_IF_ASSUMPTIONS", "HUMAN_REVIEW"}
        ),
        "unresolved_load_bearing": sum(
            1 for e in edges if e.get("load_bearing") and e["status"] not in {"EXACT", "STRUCTURAL"}
        ),
        "presentation_is_not_a_certificate": True,
    }

    return {
        "schema": "paper-audit-v2",
        "paper": {
            "id": "2604.04520",
            "title": summary["title"],
            "source": "https://arxiv.org/abs/2604.04520",
            "tex": "input/nonreciprocal.tex",
        },
        "warnings": WARNINGS,
        "summary": summary,
        "inventory": {
            "v1_claimed": INV["v1_claimed"],
            "v2": INV["v2"],
            "correction": INV["correction"],
            "method": INV["method"],
            "unnumbered_notable": INV["unnumbered_notable"],
            "equations": INV["equations"],
            "main_public_map": {
                "(1)": "S-matrix",
                "(2)": "eq:definitionOfCurrent  (V1 row ‘main 3’)",
                "(3)": "eq:nonReciprocalEsquared  (V1 ‘main 4’)",
                "(4)": "eq:currentbyExcitation Green kernel  (V1 ‘main 5’)",
                "(5)": "eq:sigma2 geometric conductivity  (V1 ‘main 6’)",
                "(6)": "D^{(2)} definition",
                "(7)": "D^{(3)} definition",
                "(8)": "eq:lowTmpGammaSquared",
                "(9)": "low-T D^{(3)}",
                "(10)": "eq:highTmpGammaLinear",
                "(11)": "high-T D^{(3)}",
            },
        },
        "claims": claims,
        "edges": edges,
        "reviewer_obligations": obligations,
        "numerical_evidence": numerical,
        "v1_frozen_note": (
            "V1 RESULTS greened only 2×2 unitarity under S†S=I. That row is "
            "kept as EXACT_IF_ASSUMPTIONS. No other V1 orange row is promoted."
        ),
        "equation_index_ids": sorted(eq_index),
    }


def main() -> None:
    data = build()
    out = ROOT / "evidence" / "audit.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    s = data["summary"]
    print("wrote", out)
    print(
        "claims", s["claim_count"],
        "edges", s["relations_reconstructed"],
        "machine", s["machine_certified_edges"],
        "unresolved_lb", s["unresolved_load_bearing"],
        "eqs", s["equation_inventory"],
    )


if __name__ == "__main__":
    main()
