# Reviewer 6 — Track V5 reproducibility replay

Isolated checkout of parent `fb3b929`. No LLM. Did not read other
reviewer notes. Did not retune hops. Did not unlock D2. Did not edit
frozen authorities. Did not rewrite historical JSON. Did not start V6.
Did **not** rerun `eval/guo_v5_rescore.py` (12×40 s ell-hop rescore).
Did not move tags.

## Checkout

| | |
|---|---|
| worktree | `/private/tmp/wt-v5-review-r6` |
| branch | `work/v5-review-r6` |
| parent | `fb3b929432b3de024e510835ff6f9fd4700c2ae1` |
| parent subject | Certify G0016 to G0013 at LEVEL C via per-polygamma C0 match. |
| python | `/Users/kawawong/Projects/symbolic-compactification/.venv/bin/python` → CPython 3.12.13 |
| sympy | 1.14.0 |
| host | Darwin 25.4.0 arm64 (`Kawas-Mac-mini.local`; Darwin Kernel Version 25.4.0, `RELEASE_ARM64_T6041`) |
| date | 2026-08-29 (local +08; UTC 2026-08-28T23:52:51Z) |
| `PYTHONPATH` | `.` (this worktree) |

Parent authorities named on this checkout resolve:

- V4 close `248d247` — *Close Track V4: atom-series certifies 327-op diagonal hops (J-C).* (`parent_track_v4` in the V5 freeze)
- V5 freeze `7102e8a` — *Freeze Track V5 inputs and Laurent coefficient IR.*
- V5 L-D close / tag `ba2a0ce` — *Close Track V5: sparse Laurent does not decide G0016 to G0013 (L-D).*
- This parent `fb3b929` — L-A LEVEL C on G0016→G0013

`.env` is **not tracked**. `.gitignore` lines 41–42 ignore `.env` and
`.env.*`. `git ls-files` has no `.env`. This worktree has no `.env` file.

## 1. Freeze integrity (live)

```
/Users/kawawong/Projects/symbolic-compactification/.venv/bin/python -m pytest tests/test_cl_freeze.py -q
```

**3 passed in 0.01s** (3 collected, 0 failed).

`research/coefficient_laurent/FROZEN_INPUTS_V5.json` file-bytes sha256:

```
3d6a5bf2ba327b8b8b3f91609f185494ade3b0eeec303175ab7df98c014d16fc
```

21915 bytes. Same sha256 at freeze commit `7102e8a` (`git show
7102e8a:research/coefficient_laurent/FROZEN_INPUTS_V5.json | shasum -a 256`).
Git blob `2bd90e9cad344306402da86578ac7b794dc1119c` is identical at
`7102e8a` and `HEAD`. Freeze JSON was not rewritten after the freeze
commit.

On-disk payload (and `freeze_v5.build()`):

| field | value |
|---|---|
| `n_hops` | 18 |
| `no_llm_calls` | `true` |
| `no_new_hypotheses` | `true` |
| `primary_hop` | `guo-p2-s0-i3:G0016->G0013` |
| `parent_track_v4` | `248d247` |
| `method_version` | `v5-coeff-laurent-1` |
| `track` | `V5` |
| primary hops with `is_primary` | 1 of 18 |

`freeze_v5.build()` rebuilt in memory and serialized with the same
`json.dumps(..., indent=2) + "\n"` as `main()` is **byte-identical**
to the committed file (same sha256). `main()` was not invoked; the
on-disk freeze was not written. Serializer drift: none.

Parent-file hashes recorded in the blob still match disk:

| recorded field | sha256 | live match |
|---|---|---|
| `v4_freeze_sha256` | `e72076d870f50b67aed2684f8460b100b34decd2823e37807903981e60de16e4` | yes (`FROZEN_INPUTS_V4.json`) |
| `v4_rescore_sha256` | `63efcaf0c62996f0b4083e068fd3de0124190f9d16b32a549c39366878ed2b2d` | yes (`GUO_HOP_RESCORE.json`) |

