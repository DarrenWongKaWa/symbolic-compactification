"""C3 math-physics CandidateDossier objects. Guo is not a case here.

Analytic-domain predicates are copied from the cited theorem statement.
Hypotheses the source does not write are listed in notes as insertions
to refuse, not as DECLARED facts.
"""
from __future__ import annotations

import json
from pathlib import Path

from research.assumption_complete_representation.schema import (
    DECLARED,
    DERIVED,
    LADDER,
    CandidateDossier,
    Predicate,
    ScientificAssumptionContract,
    guo_is_not_admitted,
)

HERE = Path(__file__).resolve().parent


def P(statement: str, source: str, label: str = DECLARED) -> Predicate:
    return Predicate(statement=statement, label=label, source=source)


def _hermite_interpolation_fa() -> CandidateDossier:
    """Higham Def. 1.4 / Thm. 1.12: f(A) is a Hermite interpolant in A."""
    src_def = (
        "Higham, Functions of Matrices, SIAM 2008, Definition 1.4 "
        "(matrix function via Hermite interpolation) and Theorem 1.12; "
        "Higham–Lin, A Schur–Padé algorithm for fractional powers of a matrix, "
        "Def. 3.2 (eprints.maths.manchester.ac.uk/2067/1/paper.pdf)"
    )
    return CandidateDossier(
        case_id="mp-hermite-fA-01",
        title="Primary matrix function as Hermite interpolant at Jordan data",
        domain="mathphys",
        expression_sketch=(
            "Let A in C^{n x n} have distinct eigenvalues l_1..l_s with indices "
            "n_i (size of the largest Jordan block for l_i). The expanded form "
            "of f(A) changes with the Jordan data: if all n_i=1 and s=2, "
            "f(A) = f(l_1)*(A-l_2 I)/(l_1-l_2) + f(l_2)*(A-l_1 I)/(l_2-l_1); "
            "if a single Jordan block J_k(l) of size m, the strictly upper "
            "diagonals of f(J_k) are f^{(j)}(l)/j! for j=1..m-1. The scientific "
            "target is one polynomial p of degree < sum_i n_i with "
            "p^{(j)}(l_i)=f^{(j)}(l_i) for j=0..n_i-1 and f(A)=p(A), valid on "
            "both the distinct-eigenvalue and repeated-node strata."
        ),
        latent_structure=(
            "Hermite interpolation definition of the primary matrix function: "
            "f(A):=p(A) where p is the unique Hermite interpolant of f on the "
            "spectrum of A with multiplicities equal to the Jordan indices. "
            "Equivalent to the Jordan-form definition (Higham Thm. 1.12) "
            "without a holomorphy hypothesis. Repeated eigenvalues are the "
            "same object (osculatory nodes), not a separate Piecewise branch."
        ),
        proposed_ladder="R3_hermite_dd",
        assumption_contract=ScientificAssumptionContract(
            symbol_assumptions={
                "A": {"type": "matrix", "space": "C^{n x n}"},
                "n": {"integer": True, "positive": True},
                "s": {
                    "integer": True,
                    "positive": True,
                    "note": "number of distinct eigenvalues of A",
                },
                "lambda_i": {
                    "type": "complex",
                    "note": "distinct eigenvalues of A, i=1:s",
                },
                "n_i": {
                    "integer": True,
                    "positive": True,
                    "note": "index of lambda_i = order of largest Jordan block",
                },
            },
            function_domains={
                "f": (
                    "Defined on the spectrum of A in the sense of Higham "
                    "Definition 1.4: the values f^{(j)}(lambda_i) exist for "
                    "j=0:n_i-1 and i=1:s. Holomorphy is not part of this "
                    "definition."
                ),
                "p": (
                    "Unique polynomial of degree less than sum_i n_i = deg(psi), "
                    "psi the minimal polynomial of A, matching those jet data."
                ),
            },
            nonzero_conditions=[],
            positivity_conditions=[],
            real_valued_functions=[],
            analytic_domains=[
                P(
                    "f is defined on the spectrum of A: the derivatives "
                    "f^{(j)}(lambda_i) exist for j=0:n_i-1, i=1:s "
                    "(Higham: 'f is said to be defined on the spectrum of A').",
                    src_def,
                ),
                P(
                    "A belongs to C^{n x n}.",
                    src_def,
                ),
            ],
            branch_conventions=[
                "Primary matrix function: the same branch of f and of its "
                "derivatives is taken at every occurrence of an eigenvalue "
                "(Higham–Al-Mohy, Computing matrix functions, §2.1; Higham "
                "2008, §1.4). Non-primary functions are a different object.",
            ],
            limit_domains=[],
            source_provenance=[
                src_def,
                "DOI 10.1137/1.9780898717778",
                "https://eprints.maths.manchester.ac.uk/2067/1/paper.pdf",
                "https://epubs.siam.org/doi/10.1137/1.9780898717778",
            ],
            derived_conditions=[
                P(
                    "There is a unique such interpolating polynomial p "
                    "(stated in Higham Definition 1.4, not an extra hypothesis).",
                    src_def,
                    DERIVED,
                ),
            ],
        ),
        public_source=(
            "N. J. Higham, Functions of Matrices: Theory and Computation, "
            "SIAM, 2008, Definitions 1.4 and 1.2, Theorem 1.12. "
            "Survey: Higham–Al-Mohy, Acta Numerica 2010, Definition 2.2. "
            "Public PDF of the Schur–Padé companion: "
            "https://eprints.maths.manchester.ac.uk/2067/1/paper.pdf"
        ),
        why_not_cse_lgg=(
            "CSE can cancel repeated scalar factors but cannot invent the "
            "interpolating polynomial whose jet data are the Jordan indices. "
            "LGG anti-unifies first-order syntax; the distinct-eigenvalue "
            "Lagrange form and the repeated-node Taylor block are different "
            "trees, so LGG does not emit a single osculatory interpolant."
        ),
        proposer_leak_risk=(
            "Keep Hermite, osculatory, Newton form, divided difference, "
            "primary matrix function, and Higham out of proposer-visible "
            "text. Show only the expanded piecewise formulae in A and the "
            "jet data f^{(j)}(l_i)."
        ),
        notes=(
            "Do not insert holomorphy of f on a neighbourhood of Lambda(A): "
            "that hypothesis belongs to Higham Definition 1.11 (Cauchy), "
            "which Theorem 1.12 invokes only for equivalence with the "
            "integral definition. Do not insert A Hermitian, A diagonalizable, "
            "or a preferred branch of sqrt/log unless a later admitted "
            "instance names that f and copies Higham's branch sentence. "
            "Higham's running square-root example uses the principal branch "
            "with Re t^{1/2} >= 0; that convention is not declared for a "
            "general f."
        ),
        rejected=False,
        is_guo=False,
    )


