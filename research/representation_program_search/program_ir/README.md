# M1 executable Program IR

This module is the typed constructor for `RepresentationGrammarV1`. It is not
a search algorithm and not a verifier. Its only successful lifecycle status is
`COMPILED`: a compiled obligation still has to be submitted to the exact
verifier, which alone may return `ZERO`, `NONZERO`, or `UNKNOWN`.

## Native schema

An M1-native program contains:

- exact `source_members` (`member_id`, package-relative `.txt` path, raw-byte
  SHA-256);
- typed `latent_objects` with ordered bound parameters and parser-dialect
  symbolic cores;
- first-class `node_structures`, including repeated labels;
- ordered operators with `operator_id`, grammar operator, `latent_id`, explicit
  `inputs`, explicit `output`, and typed `arguments`;
- member assignments with an explicit compiled `output`;
- assumption ids plus their `DECLARED` or `DERIVED` statuses;
- obligations with explicit source `member_id` and compiled `output`;
- instance maps and unexplained member ids.

Operator inputs name earlier **outputs**, not operator ids. Output names must be
unique and may not alias an operator id. This makes intermediates and the final
reconstruction graph explicit instead of inferring “the last operator.”

The immutable dataclasses are in `model.py`. `schema.program_from_dict` is the
strict JSON constructor. Unknown program fields, operator aliases, unknown
arguments, missing links, bad types, invalid sources, and hash mismatches fail
closed.

## Canonical identity

`canonical_program_hash()` computes SHA-256 over compact, sorted-key JSON with
`allow_nan=False`. It excludes the `program_id` field itself. Bound latent
parameters are alpha-normalized globally to `z0`, `z1`, ... in latent bind
order. Only scoped mathematical parameter fields are renamed. Source member
ids, paths, hashes, external node/value expressions, and source bytes are never
alpha-renamed.

No score, timestamp, token log, LLM response, or reasoning field is part of the
typed object, so those values cannot alter canonical program identity.

## Operator construction semantics

All construction uses strict parser expressions and ordinary exact SymPy
constructors. The module never calls global `simplify()`, `equals()`, numeric
comparison, or the verifier.

| operator | executable arguments |
|---|---|
| `VALUE` | `node` for one bound parameter, or complete `values` map |
| `SUBSTITUTE` | `parameter`, `value`; zero or one input |
| `DERIVATIVE` | `variable`, optional positive integer `order`; zero or one input |
| `SHIFT` | `variable`, `delta`; zero or one input |
| `PERMUTE` | simultaneous external-symbol `mapping`; exactly one input |
| `NEWTON_DD` | `nodes` id; at least two structurally distinct labels |
| `HERMITE_DD` | `nodes` id; at least one repeated, contiguously grouped label |
| `RECURRENCE` | `parameter`, `base`, `step`, and `form` (`FORWARD_DIFFERENCE` or `SHIFTED_VALUE`) |
| `LINEAR_COMBINATION` | one coefficient per input, optional `constant` |
| `BASIS_PROJECT` | one coefficient input multiplied by explicit `basis`, optional scalar `coefficient` |
| `BASIS_RECONSTRUCT` | one coefficient per basis-term input, optional `constant` |
| `COMPOSE` | one input per bound parameter of the outer latent |

The Hermite constructor uses confluent divided differences: an all-equal
subrange becomes the corresponding derivative divided by a factorial. It does
not take a limit or ask a CAS to rediscover multiplicity. `NEWTON_DD` rejects
any repeated label, and `HERMITE_DD` rejects a distinct-only node structure.

Grammar ablations are hard validation gates:

- `G_FULL`: all V1 operators;
- `G_NO_HERMITE`: rejects `HERMITE_DD` but retains repeated node objects;
- `G_PRIMITIVE`: exactly the frozen primitive operator subset.

## Compilation result

`compile_program(program, context)` always returns a `CompilationResult`.
Exceptional paths become `COMPILE_FAILURE` with a stable failure code. On
success it emits exact current source text/hash plus a constructed candidate
expression for each required obligation. It emits no verdict field and does
not certify equivalence.

The IR-level tautology detector flags independent `VALUE` wrappers whose
latents are exact copies of individual source members and have no shared latent
or nontrivial operator. The flag is diagnostic; it cannot create success.

## RPSCasePackageV1 compatibility

`load_case_package()` validates the complete artifact manifest and exact member
hashes, then injects source references and assumption statuses only from their
authoritative package files. It does not infer executable links.

The thermal packages committed before M1 omit:

1. operator `output` names;
2. member-assignment `output` names;
3. obligation-to-output links;
4. M1 alpha-normalized program ids.

The loader reports those exact `schema_deltas`. Their reference programs are
therefore inspectable but return `COMPILE_FAILURE` beginning with
`OPERATOR_OUTPUT_MISSING`; reconstruction filenames or operator ordering are
never used to guess the missing graph.
