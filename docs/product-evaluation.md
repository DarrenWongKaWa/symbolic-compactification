# Product evaluation: many-body reviewer mode (October 2026)

This page states what the tool can be trusted with today, and the evidence
behind it. All numbers below come from runs on this branch.

## Two layers with different reliability

| Layer | What it does | Evidence | Verdict |
|---|---|---|---|
| **Checking engine** | Decides an encoded claim: identity, series, remainder, Matsubara sum, Fermi integral, definite integral, Langreth rule | Many-body benchmark v0: 27 of 29 answered, 27 of 27 correct, 0 false certifications. Derivation benchmark v1: every one of 25 decisive tool verdicts correct | Reliable when the claim is encoded correctly |
| **Reading a paper** | Turns a paper's LaTeX into claims, fixing what each symbol means | Four adversarial rounds, below | Research preview: fail-closed by design, but still misreads new constructions |

The engine's verdicts were never wrong in any benchmark. The risk lies in
the reading: the paper may mean something other than what the tool
extracted, such as a condition next to a display, an operator taken for a
number, a variable fixed by the text, or a convention stated three pages
earlier.

## Adversarial rounds

After the coverage upgrade, two independent reviewers (a Claude agent and
Codex) wrote inputs in each round that try to make the tool give a wrong
verdict. Every confirmed wrong verdict was fixed by a fail-closed rule and
added to `tests/fixtures/notes/adversarial/`. `golden.json` lists every
verdict on those files, each checked by hand.

| Round | Confirmed wrong verdicts | Typical classes |
|---|---:|---|
| 9 | 23 | integer indices in e^{2πin}, arbitrary-function readings, conditions after `\qquad`, matrices |
| 10 | 24 | relations that define a symbol (Γ/(2πρ) = V²), scoped redefinitions, pointwise products |
| 11 | 32 | operators and spin components, the paper's own n_F, sign conditions, approximations |
| 12 | 25 | E and I read as e and i, limits at −∞, Grassmann numbers, layout of align rows, text outside the printed paper |
| 13 | 12 | the new readers for real papers: derivatives with time-dependent parameters, `\tan^{-1}`, special-function names, `aligned[t]`, slashes after bare arguments |

The rate is not falling. Each round finds new classes; most come from
adversarial but plausible paper text. The 357 files collected so far give
no wrong verdict today. That does not show that no wrong verdict remains.

## Coverage

| Input | Decided, before the upgrade | Decided, now |
|---|---:|---:|
| Resonant-level note (17 displays, 4 planted errors) | 3 | 7 |
| Time-integral note (6 displays, 1 planted error) | 0 | 6 |
| JWM 1994, whole paper (one command, no conventions) | 2 | 2 |

Planted errors caught now: the sign of a high-frequency tail, a missing
Langreth term, and a dropped constant in a time integral. The transmission
error is flagged only when the text states the energies real.

The price of fail-closed reading is visible: an INVALID is withheld
whenever some fact the tool cannot check might rescue the claim. A dropped
term that removes a whole symbol from one side is therefore usually not
refuted. Most of a Keldysh paper (time convolutions of unknown functions,
traces, operator algebra) stays NOT_DECIDED.

## Sixteen real papers (swarm test)

Eight PRD-type thermal field theory papers and eight NEGF transport papers
were reviewed:

- hep-ph and hep-th: 0804.3414, 0808.3382, 0907.5007, 1311.2512,
  1607.01929, 1612.00466, 1802.09095, hep-ph/0603048;
- cond-mat: 1403.8035, 1408.3608, 1510.00762, 1511.03276, 1708.01124,
  1712.02308, 2007.14827, 2208.00180.

Four agents worked as a physicist's assistant, four papers each. Each
agent added conventions taken only from what the paper states. It then
checked every verdict independently with sympy and mpmath.

| Mode | Relations | VALID | INVALID | Wrong verdicts |
|---|---:|---:|---:|---:|
| One command, no conventions | 1 277 | 0 | 0 | 0 |
| With the assistant's conventions | 1 322 | 8 | 0 | 0 |

Two notes on the counts:
- The two INVALIDs the agents first obtained were wrong. Both were `ζ(4) =
  π⁴/90` and `ζ(2) = π²/6` with ζ declared an arbitrary function. Both are
  now withheld (`ARBITRARY_FUNCTION`). A paper that names the Riemann zeta
  function gets the real one (`zeta_fn`).
- Two of the eight VALIDs appeared only after this round's fix for glued
  letters (`px` read as p·x).

What blocks real papers, in this order:
1. integrals over unknown functions or with transmissions and Fermi
   functions of several leads;
2. derivatives of functions that are written bare;
3. sums over indices;
4. undefined named quantities;
5. ⟨…⟩ expectation values and traces.