def _daleckii_krein_loewner() -> CandidateDossier:
    """Daleckii–Krein / Higham Thm 3.11: Fréchet derivative is a Loewner DD."""
    src_h = (
        "Higham, Functions of Matrices, SIAM 2008, Theorem 3.11 "
        "(Daleckii and Krein) and Corollary 3.12; divided-difference "
        "definition recalled immediately before Theorem 3.9"
    )
    src_n = (
        "Noferini, A Daleckii–Krein formula for the Fréchet derivative of a "
        "generalized matrix function, MIMS EPrint 2016.24, Theorem 2.10, "
        "citing Daleckii–Krein, Amer. Math. Soc. Transl. Ser. 2, 47 (1965) 1–30"
    )
    return CandidateDossier(
        case_id="mp-daleckii-krein-01",
        title="Fréchet derivative of f at a diagonalizable matrix as Loewner kernel",
        domain="mathphys",
        expression_sketch=(
            "Let X = Z D Z^{-1} with D = diag(l_1,...,l_n). The directional "
            "derivative of f at X in direction E expands, in the eigenbasis, as "
            "a piecewise array: (Z^{-1} L_f(X,E) Z)_{ij} equals "
            "((f(l_i)-f(l_j))/(l_i-l_j)) * (Z^{-1} E Z)_{ij} when l_i != l_j, "
            "and equals f'(l_i) * (Z^{-1} E Z)_{ii} when l_i = l_j. The same "
            "array is a single Hadamard product against the kernel of first "
            "difference quotients of f on the spectrum, including the repeated-"
            "eigenvalue diagonal."
        ),
        latent_structure=(
            "Daleckii–Krein theorem: L_f(X,E) = Z ((f[l_i,l_j]) o (Z^{-1} E Z)) "
            "Z^{-1}, where f[l,m] is the first Newton divided difference "
            "(Loewner matrix) with the confluent value f'(l) on the diagonal. "
            "Generic off-diagonal quotients and degenerate equal-eigenvalue "
            "derivatives are one kernel, not two Piecewise programs."
        ),
        proposed_ladder="R3_hermite_dd",
        assumption_contract=ScientificAssumptionContract(
            symbol_assumptions={
                "X": {"type": "matrix", "space": "C^{n x n}", "diagonalizable": True},
                "D": {"type": "matrix", "diagonal": True, "space": "C^{n x n}"},
                "Z": {"type": "matrix", "invertible": True, "space": "C^{n x n}"},
                "E": {"type": "matrix", "space": "C^{n x n}"},
                "n": {"integer": True, "positive": True},
                "lambda_i": {"type": "complex", "note": "eigenvalues of X, i=1:n"},
            },
            function_domains={
                "f": (
                    "2n-1 times continuously differentiable on an open set D "
                    "contained in R or C (Higham §3.2: 'D denotes an open "
                    "subset of R or C'), and the spectrum of X lies in D "
                    "(Higham Theorem 3.11 / Corollary 3.12)."
                ),
            },
            nonzero_conditions=[
                P(
                    "Z is invertible (X = Z D Z^{-1} in Corollary 3.12).",
                    src_h,
                ),
            ],
            positivity_conditions=[],
            real_valued_functions=[],
            analytic_domains=[
                P(
                    "D is an open subset of R or of C (Higham §3.2 opening "
                    "sentence for the Fréchet-derivative section).",
                    src_h,
                ),
                P(
                    "f is 2n-1 times continuously differentiable on D "
                    "(Higham Theorem 3.11 and Corollary 3.12).",
                    src_h,
                ),
                P(
                    "The spectrum of X lies in D, and for Theorem 3.11 the "
                    "matrix is diagonal with every diagonal entry in D; "
                    "Corollary 3.12 extends to diagonalizable X = Z D Z^{-1} "
                    "with that spectrum.",
                    src_h,
                ),
            ],
            branch_conventions=[
                "Divided difference as in Higham before Theorem 3.9: "
                "f[l,m] = (f(l)-f(m))/(l-m) if l != m, and f[l,l] = f'(l). "
                "No further branch of f is named in Theorem 3.11.",
            ],
            limit_domains=[
                P(
                    "The equal-eigenvalue clause f[l,l] = f'(l) is the "
                    "definition Higham records, not an extra limit to be "
                    "taken in the verifier; C^{2n-1} on D supplies f'.",
                    src_h,
                ),
            ],
            source_provenance=[
                src_h,
                src_n,
                "DOI 10.1137/1.9780898717778",
                "https://eprints.maths.manchester.ac.uk/2462/1/gendk.pdf",
                "Daleckii Yu. L., Krein S. G., Integration and differentiation "
                "of functions of Hermitian operators and applications to the "
                "theory of perturbations, Amer. Math. Soc. Transl. Ser. 2 "
                "47 (1965) 1–30",
            ],
            derived_conditions=[
                P(
                    "Existence of f' on the spectrum follows from the declared "
                    "C^{2n-1} regularity on an open set containing the spectrum.",
                    src_h,
                    DERIVED,
                ),
            ],
        ),
        public_source=(
            "Higham 2008, Theorem 3.11 and Corollary 3.12. "
            "Classical source: Daleckii–Krein, AMS Transl. Ser. 2 47 (1965). "
            "Restatement for diagonalizable (not necessarily Hermitian) "
            "matrices with C^1 on the spectrum: Noferini, MIMS EPrint 2016.24, "
            "Theorem 2.10, https://eprints.maths.manchester.ac.uk/2462/1/gendk.pdf"
        ),
        why_not_cse_lgg=(
            "The expanded kernel is a Piecewise with a removable 0/0 on the "
            "eigenvalue diagonal. CSE will not identify that diagonal with f'. "
            "LGG sees two syntactic families (quotient vs derivative) and does "
            "not emit a Loewner matrix / first divided-difference operator."
        ),
        proposer_leak_risk=(
            "Hide Daleckii–Krein, Loewner, divided difference, Fréchet, "
            "Hadamard/Schur product as gold names. Show the piecewise "
            "eigenbasis array and the two clauses l_i != l_j vs l_i = l_j."
        ),
        notes=(
            "Working contract is Higham Theorem 3.11 / Corollary 3.12 "
            "(C^{2n-1} on open D, diagonalizable). Do not silently replace "
            "that smoothness by holomorphy, and do not insert A Hermitian: "
            "the 1965 Daleckii–Krein paper is Hermitian, but Higham's "
            "statement used here is not. Noferini Theorem 2.10 is a weaker "
            "C^1 diagonalizable restatement; mixing the two hypothesis lists "
            "is forbidden. Do not use Noferini's C^1 to certify a Higham "
            "C^{2n-1} obligation, or conversely."
        ),
        rejected=False,
        is_guo=False,
    )


