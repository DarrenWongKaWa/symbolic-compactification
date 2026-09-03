# V1 vs V2 — arXiv:2604.04520

V1 files: `v1/audit.html`, `v1/audit.md` (frozen RESULTS table).
V2 files: `v2/audit.html`, `v2/audit.md` from `evidence/audit.json`.

V2 is **not** greener. Machine-certified edges: **1** (2×2 unitarity under
\(S^\dagger S=I\)), same as V1’s only `ZERO_UNDER_SUBSTITUTION` row.

| Criterion | V1 | V2 | Evidence |
|---|---|---|---|
| Correct equation inventory | Partial. Claimed 94 = 12+82. Split the S-matrix `array` `\\` into two numbered rows, so main-text numbers after (1) are off by one. | **Better.** Independent recount: **93 = 11+82**. Rice–Mele \(H(k)\) is inline, not numbered. Appendix A–E 18/18/28/10/8 unchanged. | `input/inventory.json`; `tools/inventory.py` |
| Major claims identified | No paper-level claims. First screen is completeness + Sign queue + A–E chips. | **Better.** C1–C5: TR+dissipation; Eq. (4)→(5) geometry; low-\(T\) \(O(\Gamma^2)\); high-\(T\)/metal \(O(\Gamma)\); Rice–Mele numerics. | `v2/audit.html` §B |
| Load-bearing claim coverage | 35 edges, mostly adjacent appendix bookkeeping; orange by default. | **Better.** 17 reconstructed relations, 13 marked load-bearing. Sequence chips A-1⋯A-18 are demoted to §E. | `evidence/audit.json` `load_bearing` |
| Eq. (4) → Eq. (5) traceability | V1’s “main 5 → main 6” is the Green kernel → \(\sigma^{\alpha\alpha\alpha}\), but numbering is shifted and the Appendix D chain is one orange row (`longitudinal kernel → σ`). | **Better.** Published (4)=`eq:currentbyExcitation`, (5)=`eq:sigma2`. Graph: (4) → C-1 → C-2 → D-1 → TR identities → \(\mathcal{A}\) → shift vector → (5). | `v2/audit.md` §C |
| Assumptions explicit | One `A?` column mixing substitutions, gauge, and \(\Gamma\to 0\). | **Better.** Separate transformation type, assumption list, and certification status on every edge. | ledger tables |
| Human-review tasks actionable | Four Sign buttons: “record that you accept this cancel.” | **Better.** Queue O1, O5–O7, O2, O8, O9, O3 with claim / why-not-certified / paper evidence / decision. Accept does not stamp Exact. | `v2/audit.html` §D |
| HTML readability | Usable ledger; first screen is inventory-first. | **Better for a physicist.** Summary → claims → (4)→(5) graph → reviewer queue → map → ledger. | section order A–F |
| Markdown mathematical integrity | Weak. `v1/audit.md` is a status table without TeX (`Inventoried numbered lines: 94`, no \(\sigma^{\alpha\alpha\alpha}\)). | **Better.** Independent MD renderer keeps labels, `$$...$$` kernels, claim IDs, and tables. | `v2/audit.md` vs `v1/audit.md` (3.7 KiB vs 21 KiB) |
| HTML/MD semantic consistency | N/A (V1 MD is not generated from the HTML model). | **Better.** Both from `audit.json`. `tests/test_v2_2604_audit.py` checks IDs/statuses and byte-matches committed files. | test file |
| False-certification resistance | Strong. 0 Exact, 1 ZUS, remainders orange. | **Equal.** No new Exact. C3/C4 stay `ASYMPTOTIC_UNCERTIFIED`. C5 is `NUMERICAL_SUPPORT`. C2 is `GAP`. | status counts |
| Fresh-agent usability | Skill/HTML_RENDERER emit a Guo-like ledger (V1 style). | **Improved if the agent reads `examples/2604.04520/README.md` and `docs/paper-audit.md`.** See `CLEAN_ROOM_TEST.md`. | clean-room note |

## What V1 still does well

V1 is the right fail-closed default: it does not pretend Appendix Green
functions are Exact. V2 keeps that. The V1 appendix chip map remains a
useful secondary index (copied conceptually into V2 §E).

## What V2 still does not do

- It does not compile Appendix D antisymmetrization or the shift-vector
  identity. Those stay `GAP`.
- It does not reproduce the Rice–Mele figures.
- It does not certify remainder bounds.
- Load-bearing coverage is still incomplete relative to every appendix
  residue case in C (those remain inventory, not fake edges).

## Verdict

V2 is substantially clearer for a physicist who needs to know **what the
paper claims, what was actually checked, and where judgment is required**,
without being scientifically greener than V1.
