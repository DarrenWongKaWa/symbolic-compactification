# Admission audit contract

This directory is the independent J-B admission audit for the 39 newly mined,
non-skeptic Representation Program Search dossiers. It does not select a
benchmark partition and does not change a dossier, grammar, search policy,
parser, verifier, manifest, or `STATUS.md`.

Run:

```bash
PYTHONPATH=src:. python3 \
  research/representation_program_search/audits/admission/audit.py --check
```

`audit.py --write` deterministically regenerates `ADMISSION_AUDIT.json` and
`ADMISSION_AUDIT.md`. The JSON records every dossier hash and the hash of the
bounded human review policy in `reviews.json`.

## Fail-closed admission statuses

The statuses are mutually exclusive, with this precedence:

1. `REJECT`: non-scientific/trivial/nonexact target, or another hard admission
   failure that repackaging cannot cure.
2. `PROBLEM_UNDERSPECIFIED`: a verifier-domain assumption is missing or labeled
   `NOT_DECLARED`. This is not a proof gap.
3. `DUPLICATE_REVIEW`: a historical or intra-new structural overlap must be
   adjudicated before partition selection.
4. `PACKAGING_GAP`: the scientific case may be useful, but exact machine
   members/obligations/source evidence are absent or the frozen parser cannot
   represent the required obligation.
5. `ADMISSION_CANDIDATE`: all preceding gates pass. This is still not
   `PROGRAM_SUCCESS` and does not assign DEV/TEST/CHALLENGE.

An `expression_sketch` is prose/context, even when it contains a short formula.
It is never passed to the verifier. An explicit `admission_package` must contain
at least two member files, at least one obligation file, and a symbols file;
every file is read directly with `load_expression()` under the frozen parser.

## Independent axes

The audit retains axes that primary-status precedence could otherwise hide:

- citation presence versus a frozen source artifact;
- absence of a fabrication signal (not source authentication);
- assumption-contract structure and manual verifier-domain gaps;
- proposed-depth plausibility;
- direct parser fit, fixed-instance-only fit, or no frozen-parser route;
- historical/intra-new duplicate references;
- exactness/nontriviality hard rejects.

`REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` is not permission to claim a
symbolic-dimension proof. It is a possible future fixed-task packaging route.
Declaring a special function as an undefined function may make syntax parse but
does not supply exact special-function semantics to the verifier.