def _resolvent_divided_difference() -> CandidateDossier:
    """First and second resolvent identities as Newton DDs of R(z,A)."""
    src_first = (
        "Glück, Functional Analysis 1 lecture notes, Proposition 2.2.9 "
        "(resolvent identity) and Example 2.3.2 (resolvent is holomorphic "
        "on rho(a) with R'(lambda,a) = -R(lambda,a)^2); Kato, Perturbation "
        "Theory for Linear Operators, Ch. I (finite-dimensional edition, "
        "1982), resolvent identity"
    )
    src_second = (
        "Müger, Functional Analysis notes, Exercise 13.29: first identity "
        "R_a(s)-R_a(t)=(s-t) R_a(s) R_a(t) for s,t in F\\sigma(a), and "
        "second identity R_a(s)-R_b(s)=R_a(s)(b-a)R_b(s) for "
        "s in F\\(σ(a)∪σ(b)), with R_a(λ)=(a-λ1)^{-1} in that source"
    )
    src_higham = (
        "Higham 2008 Definition 1.11 convention R(z)=(zI-A)^{-1}; the "
        "same convention is used in Glück (R(λ,a)=(λ-a)^{-1})"
    )
    return CandidateDossier(
        case_id="mp-resolvent-dd-01",
        title="Resolvent identities as Newton difference quotients",
        domain="mathphys",
        expression_sketch=(
            "Write R(z,A) = (z I - A)^{-1}. For spectral parameters lam, mu "
            "off the spectrum, the expanded identity is "
            "R(lam,A) - R(mu,A) = (mu - lam) R(lam,A) R(mu,A). "
            "For two operators and a common z off both spectra, "
            "R(z,A) - R(z,B) = R(z,A) (B-A) R(z,B). "
            "The first difference quotient in the spectral parameter is "
            "(R(lam,A)-R(mu,A))/(lam-mu) = - R(lam,A) R(mu,A); when "
            "lam=mu the same object is the derivative -R(lam,A)^2."
        ),
        latent_structure=(
            "Newton first divided difference of the resolvent in the spectral "
            "parameter, with the confluent node given by holomorphy of R on "
            "the resolvent set. The two-operator identity is the same "
            "difference-quotient structure in the operator argument at a "
            "fixed spectral point. One F(z)=R(z,A) generates both the "
            "generic quotient and the repeated-node derivative."
        ),
        proposed_ladder="R2_newton_dd",
        assumption_contract=ScientificAssumptionContract(
            symbol_assumptions={
                "A": {
                    "type": "element of a unital Banach algebra",
                    "note": "Glück Prop. 2.2.9; matrices C^{n x n} are the intended instance",
                },
                "B": {
                    "type": "element of the same unital Banach algebra",
                    "note": "needed only for the two-operator identity",
                },
                "lambda": {"type": "complex"},
                "mu": {"type": "complex"},
                "z": {"type": "complex"},
            },
            function_domains={
                "R": (
                    "R(·,A): rho(A) -> algebra, R(lambda,A)=(lambda I - A)^{-1} "
                    "(Glück / Higham convention). Domain is the resolvent set, "
                    "not a declared disk around the spectrum."
                ),
            },
            nonzero_conditions=[],
            positivity_conditions=[],
            real_valued_functions=[],
            analytic_domains=[
                P(
                    "lambda, mu belong to rho(A) (Glück Proposition 2.2.9: "
                    "the resolvent identity holds for all lambda, mu in rho(a)).",
                    src_first,
                ),
                P(
                    "The map rho(A) -> algebra, lambda |-> R(lambda,A), is "
                    "holomorphic, and R'(lambda,A) = -R(lambda,A)^2 for each "
                    "lambda in rho(A) (Glück Example 2.3.2).",
                    src_first,
                ),
                P(
                    "For the two-operator identity: z belongs to "
                    "rho(A) ∩ rho(B) (Müger Exercise 13.29, with that source's "
                    "resolvent convention recorded under branch_conventions).",
                    src_second,
                ),
            ],
            branch_conventions=[
                "Working resolvent: R(z,A) := (z I - A)^{-1} as in Higham "
                "Definition 1.11 and Glück Proposition 2.2.9. Then "
                "R(lam,A)-R(mu,A)=(mu-lam) R(lam,A) R(mu,A) and "
                "R'(lam,A)=-R(lam,A)^2.",
                "Müger Exercise 13.29 uses the opposite convention "
                "R_a(λ)=(a-λ1)^{-1}, which flips the sign of (s-t). Do not "
                "mix the two formulae without translating conventions.",
            ],
            limit_domains=[
                P(
                    "The repeated-node limit mu -> lambda is taken inside "
                    "rho(A): Glück Example 2.3.2 states holomorphy on rho(A), "
                    "so the difference quotient converges to R' on that open set.",
                    src_first,
                ),
            ],
            source_provenance=[
                src_first,
                src_second,
                src_higham,
                "https://fan.uni-wuppertal.de/fileadmin/mathe/reine_mathematik/funktionalanalysis/glueck/Manuskripte/Lecture_Notes__Functional_Analysis_1.pdf",
                "https://www.math.ru.nl/~mueger/functionalanalysis.pdf",
                "Kato, Perturbation Theory for Linear Operators, Springer, "
                "finite-dimensional edition 1982, Chapter I",
            ],
            derived_conditions=[
                P(
                    "rho(A) is open (standard consequence of the Neumann "
                    "series for the resolvent; used by Glück after Prop. 2.2.9).",
                    src_first,
                    DERIVED,
                ),
            ],
        ),
        public_source=(
            "Glück, Functional Analysis 1, Prop. 2.2.9 and Example 2.3.2. "
            "Two-operator form: Müger, Functional Analysis, Exercise 13.29. "
            "Textbook: Kato 1982, Chapter I. Convention (zI-A)^{-1}: Higham "
            "2008, Definition 1.11."
        ),
        why_not_cse_lgg=(
            "The identity is an algebraic rearrangement, but the representation "
            "claim is that the difference quotient in z and the product of "
            "resolvents are the same Newton first DD, with the diagonal given "
            "by holomorphy. CSE will not name F[z,w] = -R(z)R(w). LGG on "
            "expanded resolvent entries does not invent that operator kernel."
        ),
        proposer_leak_risk=(
            "Hide divided difference, Newton, confluent node. The names "
            "resolvent identity / first resolvent identity are standard and "
            "may appear in a grounded catalog; do not print Newton DD or "
            "F[z,w] in proposer context."
        ),
        notes=(
            "Do not insert a holomorphy disk that contains the spectrum: the "
            "cited identity is on rho(A), i.e. off the spectrum. Do not insert "
            "A self-adjoint, z not real, or dissipativity. Sign of the identity "
            "depends on whether the resolvent is (zI-A)^{-1} or (A-zI)^{-1}; "
            "the contract freezes the Higham/Glück convention. The two-operator "
            "clause is a second member of the same family, not a second f."
        ),
        rejected=False,
        is_guo=False,
    )


