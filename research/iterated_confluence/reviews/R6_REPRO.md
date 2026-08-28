# Reviewer 6 — Track V3 reproducibility replay

Isolated checkout. No LLM. Did not read other reviewer notes.

## Checkout

| | |
|---|---|
| worktree | `/private/tmp/wt-v3-review-r6` |
| branch | `work/v3-review-r6` |
| parent | `d977db457da2cd50b2b2a72968e8db3bd21d9405` |
| parent subject | Close Track V3: iterated 5-branch hops remain UNKNOWN (I-D). |
| python | `.venv/bin/python` → CPython 3.12.13 |
| sympy | 1.14.0 |
| host | macOS 26.4 arm64 (Darwin 25.4.0) |
| date | 2026-08-28 |

Parent authority SHAs named in the freeze resolve on this repo:

- Track V close `38d6d4a` — *Close Track V: 3 frozen Guo 2-member confluence hyps are ZERO.*
- V2 freeze `4dee916` — *Freeze Track V2: 7 multi-branch/Hermite Guo P2 hyps and family schema.*
- V2 close `fe53ebc` — *Close Track V2: Guo 5-branch families remain FAMILY_UNKNOWN (H-C).*
- V3 freeze `dcfb90c` — *Freeze Track V3 inputs and IteratedConfluenceCertificate schema.*

No `.env` is tracked.

## Replay (live)

```
.venv/bin/python -m pytest tests/test_ic_schema.py tests/test_ic_freeze.py tests/test_ic_integrity_v3.py tests/test_ic_generic_suite.py tests/test_ic_falsifier.py -q
```

**51 passed in 0.70s.** Tree remained clean (the live generic-suite write is byte-stable vs the committed JSON/MD).

| file | collected | role |
|---|---:|---|
| `tests/test_ic_schema.py` | 10 | PATH_ZERO ≠ FAMILY_ZERO; majority forbidden; order-dependent never FAMILY_ZERO |
| `tests/test_ic_freeze.py` | 4 | exactly the 7 V2 families; known ZEROs only s2-i4 G0005→G0004 and G0009→G0008 |
| `tests/test_ic_integrity_v3.py` | 1 | on-disk freeze sha256 + n=7 + `no_llm_calls` |
| `tests/test_ic_generic_suite.py` | 2 | live generic suite + falsifier; false FAMILY_ZERO = 0 |
| `tests/test_ic_falsifier.py` | 34 | 8 named attacks + 2 commuting controls; timeout/majority cannot promote |

## Frozen inputs

`research/iterated_confluence/FROZEN_INPUTS_V3.json`

```
sha256  e1fc6df85b0d293f3251ec87c1827409f402c01752a73251be8899f5b00c41db
```

Matches `EXPECTED_SHA` in `tests/test_ic_integrity_v3.py` and the hash in `REPRODUCIBILITY_V3.md` / `STATUS.md` / `VERDICT.md`.

`freeze_v3.build()` rewritten with the same `json.dumps(..., indent=2) + "\n"` serializer is **byte-identical** to the committed file (same sha256). Parent-file hashes recorded in the blob still match disk:

| recorded field | sha256 | live match |
|---|---|---|
| `v2_freeze_sha256` | `1261bf3b368276bbcb05cc02edd8afb81d0118d625d8bcfb589e658a50a621aa` | yes |
| `v2_graphs_sha256` | `fec3741db5059862204448bfcae5818a11a42a8f64719fa05f5f245e7a941abf` | yes |
| `v2_rescore_sha256` | `622c0e4befbce9461787d5f116a9124d884bdd4fb39c6691bcf54dc4f7351946` | yes |

Freeze payload:

- `n_hypotheses` = 7 = `v2_n_hypotheses`
- `no_llm_calls` = true, `no_new_hypotheses` = true
- `parent_track_v2_close` = `fe53ebc`
- every hypothesis `v2_family_verdict` = `FAMILY_UNKNOWN`
- every `source_sha_match` = true (live re-hash of the four P2 run JSONs)

Family ids (freeze order):

`guo-p2-s0-i3`, `guo-p2-s1-i2`, `guo-p2-s1-i3`, `guo-p2-s2-i2`, `guo-p2-s2-i3`, `guo-p2-s2-i4`, `guo-p2-s4-i1`

Do not confuse the **file** sha256 above with `blob_content_sha256` = `622bd711b44e2ef06a17f500f25f378c37bec2662a70519a602ceee89d7ccd46`. The latter is a hash of `json.dumps(..., sort_keys=True)` of the object without that field; it is internally consistent, but it is not the integrity pin.

## Guo iterated rescore — artifacts only

