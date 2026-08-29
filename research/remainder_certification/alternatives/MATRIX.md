# Decision matrix — remainder backends

Line: remainder certification (not V6). Parent `adbfd9f`.
D2 **LOCKED**. Probe: `probe.py` (replayed; no new packages).

**CASE R-E** means: adopt an existing certified remainder
backend *now* because it is mature, clearly superior on
symbolic affine polygamma, and currently usable.

CASE R-E is **rejected**. Recommendation: **CONTINUE_CUSTOM**.

The test class is

```
f(α₀ + c t) = Σ_{r=0}^N f^{(r)}(α₀) (c t)^r / r!  +  R_{N+1}(t)
```

with `f` polygamma of fixed order and `α₀` symbolic. The
verifier needs a checkable condition that `R_{N+1}(t)=O(t^{N+1})`
under **declared** analytic-domain hypotheses. Finite coefficient
agreement is not that condition.

---

## CASE R-E gate (all required)

1. Mature remainder (or analytic-continuation) backend.
2. Clearly superior to a custom Taylor/Cauchy certificate
   on this class.
3. Currently usable: importable in the project interpreter;
   no `pip install`; no heavy Sage/FLINT integration.
4. Sound as a remainder-order proof, or honest fail-closed.
5. Decides — or fail-closes with an explicit missing
   hypothesis — on **symbolic** affine polygamma.

No evaluated method meets (2)+(3)+(5) together.

---

## Matrix

| Method | Soundness | Decidability on symbolic affine polygamma | Dependency cost | Use now? |
|---|---|---|---|---|
| Custom remainder certificate (Taylor / Cauchy bound + listed domain) | Sound when every used hypothesis is class A or B and recorded on `RemainderCertificate`. Class C/D cannot emit `CERTIFIED`. | Decides `CERTIFIED` only after a neighborhood / distance-to-pole proof; otherwise `ASSUMPTION_REQUIRED`, `NONANALYTIC`, or `UNKNOWN`. That is the intended contract. | In-tree. No new packages. | **Yes — continue** |
| Exact special-function identities (recurrence, reflection, Hurwitz-ζ rewrite; **not** identity tables) | The identities are standard and sound as *rewrites* (DLMF 5.15; `expand_func(polygamma(n,z+1))`). | They do not prove holomorphy of `polygamma(n, α₀+c t)` at `t=0` for free `α₀`. The Lagrange/integral remainder is still a higher polygamma, which still needs `α₀` off `Z_≤0`. Probe: recurrence holds; `remainder_ok(a+t,t)` stays False. | Already in SymPy 1.14. | Auxiliary only |
| Holonomic / D-finite DEs (`sympy.holonomic`) | Sound for D-finite germs (linear ODEs with polynomial coefficients). Γ and polygamma are **not** D-finite: `d/dz polygamma(n,z)=polygamma(n+1,z)` is an infinite chain, not a finite-order annihilator. | `expr_to_holonomic(polygamma(k,·))` and `gamma` raise `NotImplementedError`. Lookup table is exp/sin/erf/… only. Cannot emit a remainder bound. | Already in SymPy. Unusable for this class. | No |
| `ore_algebra` / Mezzarobba numeric analytic continuation | Mature for *D-finite* numeric continuation and remainder balls. Wrong object here. | Package absent (`ModuleNotFoundError: ore_algebra`, `sage`). Even if present, polygamma is not D-finite. | Heavy (Sage optional). Not installed. Do not pip-install. | No |
| Arb / python-flint ball arithmetic | Mature *numeric* enclosures and Taylor balls (Johansson). Sound for a numeric point, not a symbolic identity. Numeric agreement is never hop `ZERO` (engine semantics). | `flint`, `python_flint`, `arb` are **not importable**. A later install would still only enclose numeric instances of `α₀`; it cannot discharge `α₀ ∉ Z_≤0` as a symbolic predicate. | **Absent.** Do not pip-install. Do not vendor FLINT. | No |
| mpmath interval (`mpmath.iv`) | Interval arithmetic for some elementary and gamma functions. Not a theorem prover. `iv.zeta` currently errors (`bernoulli` missing on the iv context). | No `iv.psi` / `iv.polygamma` / `iv.digamma`. Cannot parse symbolic `α`. Finite differences of `iv.loggamma` are not implemented and would still be numeric. | mpmath 1.3.0 already present (SymPy dependency). | No |
| Symbolic analytic continuation in SymPy (`unpolarify`, `nseries`, `fps`) | Branch normalization and formal series. Not a continuation certificate. `fps(polygamma(0,a+t))` does not even build a `FormalPowerSeries`. | Formal Taylor in `t` for symbolic `α₀` does not prove a disk of holomorphy. | Already installed. | No |
| SymPy `series` + `O(t^n)` truncation | **Unsound as a remainder bound.** `O` is a truncation marker. | `polygamma(0,a+t).series(t,0,3)` emits the holomorphic jet plus `O(t**3)` without testing whether `a` is a pole. The same series at `a=0` is `zoo+…`; genuine `polygamma(0,t).series` raises `PoleError`. | Already installed. | No |
| V5 `remainder_ok` (SymPy `series` gate) | Sound *fail-closed* gate: True only when the affine argument at `t=0` is a concrete number not in `Z_≤0` (or the polygamma order is entire). False → remainder `UNKNOWN`, never hop `NONZERO`. | Symbolic `α` → False / `UNKNOWN`. Known insufficient for LEVEL C on this class. Keep as a gate, not as the certificate. | In-tree (`research.coefficient_laurent.remainder`). | Gate only |
| `sympy.singularities` / `ask` | Incomplete domain tool: `singularities(polygamma(0,z),z)` and `singularities(gamma(z),z)` are `EmptySet` (rational poles are seen). | Cannot prove `α₀` is not a pole from free symbols. `ask(Q.integer(α))` is `None` on the motivating affine form. | Already installed. | No |