def _cauchy_dunford_resolvent() -> CandidateDossier:
    """Higham Def. 1.11 Dunford–Taylor integral as master object."""
    src = (
        "Higham, Functions of Matrices, SIAM 2008, Definition 1.11 "
        "(matrix function via Cauchy integral) and Theorem 1.12 "
        "(equivalence with Jordan and Hermite definitions when f is analytic); "
        "Higham–Lin Def. 3.3, eprints.maths.manchester.ac.uk/2067/1/paper.pdf"
    )
    src_frob = (
        "de Boor, Divided Differences, Surveys in Approximation Theory 1 "
        "(2005) 46–69, arXiv:math/0502036, §9 Contour integral, display (51), "
        "attributing the formula to Frobenius 1871"
    )
    return CandidateDossier(
        case_id="mp-cauchy-dunford-01",
        title="Cauchy–Dunford integral of the resolvent as master for f(A)",
        domain="mathphys",
        expression_sketch=(
            "f(A) is defined as (1/(2 π i)) * contour_integral_Gamma "
            "f(z) (z I - A)^{-1} dz, with Gamma a closed contour about the "
            "eigenvalues. Expanding the resolvent in a Jordan or eigenbasis "
            "recovers the usual block formulae; the same contour with "
            "denominator (z-t_1)...(z-t_k) produces the Newton coefficients "
            "of f. The compact object is the contour integral, not the "
            "expanded residue table."
        ),
        latent_structure=(
            "Dunford–Taylor / Cauchy integral of the resolvent as a master "
            "analytic object (ladder R6). Higham Theorem 1.12: when f is "
            "analytic this coincides with the Jordan and Hermite definitions. "
            "Related instance (not automatically the same hypothesis list): "
            "Frobenius/de Boor contour formula for divided differences, "
            "Δ(t_{1:j}) f = (1/(2πi)) ∮ f(ζ)/w_{j,t}(ζ) dζ."
        ),
        proposed_ladder="R6_master_object",
        assumption_contract=ScientificAssumptionContract(
            symbol_assumptions={
                "A": {"type": "matrix", "space": "C^{n x n}"},
                "n": {"integer": True, "positive": True},
                "Gamma": {
                    "type": "closed contour in C",
                    "note": "encloses Lambda(A); disjoint from Lambda(A)",
                },
            },
            function_domains={
                "f": (
                    "Analytic on and inside a closed contour Gamma that "
                    "encloses Lambda(A) (Higham Definition 1.11)."
                ),
                "resolvent": (
                    "(z I - A)^{-1} is defined on Gamma because Gamma is "
                    "disjoint from the spectrum (Higham Definition 1.11)."
                ),
            },
            nonzero_conditions=[],
            positivity_conditions=[],
            real_valued_functions=[],
            analytic_domains=[
                P(
                    "f is analytic on and inside a closed contour Gamma that "
                    "encloses Lambda(A) (Higham Definition 1.11; Higham–Lin "
                    "Definition 3.3 uses the same wording).",
                    src,
                ),
                P(
                    "The integrand contains the resolvent (zI-A)^{-1}, which "
                    "is defined on Gamma since Gamma is disjoint from the "
                    "spectrum of A (Higham Definition 1.11, sentence after "
                    "display (1.12)).",
                    src,
                ),
                P(
                    "If the Cauchy definition is claimed equivalent to the "
                    "Jordan and Hermite definitions, f is analytic (Higham "
                    "Theorem 1.12: 'If f is analytic then Definition 1.11 is "
                    "equivalent to Definitions 1.2 and 1.4').",
                    src,
                ),
            ],
            branch_conventions=[
                "Positive orientation of Gamma (standard Cauchy integral; "
                "Higham writes the factor 1/(2πi) as in the scalar Cauchy "
                "formula).",
                "Primary matrix function: one branch of f on and inside Gamma.",
            ],
            limit_domains=[],
            source_provenance=[
                src,
                src_frob,
                "DOI 10.1137/1.9780898717778",
                "https://eprints.maths.manchester.ac.uk/2067/1/paper.pdf",
                "https://arxiv.org/abs/math/0502036",
                "Horn–Johnson, Topics in Matrix Analysis, 1991, Theorem 6.2.28 "
                "(cited by Higham for the Cauchy equivalence)",
            ],
            derived_conditions=[],
        ),
        public_source=(
            "Higham 2008, Definition 1.11 and Theorem 1.12. "
            "Higham–Lin, https://eprints.maths.manchester.ac.uk/2067/1/paper.pdf, "
            "Definition 3.3. Related contour DD: de Boor, arXiv:math/0502036, §9."
        ),
        why_not_cse_lgg=(
            "The expanded residue calculus is a sum of Jordan-block Taylor "
            "polynomials. CSE/LGG operate on that expansion and do not "
            "reinvent the contour integral of f(z) times the resolvent as a "
            "single master object generating those blocks."
        ),
        proposer_leak_risk=(
            "Hide Dunford–Taylor, Cauchy integral definition, master object, "
            "Hermite interpolant. A catalog may list the integral formula as "
            "source text; do not name it as the gold representation type."
        ),
        notes=(
            "Holomorphy on and inside Gamma is in the cited definition; it is "
            "not to be weakened to 'f defined on the spectrum'. Conversely, "
            "do not attach this holomorphy list to mp-hermite-fA-01. The "
            "Frobenius/de Boor contour DD (de Boor display (51)) is a sibling "
            "formula whose hypotheses in that survey are: f entire in a disk "
            "of radius rho, contour of radius rho'<rho, interpolation nodes "
            "not in the annulus. Do not import those disk/annulus hypotheses "
            "into Higham Definition 1.11, and do not certify (51) from "
            "Higham's wording alone."
        ),
        rejected=False,
        is_guo=False,
    )