Full `25s × N` rescore **not rerun**. `EDGE_SECONDS = 25.0` in `eval/guo_iterated_rescore.py`; the committed JSON has 39 covering edges. A live replay would be tens of minutes of process-budgeted `UNKNOWN` timeouts, which this review was instructed not to spend.

Files exist, are git-tracked, and were introduced on the close commit `d977db4`:

| artifact | bytes | sha256 |
|---|---:|---|
| `GUO_ITERATED_RESCORE.json` | 17988 | `b386bae039b39f5430df630279118b2191099e0998b6852fe2c5a7aa4fb99d22` |
| `GUO_ITERATED_RESCORE.csv` | 726 | `bb6119cf90e15b0eefa8d8f5f6af42052aa42d12e70e2c23df88112287fc35bf` |
| `GUO_ITERATED_RESCORE.md` | 658 | `b394fde0a0d1068675489bfafe462152c3df3b28a42af4fe7f714a34556e1888` |

JSON header: `n_families=7`, `FAMILY_ZERO=0`, `FAMILY_NONZERO=0`, `FAMILY_UNKNOWN=7`, `case=I-D`, `edge_seconds=25.0`, `no_llm=true`.

All 7 CSV/JSON family rows are `FAMILY_UNKNOWN`. Freeze `family_ids` == rescore row order. JSON family rows match the CSV on `(family_id, family_verdict, n_members, n_zero_edges, n_unknown_edges)`. Per-family edge tallies match the `edges[]` array (no mismatch).

Edge census (39 unique covering edges):

- `ZERO` 2 — only `guo-p2-s2-i4` `G0005→G0004` and `G0009→G0008`, provenance `check_limit:series`, full/local ops 176/172
- `UNKNOWN` 37 — 36 `timeout` on 5-branch one-parameter hops + 1 substitution `G0005→G0009` (`b↔c`) with provenance `UNKNOWN`
- `NONZERO` 0

That is the documented I-D close: local 5-branch hops stay UNKNOWN; the two reused Track V two-member ZEROs do not promote the 4-member family because composition still sees an UNKNOWN substitution (`require_path_independence=false` on s2-i4, 2 PATH_ZERO paths, family still `FAMILY_UNKNOWN`). Schema tests on this checkout independently forbid that promotion.

## Generic suite (live, cheap)

`research.iterated_confluence.eval.generic_suite.run()` on this checkout equals the committed `GENERIC_SUITE.json` (sha256 `40e63cceb14f7c0c4bdf90f70b2418412ce27b8a14b03be4a2608070cb8fc5d7`):

`n=8`, `n_ok=8`, `false_FAMILY_ZERO=0`, `pass=true`.

Order-dependent `x/(x+y)` is FAMILY_NONZERO. Majority PATH_ZERO+UNKNOWN is FAMILY_UNKNOWN. Spectator `h1` cubic kernel is FAMILY_ZERO.

## What this replay does and does not prove

**Proved here (live):** freeze reconstruction, freeze file pin, V2 parent-file pins, source-run SHA pins, family-composition rules, generic suite, adversarial falsifier. False FAMILY_ZERO = 0 on the cheap suites.

**Not re-executed:** Guo 5-branch one-parameter hops at 25 s (or 90 s). The scientific-scale I-D claim is **artifact-pinned**, not CI-replayed.

## Reproducibility gaps (do not block the freeze pin)

1. **No pytest assertion on `GUO_ITERATED_RESCORE.json`.** `test_ic_integrity_v3.py` pins the freeze file, not the close-track family table. A bit-rot of the rescore JSON would not fail the replay command above. The 7×`FAMILY_UNKNOWN` check in this review is reviewer-side only.

2. **Timeout `UNKNOWN` is budget-machine relative if someone reruns the rescore.** The committed 25 s run is the pin. Docs already record that the 327-op diagonal→triple hop is still UNKNOWN at 90 s; that 90 s run is *not* in the JSON (`edge_seconds` is 25.0 only).

3. **Generic-suite tests write `GENERIC_SUITE.json` / `.md` as a side effect.** Deterministic on this checkout (no dirty tree), but a non-deterministic `check_limit` would rewrite historical run JSON — contrary to the “do not edit historical run JSON” rule in `OWNERS.md`.

4. **Two hashes on the freeze object.** Integrity tests correctly pin the **file** sha256. Downstream text that quotes `blob_content_sha256` is a different function.

## Verdict

**REPRODUCIBLE** for the freeze and for the cheap verifier suites specified in `REPRODUCIBILITY_V3.md`.

The Track V3 close statement “7/7 Guo families FAMILY_UNKNOWN (I-D)” is consistent with the committed JSON/CSV on this parent and with the composition rules that were live-tested. It is **not** independently re-certified at polygamma scale in this replay.

Track D2 remains locked on these artifacts. No freeze rewrite. No Guo gold names. No LLM.