All 18 hops have V4 verdict `UNKNOWN`. The 18 ids are the six
generic→diagonal covering triples (G0016→G0013/14/15 and
G0023→G0020/21/22) on families `s0-i3`, `s1-i2`, `s1-i3`, `s2-i2`,
`s2-i3`, `s4-i1`.

`tests/test_cl_freeze.py` does **not** pin the file sha256. It checks
`build()` metadata and, if the file exists, only `n_hops` and
`primary_hop`. The freeze-commit `STATUS.md` quoted this sha256;
current `STATUS.md` (rewritten at L-D then L-A) no longer does.

## 2. Package tests (live)

```
PYTHONPATH=. /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python -m pytest \
  tests/test_cl_atoms.py tests/test_cl_basis.py tests/test_cl_c0.py \
  tests/test_cl_cache.py tests/test_cl_cache_audit.py tests/test_cl_falsifier.py \
  tests/test_cl_freeze.py tests/test_cl_generic.py tests/test_cl_grouping.py \
  tests/test_cl_numeric.py tests/test_cl_pg_series.py tests/test_cl_poles.py \
  tests/test_cl_rational.py tests/test_cl_remainder.py tests/test_cl_schema.py \
  tests/test_cl_sparse.py -q
```

**163 collected, 163 passed, 0 failed, 1.96s.** Tree stayed clean
(`git status --porcelain` empty).

| file | collected | role |
|---|---:|---|
| `tests/test_cl_atoms.py` | 11 | reconstruct/decompose; frozen-hop atom map |
| `tests/test_cl_basis.py` | 9 | polygamma derivative Taylor; never hop ZERO |
| `tests/test_cl_c0.py` | 8 | per-polygamma rational C0; no full-kernel together |
| `tests/test_cl_cache.py` | 6 | full-text keys; G0014 ↛ G0016 |
| `tests/test_cl_cache_audit.py` | 11 | V5-K alias attacks; false alias = 0 |
| `tests/test_cl_falsifier.py` | 27 | five named attacks + controls; false ZERO = 0 |
| `tests/test_cl_freeze.py` | 3 | freeze metadata (not file sha256) |
| `tests/test_cl_generic.py` | 1 | live generic suite; false ZERO = 0 |
| `tests/test_cl_grouping.py` | 12 | per-atom grouping keys |
| `tests/test_cl_numeric.py` | 13 | numeric probe never returns ZERO |
| `tests/test_cl_pg_series.py` | 6 | per-atom polygamma series |
| `tests/test_cl_poles.py` | 12 | negative coefficients; leftover \(t^{-1}\) is NONZERO |
| `tests/test_cl_rational.py` | 17 | rational prefactor series / convolution |
| `tests/test_cl_remainder.py` | 15 | remainder sufficiency; remainder-false → UNKNOWN |
| `tests/test_cl_schema.py` | 4 | LEVEL A ≠ ZERO; LEVEL C all-zero; surviving pole NONZERO |
| `tests/test_cl_sparse.py` | 8 | sparse add/convolve never `together` of summed kernel |
| **total** | **163** | |

`eval/generic_suite.run()` (invoked by `test_cl_generic.py`) **writes**
`GENERIC_SUITE.json` and `GENERIC_SUITE.md` as a side effect. On this
checkout the write is byte-stable vs the committed files (sha256
unchanged; no dirty tree). A non-deterministic `run()` would rewrite
historical JSON.

## 3. Generic suite (live, cheap)

```
PYTHONPATH=. /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  research/coefficient_laurent/eval/generic_suite.py
```

Stdout: `{"n": 4, "false_ZERO": 0, "pass": true}`.

| id | expect | got |
|---|---|---|
| `B-full-cancel` | ZERO | ZERO |
| `C-surviving-pole` | NONZERO | NONZERO |
| `E-wrong-order` | NONZERO | NONZERO |
| `A-atoms-only-not-zero` | UNKNOWN | UNKNOWN |

`false_ZERO = 0`. Surviving \(t^{-1}\) with matching \(t^0\) is not
ZERO. LEVEL A atoms-only is UNKNOWN, not ZERO.