def _mathias_block_frechet() -> CandidateDossier:
    """Mathias block-triangular embedding of the Fréchet derivative."""
    src = (
        "Mathias, A chain rule for matrix functions and applications, "
        "SIAM J. Matrix Anal. Appl. 17 (1996) 610–620, Theorem 2.1 / Lemma 1.1; "
        "Higham 2008, Theorem 3.6 (Mathias); Higham–Relton, Higher order "
        "Fréchet derivatives of matrix functions, SIMAX 35 (2014) 1019–1037, "
        "Theorem 3.3 quoting Mathias; Al-Mohy–Higham, Computing the Fréchet "
        "derivative of the matrix exponential, Theorem 2.1"
    )
    return CandidateDossier(
        case_id="mp-mathias-block-01",
        title="Fréchet derivative as the off-diagonal block of f of a 2n triangular matrix",
        domain="mathphys",
        expression_sketch=(
            "For X, E in C^{n x n}, the 2n x 2n block matrix "
            "M = [[X, E], [0, X]] is mapped by f to "
            "[[f(X), L], [0, f(X)]]. Expanding f(M) by Jordan data of M "
            "produces L as a complicated combination of divided differences "
            "of f at eigenvalues of X (double spectrum). The compact claim "
            "is that this off-diagonal block L is exactly the Fréchet "
            "derivative L_f(X,E)."
        ),
        latent_structure=(
            "Mathias block-triangular identity: f([[X,E],[0,X]]) = "
            "[[f(X), L_f(X,E)],[0, f(X)]]. One matrix-function evaluation "
            "at a 2n argument is a master for both f(X) and its Fréchet "
            "derivative. Degeneracy of eigenvalues of X is already encoded "
            "in f(M), so the generic vs coincident spectra of X are not "
            "separate programs."
        ),
        proposed_ladder="R6_master_object",
        assumption_contract=ScientificAssumptionContract(
            symbol_assumptions={
                "X": {"type": "matrix", "space": "C^{n x n}"},
                "E": {"type": "matrix", "space": "C^{n x n}"},
                "n": {"integer": True, "positive": True},
            },
            function_domains={
                "f": (
                    "2n-1 times continuously differentiable on an open set D "
                    "subset of R or C; spectrum of X lies in D "
                    "(Higham Theorem 3.6 / Al-Mohy–Higham Theorem 2.1 / "
                    "Mathias Theorem 2.1)."
                ),
            },
            nonzero_conditions=[],
            positivity_conditions=[],
            real_valued_functions=[],
            analytic_domains=[
                P(
                    "f is 2n-1 times continuously differentiable on D, where D "
                    "is an open subset of R or C (Higham Theorem 3.6; "
                    "Al-Mohy–Higham Theorem 2.1: 'Let f be 2n-1 times "
                    "continuously differentiable on D and let the spectrum of "
                    "X lie in D').",
                    src,
                ),
                P(
                    "The spectrum of X lies in D (same theorem statements).",
                    src,
                ),
                P(
                    "Mathias 1996 also records: if A(t) is differentiable at "
                    "t=0 and the spectrum of A(t) is contained in D for all t "
                    "in some neighbourhood of 0, then the t-derivative of "
                    "f(A(t)) at 0 is the (1,2) block of f of the block "
                    "triangular matrix with A(0) on the diagonal and A'(0) "
                    "in the corner (Higham Theorem 3.6).",
                    src,
                ),
            ],
            branch_conventions=[],
            limit_domains=[
                P(
                    "For the path form (Higham Thm 3.6): spectrum of A(t) "
                    "stays in D for all t in some neighbourhood of 0 "
                    "(stated in the theorem; not a silent 'sufficiently small "
                    "t' without that neighbourhood clause).",
                    src,
                ),
            ],
            source_provenance=[
                src,
                "DOI 10.1137/S0895479895284634",
                "DOI 10.1137/130945259",
                "DOI 10.1137/1.9780898717778",
            ],
            derived_conditions=[],
        ),
        public_source=(
            "R. Mathias, SIAM J. Matrix Anal. Appl. 17 (1996) 610–620, "
            "Theorem 2.1. Higham 2008, Theorem 3.6. Al-Mohy–Higham, "
            "Theorem 2.1 (Fréchet derivative of the matrix exponential paper)."
        ),
        why_not_cse_lgg=(
            "f of a 2n block matrix is syntactically larger than f(X). CSE "
            "does not identify the (1,2) block with a derivative operator. "
            "LGG on entries of f(X) and of L_f(X,E) does not invent the "
            "block embedding."
        ),
        proposer_leak_risk=(
            "Hide Fréchet, Mathias, Daleckii–Krein, divided difference. "
            "The block matrix [[X,E],[0,X]] may appear in the catalog; do "
            "not label its (1,2) block as L_f in proposer-visible gold."
        ),
        notes=(
            "Do not insert holomorphy: Mathias/Higham require C^{2n-1}, not "
            "analyticity (Najfeld–Havel prove a related block formula under "
            "analyticity; that is a different citation). Do not drop the "
            "'spectrum of A(t) stays in D near 0' clause if the path form "
            "is used. Do not insert X Hermitian or X diagonalizable."
        ),
        rejected=False,
        is_guo=False,
    )