The agents also found two likely errors in the papers themselves, which
the tool did not decide:
- a sign in 1511.03276, Eq. (81);
- a factor 3 in the μ² term of 0808.3382, Eq. (n5).

So on real papers the tool is today a strict checker for the algebraic
steps an assistant isolates. It does not review a paper on its own.

## Thirty more papers (second swarm test)

Thirty further papers were reviewed, none of them in the first set, ten of
each kind:

- **Thermal field theory and finite density** (hep-ph, hep-th, nucl-th):
  0805.4201, 0903.3946, 1207.5808, 1312.1204, 1702.07340, 2207.00534,
  hep-ph/0011229, hep-ph/0108026, hep-ph/0305001, nucl-th/0001040.
- **Condensed matter and many-body** (cond-mat): 0808.0931, 1111.5337,
  1611.01459, cond-mat/0309372, cond-mat/0512157, cond-mat/0606800,
  cond-mat/0608682, cond-mat/0610630, nlin/0301033, quant-ph/0702032.
- **Mathematical physics and lecture notes** (math-ph and others): 0902.1749,
  0909.2209, 1002.4238, 1002.4692, 1005.2389, 1104.4330, 2108.11210,
  math-ph/0303052, math-ph/0409034, quant-ph/0205085.

Six agents worked as a physicist's assistant, five papers each, with the
same rules as before: add only conventions the paper states, then check
every verdict independently with sympy and mpmath.

| Mode | Relations | VALID | INVALID | Wrong verdicts |
|---|---:|---:|---:|---:|
| One command, no conventions (all 30 papers, after the fixes) | 3 821 | 3 | 0 | 0 |
| With the assistant's conventions (30 papers) | 2 734 | 24 | 0 | 0 |

Notes on the counts:
- 2207.00534 (a 7 900-line lecture course) did not finish within 8 minutes,
  so its agent reviewed two sections of it (123 relations, 7 of the 24
  VALIDs). Each card re-read the whole paper. The displays, macros and
  conventions are now read once per paper. The whole course (1 229
  relations) then takes 232 s, and the other 29 papers 112 s instead of
  796 s. In the whole course the 6 one-command VALIDs of the two-section
  copy stay undecided. First, a remark that a gauge fixing "does not
  commute" with a limit had marked every quantity a matrix; that is fixed.
  Now k₀ is the blocker: the course sets it to several values (2πinT,
  (2m+1)iπT, ±ω_k), so it is not read as a free symbol
  (`NAMED_QUANTITY_UNDEFINED`).
- The first one-command run of this set gave one wrong VALID. In 1005.2389
  a boundary condition, u(0) = u(a) = 0, was read as a definition of u. This
  was fixed before the agents started: a value at a point no longer counts
  as a definition. The three VALIDs above come from the fixed tool.
- One VALID (1104.4330, display BMil) was vacuous. The agent defined a
  quantity from a display and then checked that same display, so the step
  was its definition checked against itself. Such a step is now withheld
  (`DEFINED_BY_THIS_DISPLAY`). The table counts it as VALID because that is
  what the tool said then.

No guard was found to let a wrong verdict through. Once the engine's raw
result was wrong and a guard withheld it. In math-ph/0409034, a definition
of R(x) from the Duffing section was applied in the next section, where
R(x) means something else. `CONSTRAINED_IN_TEXT` held it back by chance.
Such a refutation is now withheld on purpose
(`DEFINITION_FROM_ANOTHER_SECTION`).

One true refutation was withheld. In 2207.00534 (display lf2), the engine
found the sign error described below (`CLAIM_DIFFERS_FROM_RESIDUE_SUM`).
It was not reported because the summed variable k₀ is "constrained" by the
text (k₀ = iωₙ). The summed or integrated variable is now exempt. The step
still stays NOT_DECIDED, because the text also gives ω_k a value.

Fixed after this round:
- sums over all integers;
- sin²(x), |x| inside a logarithm, (−1)ⁿ and 2ⁿ as powers;
- G_> and G_< subscripts, the `\>` spacing and `\<`, `\>` macros;
- `{\cal E}`, `\Biggl` and `\textstyle`;
- Matsubara sums over the paper's definitions (ω_k = √(k² + m²)), with exact
  residues at such poles;
- the two guards above;
- "does not commute" marks the paper's quantities as matrices only when it
  has a mathematical subject, and the arguments of an operator (k in a(k))
  are no longer taken for operators.

Likely errors in the papers that the agents found while checking (the
tool did not decide these; they need a physicist to confirm):
- 0902.1749, the unnumbered low-temperature display (source line 202):
  tanh² where −∂f/∂ε gives cosh². As printed, the integral diverges.
- 1002.4692, displays eq19 and eq20: sinh y where sinh(πy) is needed; also
  eq13.
- 1611.01459, display eq28: a missing factor t.
- 2207.00534, displays lf2 and aex7: the tadpole frequency sum has the wrong
  sign. With k₀ = iωₙ every term is negative, so the sum is
  −(1 + 2n_B)/(2ω_k).
