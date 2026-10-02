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

The rate is not falling. Each round finds new classes; most come from
adversarial but plausible paper text. The 300 files collected so far give
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

## What this supports

- **Claim:** a VALID means the quoted relation is an exact identity under
  the listed assumptions, and the replay certificate lets anyone check it.
- **Claim:** an INVALID comes with a counterexample and means "look here".
- **Not claimed:** that the tool finds every error, or reviews a whole paper.
- **Not claimed:** that a VALID cannot rest on a misreading. The reviewer
  page lists every assumption and reading it used, so a person can check
  them.

In short, the checking engine is ready for use. The paper reader is a
research preview, to be used as a second pair of eyes whose readings are
always shown.