def _opitz_dd_matrix_function() -> CandidateDossier:
    """Opitz: f of the Newton bidiagonal matrix is the divided-difference table."""
    src = (
        "de Boor, Divided Differences, Surveys in Approximation Theory 1 "
        "(2005) 46–69, arXiv:math/0502036, Proposition 25 (Opitz formula) "
        "and Definition 37 (Kowalewski extension from polynomials to "
        "functions for which the Hermite interpolant exists)"
    )
    return CandidateDossier(
        case_id="mp-opitz-dd-01",
        title="Opitz formula: matrix function of the Newton bidiagonal is the DD table",
        domain="mathphys",
        expression_sketch=(
            "Let t = (t_1,...,t_n) be nodes, not necessarily distinct, and "
            "let A_{n,t} be the n x n lower bidiagonal matrix with t_j on "
            "the diagonal and 1 on the subdiagonal. For a polynomial p, "
            "the entries of p(A_{n,t}) are the quantities Delta(t_j:i) p "
            "(zero below the first nonzero subdiagonal band). The expanded "
            "Newton table that computes those entries by successive "
            "quotients (or by p^{(k)}(t_i)/k! on a repeated-node cluster) "
            "is therefore a matrix function of one bidiagonal argument."
        ),
        latent_structure=(
            "Opitz formula: p(A_{n,t}) = (Delta(t_j:i) p)_{i,j=1:n}. The "
            "divided-difference table is f(A) for A the Newton companion / "
            "bidiagonal multiplication-by-x operator in the Newton basis. "
            "Repeated nodes are already in A_{n,t} (equal diagonal entries); "
            "the confluent Hermite rule is the same matrix function, not a "
            "second algorithm. Kowalewski: the leading Newton coefficient "
            "of a non-polynomial f is that of its Hermite interpolant."
        ),
        proposed_ladder="R3_hermite_dd",
        assumption_contract=ScientificAssumptionContract(
            symbol_assumptions={
                "n": {"integer": True, "positive": True},
                "t_j": {
                    "type": "scalar in IF",
                    "note": "IF = R or C as in de Boor §1; nodes may coincide",
                },
                "A_n_t": {
                    "type": "matrix",
                    "space": "IF^{n x n}",
                    "note": "bidiagonal: diagonal t_1..t_n, subdiagonal ones",
                },
            },
            function_domains={
                "p": (
                    "Polynomial IF -> IF for Proposition 25 (Opitz). No "
                    "holomorphy hypothesis in that statement."
                ),
                "f": (
                    "For the extension off polynomials: any function for which "
                    "the Hermite interpolant at t_{1:n} exists, i.e. the "
                    "derivatives named in de Boor (31)/(36) make sense "
                    "(Definition 37, Kowalewski 1932)."
                ),
            },
            nonzero_conditions=[],
            positivity_conditions=[],
            real_valued_functions=[],
            analytic_domains=[
                P(
                    "Proposition 25 is stated for any polynomial p in Π "
                    "(de Boor, display (26)). Continuity of Delta(t_{1:j}) "
                    "in the nodes (Proposition 21) is used in the proof to "
                    "pass from distinct t_i to coincident nodes.",
                    src,
                ),
                P(
                    "Off polynomials, Definition 37 requires f smooth enough "
                    "that the derivatives in (36) make sense, equivalently "
                    "that the Hermite interpolant of f at t_{1:n} exists "
                    "(de Boor §7, citing Kowalewski 1932).",
                    src,
                ),
            ],
            branch_conventions=[
                "IF is R or C as in de Boor §1. No branch of a multi-valued f "
                "is named.",
            ],
            limit_domains=[
                P(
                    "Coincident nodes are included: de Boor notes that Opitz "
                    "originally excluded coincident t_j, and that continuity "
                    "of the divided difference (Proposition 21) extends the "
                    "identity to repeated nodes. The repeated-node rule "
                    "Delta(tau[n+1]) p = D^n p(tau)/n! is Example 4 / (14).",
                    src,
                ),
            ],
            source_provenance=[
                src,
                "https://arxiv.org/abs/math/0502036",
                "Opitz G., Steigungsmatrizen, ZAMM 44 (1964) T52–T54 "
                "(as cited by de Boor; Opitz excluded coincident nodes)",
            ],
            derived_conditions=[
                P(
                    "For polynomials, the identity at coincident nodes follows "
                    "from the distinct-node case plus continuity of Delta "
                    "(de Boor Proposition 21), which de Boor records as the "
                    "justification for dropping Opitz's distinctness ban.",
                    src,
                    DERIVED,
                ),
            ],
        ),
        public_source=(
            "C. de Boor, Divided Differences, Surveys in Approximation "
            "Theory 1 (2005) 46–69, arXiv:math/0502036, Proposition 25 and "
            "Definition 37. Original: G. Opitz, ZAMM 44 (1964)."
        ),
        why_not_cse_lgg=(
            "A Newton table is a triangular array of quotients. CSE common-"
            "subexpression folding does not recognise that array as p of one "
            "bidiagonal matrix. LGG on table entries does not invent the "
            "matrix-function representation."
        ),
        proposer_leak_risk=(
            "Hide Opitz, Steigungsmatrix, divided difference, Newton basis, "
            "Hermite interpolant. The bidiagonal matrix and the table of "
            "quotients may appear as source members."
        ),
        notes=(
            "Do not import holomorphy from the Cauchy/Frobenius contour "
            "paragraph of the same survey (§9) into Proposition 25. Do not "
            "require distinct nodes: that was Opitz's restriction, which de "
            "Boor removes. For non-polynomial f, do not silently assume "
            "entire-ness; Kowalewski only needs the Hermite jet to exist."
        ),
        rejected=False,
        is_guo=False,
    )