- hep-ph/0108026, display eq20, second relation: an extra factor 1/z
  compared with display ber2.
- math-ph/0303052, display omega3duff: 64 where 69 follows.
- math-ph/0409034, the display after b₀ and b₁: x₊² where x₋² is meant, in
  the denominator of λ.
- quant-ph/0702032, display eq:LZphases: a factor 2.

(Display names are the paper's `\label`s or the tool's step ids.)

What blocks real papers is the same as in the first round. Of the 2 710
undecided relations, most (about three quarters in the agents' counts)
hold `\int`, `\sum`, `\partial`, ⟨…⟩ or matrix notation the reader does
not take apart. Next come papers
that state their quantities are matrices, where `NONCOMMUTING_STATED`
blocks every relation, scalar ones included. After that come named
quantities defined only in words, and displays that carry a condition.

Across both rounds (46 papers, about 4 000 relations), three wrong verdicts
appeared, all in first runs: the two ζ refutations and the boundary-condition
VALID. Each was fixed before the final counts, and none remains in them.

## Two readers and the step ledger (2026-10-03)

Every LaTeX quote is now read twice, by the tool's reader and by SymPy's
LaTeX parser, and counts only when the two agree
(`docs/encoding-cookbook.md`, "Two readers for every LaTeX quote").
- Golden adversarial notes: the 110 decided steps are unchanged; no new
  verdict appeared.
- 46 papers, card by card in strict mode: 9 VALID before and after, nothing
  else decided either way. Of 4 909 fields the tool's reader had read, 462
  are now refused: 354 read differently by SymPy, 108 not readable by it.
  In a sample of 30 disagreements, about 20 were the tool's own misreadings
  (subscript after a superscript, `{\rm X}` in a subscript, `\mp` glued into
  a subscript, `\frac{d}{dx}` before `\Bigl(` read as 1/x); about 4 were
  SymPy's (`ds^2`, `\vec p`), the rest unreadable to both. Before, these
  quotes were held back only because other guards happened to block their
  cards.

Steps that go from one display to another can now be checked from a step
ledger ("Eq. X -> Eq. Y using R", every formula quoted;
`docs/encoding-cookbook.md`, "Steps across displays"). On Appendix D of
Guo et al. (PRL 136, 206303) a 12-step ledger gives 12 VALID: 7 by exact
algebra and 5 under quoted relations (metric-velocity relation,
ε₂₁ = −ε₁₂, Feynman–Hellmann identity, Berry curvature of band 1), each with
explicit cofactors. The whole paper in one command gives 1 VALID of 264
relations. Mutated ledgers (wrong pairing, a missing index instance of a
relation, an unneeded relation, a quote not in the paper) gave no wrong
verdict: the unneeded relation leaves the step VALID (exact without it),
every other mutation is NOT_DECIDED. An independent review of this code
found four ways to a wrong verdict (relations that make a denominator
vanish, guards lifted by name only, counterexamples outside the declared
domain, `under:` scope checks); each is fixed and has a test.

**Ledgers on thirteen papers (2026-10-04).** Agents wrote step ledgers for 12
arXiv papers plus Guo et al.: 651 steps. Each step is typed. The tool checks
only `algebra` and `sum-termwise` steps; integral, limit, approximation and
definition steps are listed for the reviewer (`NEEDS_REVIEWER`), on the
reviewer page as well.
- Algebra steps decided: 32 of 177 (18 %), all VALID. Sum-termwise steps
  decided: 4 of 47. INVALID: 0.
- 32 refutations were found by the engine but withheld by a guard, mostly
  names whose value the text gives elsewhere (`NAMED_QUANTITY_UNDEFINED`).
- Ledger agents found two ways to a wrong verdict, and both are fixed, each
  with a test:
  - An index rename did not reach inside a macro (`\rpq` is `r_{pq}`), so a
    correct step came out INVALID.
  - `\Delta T` was read as Δ·T by both readers, so `ΔT/ΔV = T/V` came out
    VALID. A name right after `\Delta` or `\delta` is now refused, which
    costs one paper 9 VALID steps.

## What this supports

- **Claim:** a VALID means the quoted relation is an exact identity under
  the listed assumptions, and the replay certificate lets anyone check it.
- **Claim:** an INVALID comes with a counterexample and means "look here".
- **Not claimed:** that the tool finds every error, or reviews a whole paper.
- **Not claimed:** that a VALID cannot rest on a misreading. Since
  2026-10-03 each LaTeX quote must be read alike by two independent readers,
  which removes structural misreadings; the conventions both share (listed
  in the cookbook) and every assumption still need a person's check, and the
  reviewer page shows them.

In short, the checking engine is ready for use. The paper reader is a
research preview, to be used as a second pair of eyes whose readings are
always shown.