`CERTIFIED` remainder is not hop `ZERO`. Hop composition stays
`compose_hop_verdict`. LEVEL B coefficients + remainder
`UNKNOWN` stay hop `UNKNOWN`.

---

## Experiments (probe replay)

Interpreter: project `.venv`, `PYTHONPATH=.`, no extra installs.

| fact | result |
|---|---|
| `import flint` / `python_flint` / `arb` / `sage` / `ore_algebra` / `gmpy2` | `ModuleNotFoundError` |
| `sympy`, `sympy.holonomic`, `mpmath` | present (1.14.0 / 1.3.0) |
| `remainder_ok(1+t,t)` | True |
| `remainder_ok(a+t,t)` | False, verdict `UNKNOWN` |
| `polygamma(0,a+t).series(t,0,3)` | jet + `O(t**3)` |
| `polygamma(0,t).series(t,0,3)` | `PoleError` |
| `expr_to_holonomic(exp(x))` / `sin(x)` | converted |
| `expr_to_holonomic(gamma(x))` / `polygamma(k,·)` | `NotImplementedError` |
| `mpmath.iv.gamma` on a numeric interval | enclosure returned |
| `mpmath.iv.psi` / `polygamma` | missing |
| `mpmath.iv.zeta(2)` | `AttributeError` (`bernoulli`) |
| `expand_func(polygamma(0,z+1))` | `polygamma(0,z)+1/z` |
| `singularities(polygamma(0,z),z)` | `EmptySet` |

---

## Why not CASE R-E even later

Installing python-flint would add a numeric enclosure backend.
That is the same evidence class as V5-J probes: useful to
*refute*, forbidden as `ZERO`. It does not decide symbolic `α₀`.

Installing Sage + `ore_algebra.analytic` would add D-finite
continuation. Polygamma is not D-finite.

Exact identities are already available and already insufficient.

So a future optional extra does not change the remainder
authority. The authority remains a custom certificate with
explicit assumptions.

---

## Recommendation

**CONTINUE_CUSTOM** — not **CASE R-E**.

Implement the generic remainder theorem in this cluster
(neighborhood, Cauchy/Taylor bound, order algebra, listed
domain). Do not integrate a heavy backend. Do not unlock D2.
Do not restore retracted LEVEL_C hop `ZERO`.
