# Flagship audit report (operator)

Campaign: GUO_FULL_PAPER_AUDIT_FLAGSHIP_V1
Verdict: FULL_PAPER_AUDIT_DEMONSTRATED

## Identity

- branch: experiment/guo-full-paper-audit-flagship-v1
- RESULTS commit: 351580b725d8e2952f940c72da86eef7ac55820e
- product peel: 783ec64c0bb4ffd0b4b6ad33f33ead96dba49087
- public source: arXiv:2511.16422v2
- main.tex sha256: d2f82d48b19816bffbae22330d89c64f95027c4228c8d6f342036e981079220d
- eprint tar sha256: f074c3045aa17627ddf974895847ed5842e84cbf7b7c755a66700ff2fa01a9e9

## Counts

- numbered equations found (TeX = HTML): 189
- inventoried: 189 / 189
- derivation relations: 146 (plus 1 local Leibniz helper, not a numbered-equation row)
- executable relations: 53 numbered + 1 helper
- EXACT_ZERO: 32
- ZERO_UNDER_SUBSTITUTION: 21
- CERTIFIED_BY_RULE: 11
- UNKNOWN / UNKNOWN_REMAINDER: 17
- STRUCTURAL: 47
- UNSUPPORTED: 18
- NONZERO: 0
- PARSE_FAILURE / COMPILE_FAILURE (final): 0
- false promotion: 0 / 155
- numbering discrepancies: 0

## Regression against public 26-edge Guo evidence (69ad474)

Machine ZERO / CERTIFIED_BY_RULE / UNKNOWN_REMAINDER semantics match the public table.

- (D-59)->(D-60) EXACT_ZERO
- metric-velocity pair -> (D-60) EXACT_ZERO
- (D-60) metric subst ZERO_UNDER_SUBSTITUTION
- (D-60)->(D-61) EXACT_ZERO
- (D-66)->(D-67) ZERO_UNDER_SUBSTITUTION
- (D-61)+(D-67)->(D-68) EXACT_ZERO
- (D-71)->(D-72) EXACT_ZERO
- (D-73) expand EXACT_ZERO; second equality ZERO_UNDER_SUBSTITUTION
- (D-74) EXACT_ZERO; (D-74)->(D-75) ZERO_UNDER_SUBSTITUTION
- (D-70)+(D-76)->(D-77) EXACT_ZERO
- (D-77)->(D-78) ZERO_UNDER_SUBSTITUTION
- (D-114)->(D-119) CERTIFIED_BY_RULE (not engine ZERO)
- (D-119) local EXACT_ZERO
- (D-120)->(D-121) EXACT_ZERO
- (D-123)->(D-124) CERTIFIED_BY_RULE
- (D-122)+(D-124)->(D-125) EXACT_ZERO
- (D-125)->(D-126) ZERO_UNDER_SUBSTITUTION
- (D-126)->(D-127) ZERO_UNDER_SUBSTITUTION
- (D-57) UNKNOWN_REMAINDER
- Leibniz helper EXACT_ZERO
- (B-23)->(B-24) SPLIT / STRUCTURAL
- (B-24)->(B-25) BOOKKEEPING / STRUCTURAL
- (E-128) DEFINITION / STRUCTURAL

The public strength overlay called (D-73) $\epsilon_{12}\epsilon_{21}=-\epsilon_{12}^2$ DIRECT_EXACT because the substitution was already written into the residual file. This table splits that axis: direct NONZERO, conditional ZERO.

## Files

- examples/flagship/guo_full_paper_audit/RESULTS.md
- examples/flagship/guo_full_paper_audit/EQUATION_INVENTORY.yaml
- examples/flagship/guo_full_paper_audit/RELATIONS_FROZEN.yaml
- examples/flagship/guo_full_paper_audit/COVERAGE.json
- examples/flagship/guo_full_paper_audit/PRODUCT_GAPS.md
- examples/flagship/guo_full_paper_audit/REPRODUCE.md
- examples/flagship/guo_full_paper_audit/SOURCE_REVIEW.md
- examples/flagship/guo_full_paper_audit/FLAGSHIP_AUDIT_REPORT.md

src/ was not modified. No tag, no merge, no v0.3 release.