Committed hashes (unchanged after the live write):

| file | sha256 |
|---|---|
| `GENERIC_SUITE.json` | `768e20a8493397fa06747e37edfbc0b408d11c347eada54a4f5c3fbca7cebaf8` |
| `GENERIC_SUITE.md` | `aa2b202e99825c8eb9497f2f0e27683868987b960eabca6edea4bce4995f29c1` |

## 4. Committed rescore artifacts (not rerun)

`EDGE_SECONDS = 40.0` in `eval/guo_v5_rescore.py`. The 12 ell-hops are
process-timeout `UNKNOWN` at that budget. This review did **not**
rerun the 12×40 s job.

Files exist, are git-tracked, were introduced on L-D close `ba2a0ce`
and rewritten on this parent `fb3b929`:

| artifact | bytes | sha256 |
|---|---:|---|
| `GUO_V5_RESCORE.json` | 7769 | `6cef7da88c38008b4ce92a8de1750717f749aea6ad79559a557a381371768661` |
| `GUO_V5_RESCORE.csv` | 1767 | `13ca5ab346bc3a79e5487e229dfc8165df142bf0e0c559569ea0a1c54d7e4908` |
| `GUO_V5_RESCORE.md` | 1519 | `3449c1ea50b3340cc39f7e21c9e9a54e261ae74f60c823d8c4d4fbc0efa611f7` |

JSON header:

- `n_hops=18`, `ZERO=6`, `NONZERO=0`, `UNKNOWN=12`, `case=L-A`
- `no_llm=true`
- `FAMILY_ZERO=0`, `FAMILY_NONZERO=0`, `FAMILY_UNKNOWN=7`
- `d2_unlocked=false`
- primary `guo-p2-s0-i3:G0016->G0013`: `ZERO` / `LEVEL_C` / `neg=ZERO` /
  `c0=ZERO` / `remainder=ZERO` / `max_ops=1696` / `together=false` /
  `v4=UNKNOWN`

CSV has the same 18 `hop_id`s in the same order. Overlapping fields
match JSON (bools/nulls stringified; UNKNOWN `neg`/`c0`/`remainder`/
`max_ops`/`together` are empty CSV cells vs JSON `null`). MD table
matches JSON on `(hop, verdict, level, neg, c0, max_ops)` including
`None` for UNKNOWN ell-hops. MD header:

```
hops ZERO=6 NONZERO=0 UNKNOWN=12 case **L-A**
primary guo-p2-s0-i3:G0016->G0013: ZERO (LEVEL_C) neg=ZERO c0=ZERO
FAMILY_ZERO=0 D2 unlocked=False
```

Six LEVEL_C ZERO hops (all m→n generic→diagonal; `max_ops=1696`):

- `G0016->G0013` on `s0-i3`, `s1-i2`, `s2-i2`, `s4-i1`
- `G0023->G0020` on `s1-i3`, `s2-i3`

Twelve UNKNOWN LEVEL_A ell-hops (`G0016->G0014/G0015`,
`G0023->G0021/G0022` on the same six families). NONZERO = 0.

JSON `families[]`: 7/7 `FAMILY_UNKNOWN` (including `s2-i4`, which has
no V5 generic→diagonal hop in the freeze). That matches
`TRACK_V5_CLOSED.md` / `VERDICT.md` / `STATUS.md` on this parent:
case **L-A**, FAMILY_ZERO=0, D2 locked.

No pytest assertion pins `GUO_V5_RESCORE.json`. Bit-rot of the rescore
table would not fail the package-test command above.

## 5. Stale-doc audit (report only; not edited)

Authorities that **agree** with parent `fb3b929` (L-A, G0016→G0013
LEVEL_C ZERO, 6/0/12, FAMILY_ZERO=0, D2 LOCKED, publication E):