def _kato_simple_eigenvalue() -> CandidateDossier:
    """Greenbaum–Li–Overton / Kato: simple-eigenvalue first-order formulae."""
    src_glo = (
        "Greenbaum, Li, Overton, First-order perturbation theory for "
        "eigenvalues and eigenvectors, arXiv:1903.00785, Assumption 1 and "
        "Theorems 1–3"
    )
    src_kato = (
        "Kato, Perturbation Theory for Linear Operators, Springer, "
        "finite-dimensional edition 1982, Chapter II (cited throughout "
        "Greenbaum–Li–Overton; reduced resolvent at I.5.28 and II.2.11; "
        "eigenprojector derivative at II.2.13)"
    )
    return CandidateDossier(
        case_id="mp-kato-simple-ev-01",
        title="First-order perturbation of a simple eigenvalue via reduced resolvent",
        domain="mathphys",
        expression_sketch=(
            "A(tau) is an analytic matrix family, A(tau0)=A0, with a simple "
            "eigenvalue l0 of A0, right/left eigenvectors x0, y0. Expanded "
            "first-order formulae: l'(tau0) = y0* A'(tau0) x0, and "
            "x'(tau0) = -S A'(tau0) x0 where S is the reduced resolvent "
            "(group inverse of A0 - l0 I on the complementary subspace). "
            "When two eigenvalues collide the simple-eigenvalue formulae "
            "stop; the same first-order data then require a different "
            "Puiseux/Rellich calculus not claimed here."
        ),
        latent_structure=(
            "Kato simple-eigenvalue perturbation: analytic branches of "
            "lambda(tau), x(tau), Pi(tau)=x(tau) y(tau)* generated by the "
            "reduced resolvent S of A0 at l0. Equivalent contour form of "
            "the eigenprojector (APT stream) is a Dunford integral of the "
            "resolvent about an isolating contour. The degenerate "
            "(non-simple) limit is explicitly out of the cited theorems "
            "(Greenbaum–Li–Overton §4); unifying simple vs multiple is a "
            "ladder-R4 target, not a declared theorem here."
        ),
        proposed_ladder="R2_newton_dd",
        assumption_contract=ScientificAssumptionContract(
            symbol_assumptions={
                "n": {"integer": True, "positive": True},
                "A0": {"type": "matrix", "space": "C^{n x n}"},
                "tau0": {"type": "complex"},
                "lambda0": {"type": "complex", "simple_eigenvalue_of": "A0"},
                "x0": {"type": "vector in C^n", "nonzero": True},
                "y0": {"type": "vector in C^n", "nonzero": True},
            },
            function_domains={
                "A": (
                    "Complex-valued n x n matrix function of a complex "
                    "parameter tau, analytic in a neighbourhood of tau0, "
                    "with A(tau0)=A0 (Greenbaum–Li–Overton Assumption 1)."
                ),
            },
            nonzero_conditions=[
                P(
                    "x0 != 0 and y0 != 0, with A0 x0 = lambda0 x0 and "
                    "y0* A0 = lambda0 y0* (Assumption 1).",
                    src_glo,
                ),
                P(
                    "Normalization y0* x0 = 1 is declared in Assumption 1.",
                    src_glo,
                ),
            ],
            positivity_conditions=[],
            real_valued_functions=[],
            analytic_domains=[
                P(
                    "lambda0 is a simple eigenvalue of A0 "
                    "(Greenbaum–Li–Overton Assumption 1).",
                    src_glo,
                ),
                P(
                    "A(tau) is analytic in a neighbourhood of tau0 "
                    "(Assumption 1: each entry analytic / complex "
                    "differentiable / holomorphic near tau0).",
                    src_glo,
                ),
                P(
                    "Theorems 1–3 then give unique lambda(tau), and some "
                    "x(tau), y(tau)*, Pi(tau), analytic in a neighbourhood "
                    "of tau0.",
                    src_glo,
                ),
            ],
            branch_conventions=[
                "Left eigenvectors are written with conjugate transpose y* "
                "(Greenbaum–Li–Overton Remark 1: a convention, not forced). "
                "y(tau)* , not y(tau), is analytic in the complex parameter.",
                "Eigenvector scale: y(tau)* x(tau) = 1 together with "
                "y0* x'(tau0)=0 and (y*)'(tau0) x0 = 0 in Theorem 2; other "
                "normalizations are a different theorem in that paper §3.4.",
            ],
            limit_domains=[
                P(
                    "Neighbourhood of tau0 in which the analytic branches "
                    "exist is the neighbourhood granted by Theorems 1–3; "
                    "no explicit radius is stated in those theorems.",
                    src_glo,
                ),
            ],
            source_provenance=[
                src_glo,
                src_kato,
                "https://ar5iv.labs.arxiv.org/html/1903.00785",
                "https://arxiv.org/abs/1903.00785",
            ],
            derived_conditions=[
                P(
                    "y0* x0 != 0, so the normalization y0* x0 = 1 is always "
                    "possible: 'the right and left eigenvector corresponding "
                    "to a simple eigenvalue cannot be orthogonal' "
                    "(Greenbaum–Li–Overton Remark 1).",
                    src_glo,
                    DERIVED,
                ),
                P(
                    "In finite dimension, a simple eigenvalue is isolated "
                    "(spectrum of A0 in C^{n x n} is finite). Isolation is "
                    "not an extra hypothesis beyond Assumption 1's matrix "
                    "setting.",
                    src_glo,
                    DERIVED,
                ),
            ],
        ),
        public_source=(
            "A. Greenbaum, R.-C. Li, M. L. Overton, arXiv:1903.00785, "
            "Assumption 1 and Theorems 1–3. Kato 1982, Chapters I–II "
            "(reduced resolvent, eigenprojector)."
        ),
        why_not_cse_lgg=(
            "The expanded Rayleigh quotient y* A' x and the sum over "
            "complementary eigenpairs for S are first-order algebra. CSE "
            "will not identify S as the reduced resolvent / group inverse, "
            "nor treat the colliding-eigenvalue limit as a change of "
            "representation. LGG does not invent that operator."
        ),
        proposer_leak_risk=(
            "Hide Kato, reduced resolvent, group inverse, eigenprojector, "
            "Rellich. Catalog members are the expanded l' and x' formulae "
            "and the complementary-subspace sum."
        ),
        notes=(
            "Do not insert self-adjointness or Rellich's convergent power "
            "series for multiple eigenvalues (Greenbaum–Li–Overton §1 and "
            "§4: those are a different theorem, and multiple eigenvalues "
            "break Assumption 1). Do not insert an isolating contour unless "
            "the contour form of Pi is taken from Kato and Gamma subset "
            "rho(A0) enclosing only lambda0 is then DECLARED from Kato, not "
            "from Assumption 1. Do not insert 'sufficiently small tau' "
            "beyond the neighbourhood the theorems already grant."
        ),
        rejected=False,
        is_guo=False,
    )