| file | agrees with `fb3b929`? |
|---|---|
| `research/coefficient_laurent/STATUS.md` | yes (CASE L-A; LEVEL_C ZERO; ell UNKNOWN; D2 LOCKED; E) |
| `research/coefficient_laurent/VERDICT.md` | yes (20-question close; publication **E**; D2 no) |
| `research/coefficient_laurent/TRACK_V5_CLOSED.md` | yes (6 ZERO / 0 NONZERO / 12 UNKNOWN; L-A; FAMILY_UNKNOWN; D2 LOCKED) |
| `research/coefficient_laurent/GUO_V5_RESCORE.{json,csv,md}` | yes (see §4) |
| `research/coefficient_laurent/PROTOCOL.md` | protocol, not a close statement; D2 locked until FAMILY_ZERO/NONZERO; no L-A/L-D case label |
| `research/coefficient_laurent/OWNERS.md` | ownership only |

**Stale vs `fb3b929`** (still describe the L-D / freeze-era state;
`git diff ba2a0ce fb3b929` is empty on these paths):

| file | stale claim |
|---|---|
| `research/PROGRAM_STATUS_V5.md` | **CASE L-D**; “18/18 generic→diagonal hops UNKNOWN; LEVEL B on m→n negatives; no LEVEL C”. Last commit `ba2a0ce`. Publication E and D2 LOCKED still happen to be correct. |
| `research/coefficient_laurent/literature/CLASSIFICATION.md` | G0016→G0013 is `UNKNOWN`; packaged routing is a **GAP** “because G0016→G0013 is not `LEVEL_C` `ZERO`”. Last commit `9bc123e`. |
| `research/coefficient_laurent/literature/README.md` | “G0016→G0013 is `UNKNOWN`”; “Do not claim Track V5 closed.” |
| `research/coefficient_laurent/literature/HANDOFF.md` | “GAP until G0016→G0013 is `LEVEL_C` `ZERO`.” Parent SHA `7102e8a`. |
| `research/coefficient_laurent/literature/METHODS.md` | “**not closed**; freeze only (`7102e8a`); G0016→G0013 UNKNOWN” |

`research/PROGRAM_STATUS.md` is Track V (V-D), not a V5 close file.

**Missing:** `REPRODUCIBILITY_V5.md` (no such path at repo root,
`research/`, or `research/coefficient_laurent/`). Track V3 has
`research/iterated_confluence/REPRODUCIBILITY_V3.md`. There is no V5
equivalent pinning freeze sha256, pytest command, or “do not rerun
40 s ell-hops.”

Agent HANDOFF/README under `cache_audit/`, `numeric/`, `remainder/`
are line-scoped, not track-status.

## 6. Tag `coefficient-space-laurent-v1`

Lightweight tag → **`ba2a0ce`**
(`ba2a0ced1fc1ca308575ef40ab8a57dde9f0cde1`),
*Close Track V5: sparse Laurent does not decide G0016 to G0013 (L-D).*
2026-08-28 18:50:12 +0800.

| candidate | SHA | tag points here? |
|---|---|---|
| freeze `7102e8a` | `7102e8a3884e4f24da453c54f72263fbbb28f2ea` | **no** (tag descends from freeze; does not name it) |
| L-D close `ba2a0ce` | `ba2a0ced1fc1ca308575ef40ab8a57dde9f0cde1` | **yes** |
| L-A close `fb3b929` | `fb3b929432b3de024e510835ff6f9fd4700c2ae1` | **no** |

Branch `research/coefficient-space-laurent-v1` is at `fb3b929`. The
**tag** of the same name was not moved past L-D. This review did not
move it.

`VERDICT.md` §20 says “V5 freeze `7102e8a`. Close update on
`research/coefficient-space-laurent-v1`.” That is the branch, not the
tag.

## 7. No `.env`; no LLM client imports

No `.env` committed (see Checkout).

Under `research/coefficient_laurent/**/*.py` there are **no** imports
of `openai`, `anthropic`, `httpx`, `research.llm_abstraction.client`,
or other LLM HTTP clients.

Two evaluation scripts import **local frozen-task helpers**, not the
API client:

- `atoms/build_map.py` — `parse_flex`, `load_guo_item`
- `eval/guo_v5_rescore.py` — same

`parse_flex` is a SymPy text parser. `load_guo_item` reads
`examples/long/Guo_Sigma_abc_dc_exact.txt` and translates Wolfram
text. Neither module imports `client.py` (`from openai import OpenAI`
lives only in `research/llm_abstraction/client.py`, unused here).
`freeze_v5.py` has `no_llm_calls: True` and no LLM imports.

`tests/test_cl_falsifier.py::test_no_llm_imports_or_calls` bans
`research.llm_abstraction` inside `falsifier/` only; that directory
is clean.

Comments/docstrings saying “No LLM” appear throughout the package.

## Publication E; D2 locked

| source | publication | D2 |
|---|---|---|
| `STATUS.md` | E | LOCKED |
| `VERDICT.md` §12 / §19 | **E** | **No** |
| `TRACK_V5_CLOSED.md` | (edge V_GAIN, not family) | LOCKED |
| `GUO_V5_RESCORE.json` | — | `d2_unlocked=false` |
| `PROGRAM_STATUS_V5.md` | E | LOCKED (file otherwise stale L-D) |
| `PROTOCOL.md` | — | locked until FAMILY_ZERO/NONZERO |

This replay does not unlock D2. FAMILY_ZERO remains 0.

## What this replay does and does not prove

**Proved here (live):** freeze reconstruction byte-identity, freeze
file sha256 (reviewer-side; not pytest-pinned), V4 parent-file pins,
163 package tests, generic suite `false_ZERO=0`, JSON/CSV/MD rescore
internal consistency, D2 still locked on artifacts, no tracked `.env`,
no LLM client imports in the V5 package.

**Not re-executed:** Guo generic→diagonal hops at 40 s (or any other
budget). The L-A census 6 ZERO / 0 NONZERO / 12 UNKNOWN is
**artifact-pinned**, not CI-replayed. The six LEVEL_C ZEROs are the
cheap package-test story plus the committed rescore table, not a
fresh 18-hop engine run.

## Reproducibility gaps (do not block the freeze pin)

1. **No pytest pin of freeze file sha256.** Unlike V3
   `test_ic_integrity_v3.py`, `test_cl_freeze.py` does not assert
   `3d6a5bf2…`. A silent freeze rewrite that kept `n_hops` and
   `primary_hop` would pass.
2. **No pytest pin of `GUO_V5_RESCORE.json`.** Close-track L-A is
   reviewer-side.
3. **Generic-suite tests write `GENERIC_SUITE.json` / `.md`.**
   Deterministic on this checkout; still a historical-JSON write path.
4. **Tag `coefficient-space-laurent-v1` names L-D `ba2a0ce`, not L-A
   `fb3b929`.** Branch and tag disagree.
5. **`REPRODUCIBILITY_V5.md` is missing.** Freeze hash left STATUS.md
   when the L-D/L-A close rewrote that file.
6. **Literature + `PROGRAM_STATUS_V5.md` still say L-D / G0016→G0013
   UNKNOWN.** Close docs in `coefficient_laurent/{STATUS,VERDICT,TRACK_V5_CLOSED}.md`
   are current; the program-status and literature pack were not
   updated on `fb3b929`.

## Verdict

**REPRODUCIBLE** for the freeze (byte-identical rebuild, sha256
`3d6a5bf2ba327b8b8b3f91609f185494ade3b0eeec303175ab7df98c014d16fc`)
and for the cheap `tests/test_cl_*.py` package (163 passed / 1.96 s)
plus generic suite (`false_ZERO=0`).

The Track V5 L-A close statement — hops ZERO=6 NONZERO=0 UNKNOWN=12
case L-A; primary G0016→G0013 LEVEL_C ZERO; FAMILY_ZERO=0;
`d2_unlocked=false`; publication **E** — is consistent with the
committed JSON/CSV/MD and with `STATUS.md` / `VERDICT.md` /
`TRACK_V5_CLOSED.md` on parent `fb3b929`. It is **not** independently
re-certified at 40 s ell-hop scale in this replay.

Track D2 remains locked on these artifacts. No freeze rewrite. No hop
retune. No LLM.