def _parlett_schur_degeneracy() -> CandidateDossier:
    """Parlett recurrence: off-diagonal f(T) as a difference quotient, with a block form when eigenvalues collide."""
    src = (
        "Parlett, A recurrence among the elements of functions of triangular "
        "matrices, Linear Algebra Appl. 14 (1976) 117–121; Higham–Al-Mohy, "
        "Computing matrix functions, Acta Numerica 2010, Algorithms 4.2 "
        "(scalar Parlett recurrence) and 4.3 (block Parlett recurrence); "
        "Higham 2008, Chapter 9 (Schur–Parlett)"
    )
    return CandidateDossier(
        case_id="mp-parlett-schur-01",
        title="Parlett recurrence on a triangular factor: generic quotient vs block degeneracy",
        domain="mathphys",
        expression_sketch=(
            "T upper triangular, F = f(T) also upper triangular, F_ii = f(T_ii). "
            "For i < j the commuting identity F T = T F expands to "
            "(T_ii - T_jj) F_ij = T_ij (F_ii - F_jj) + sum_{k=i+1}^{j-1} "
            "(F_ik T_kj - T_ik F_kj). When T_ii != T_jj this is solved by "
            "division by (T_ii - T_jj). When T_ii = T_jj the scalar division "
            "is 0/0 and the algorithm is restated in blocks: partition T so "
            "that no two diagonal blocks share an eigenvalue, and solve a "
            "Sylvester equation for each superdiagonal block of F."
        ),
        latent_structure=(
            "Parlett recurrence is the first divided difference of f on the "
            "diagonal of T, with a Sylvester/block form as the confluent "
            "replacement when eigenvalues of adjacent blocks collide. "
            "Ladder R4: one commuting identity FT=TF unifies the generic "
            "quotient and the degenerate Sylvester stratum. Schur–Parlett "
            "evaluates f(A) by reducing to this triangular representation."
        ),
        proposed_ladder="R4_piecewise_unification",
        assumption_contract=ScientificAssumptionContract(
            symbol_assumptions={
                "T": {
                    "type": "matrix",
                    "space": "C^{n x n}",
                    "upper_triangular": True,
                },
                "n": {"integer": True, "positive": True},
            },
            function_domains={
                "f": (
                    "Defined on the spectrum of T (Higham–Al-Mohy Algorithm "
                    "4.2: 'a function f defined on the spectrum of T'). "
                    "No holomorphy is stated for the scalar recurrence."
                ),
            },
            nonzero_conditions=[
                P(
                    "Scalar Parlett recurrence (Algorithm 4.2): T has distinct "
                    "diagonal elements, so T_ii - T_jj != 0 in every division.",
                    src,
                ),
            ],
            positivity_conditions=[],
            real_valued_functions=[],
            analytic_domains=[
                P(
                    "Scalar algorithm: T upper triangular in C^{n x n} with "
                    "distinct diagonal elements, and f defined on the spectrum "
                    "of T (Higham–Al-Mohy Algorithm 4.2).",
                    src,
                ),
                P(
                    "Block algorithm: T upper triangular, partitioned in block "
                    "m x m form with no two diagonal blocks having an "
                    "eigenvalue in common, and f defined on the spectrum of T "
                    "(Higham–Al-Mohy Algorithm 4.3).",
                    src,
                ),
            ],
            branch_conventions=[
                "Primary matrix function of a triangular matrix: F is upper "
                "triangular with diagonal f(t_ii), using one branch of f at "
                "each eigenvalue (Higham–Al-Mohy, facts after Definition 2.2).",
            ],
            limit_domains=[
                P(
                    "The scalar recurrence is not defined when t_ii = t_jj; "
                    "that degeneracy is the block recurrence's hypothesis "
                    "('no two diagonal blocks having an eigenvalue in "
                    "common'), not a limit of the scalar formula inside "
                    "Algorithm 4.2.",
                    src,
                ),
            ],
            source_provenance=[
                src,
                "https://eprints.maths.manchester.ac.uk/1451/1/paper8.pdf",
                "DOI 10.1016/0024-3795(76)90061-5",
            ],
            derived_conditions=[
                P(
                    "F = f(T) commutes with T because f(T) is a polynomial "
                    "in T when f is defined on the spectrum (Higham Theorem "
                    "1.13 / Higham–Al-Mohy Theorem 2.3), which is the source "
                    "of FT=TF used to derive the recurrence.",
                    src,
                    DERIVED,
                ),
            ],
        ),
        public_source=(
            "B. N. Parlett, Linear Algebra Appl. 14 (1976) 117–121. "
            "Higham–Al-Mohy, Computing matrix functions, Acta Numerica 2010, "
            "Algorithms 4.2–4.3, https://eprints.maths.manchester.ac.uk/1451/1/paper8.pdf. "
            "Higham 2008, Chapter 9."
        ),
        why_not_cse_lgg=(
            "The generic superdiagonal formula is a rational expression; the "
            "equal-diagonal case is a Sylvester equation. CSE will not merge "
            "them. LGG cannot invent the commuting identity FT=TF as a "
            "representation that covers both strata."
        ),
        proposer_leak_risk=(
            "Hide Parlett, Schur–Parlett, divided difference, Sylvester. "
            "Show FT=TF, the triangular layout, and the two algorithmic "
            "branches (distinct diagonals vs shared eigenvalues)."
        ),
        notes=(
            "Do not run the scalar recurrence when diagonals coincide, and "
            "do not insert holomorphy. The block hypothesis is spectral "
            "disjointness of diagonal blocks, not 'generic parameters'. "
            "Do not claim the block form as a limit identity without a "
            "separate confluence theorem (that would be Daleckii–Krein / "
            "Hermite on the triangular factor, a different dossier)."
        ),
        rejected=False,
        is_guo=False,
    )


DOSSIERS: list[CandidateDossier] = [
    _hermite_interpolation_fa(),
    _daleckii_krein_loewner(),
    _resolvent_divided_difference(),
    _cauchy_dunford_resolvent(),
    _mathias_block_frechet(),
    _opitz_dd_matrix_function(),
    _kato_simple_eigenvalue(),
    _parlett_schur_degeneracy(),
]


def dossier_by_id(case_id: str) -> CandidateDossier:
    for d in DOSSIERS:
        if d.case_id == case_id:
            return d
    raise KeyError(case_id)


def validate_dossiers(dossiers: list[CandidateDossier] | None = None) -> list[str]:
    """Fail closed on Guo, missing contracts, and bad ladder names."""
    errors: list[str] = []
    seen: set[str] = set()
    items = dossiers if dossiers is not None else DOSSIERS
    for d in items:
        if d.case_id in seen:
            errors.append(f"duplicate case_id {d.case_id}")
        seen.add(d.case_id)
        blob = (d.case_id + " " + d.title).lower()
        if d.is_guo or "guo" in blob:
            errors.append(f"{d.case_id}: Guo is not admitted")
        if not guo_is_not_admitted(d):
            errors.append(f"{d.case_id}: guo_is_not_admitted failed")
        if d.assumption_contract is None:
            errors.append(f"{d.case_id}: missing ScientificAssumptionContract")
            continue
        ac = d.assumption_contract
        if not ac.source_provenance:
            errors.append(f"{d.case_id}: empty source_provenance")
        if d.proposed_ladder and d.proposed_ladder not in LADDER:
            errors.append(f"{d.case_id}: proposed_ladder {d.proposed_ladder!r} not in LADDER")
        for pred in (
            list(ac.analytic_domains)
            + list(ac.limit_domains)
            + list(ac.nonzero_conditions)
            + list(ac.positivity_conditions)
            + list(ac.derived_conditions)
        ):
            if pred.label not in (DECLARED, DERIVED):
                errors.append(
                    f"{d.case_id}: predicate {pred.statement!r} has label {pred.label!r}"
                )
            if pred.label == DECLARED and not pred.source:
                errors.append(f"{d.case_id}: DECLARED predicate missing source")
        if not ac.analytic_domains:
            errors.append(f"{d.case_id}: empty analytic_domains")
    if len(items) < 3 or len(items) > 8:
        errors.append(f"expected 3–8 dossiers, got {len(items)}")
    return errors


def dump_json(directory: Path | None = None) -> list[Path]:
    directory = directory or HERE
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    index = []
    for d in DOSSIERS:
        path = directory / f"{d.case_id}.json"
        path.write_text(json.dumps(d.to_dict(), indent=2) + "\n", encoding="utf-8")
        written.append(path)
        index.append(
            {
                "case_id": d.case_id,
                "title": d.title,
                "domain": d.domain,
                "proposed_ladder": d.proposed_ladder,
                "public_source": d.public_source,
                "json": path.name,
            }
        )
    index_path = directory / "index.json"
    index_path.write_text(
        json.dumps(
            {
                "owner": "C3 math-physics",
                "parent": "1075d80",
                "count": len(DOSSIERS),
                "is_guo": False,
                "dossiers": index,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(index_path)
    return written


if __name__ == "__main__":
    errs = validate_dossiers()
    if errs:
        raise SystemExit("dossier validation failed:\n- " + "\n- ".join(errs))
    paths = dump_json()
    print(f"validated {len(DOSSIERS)} dossiers")
    for p in paths:
        print(p)
