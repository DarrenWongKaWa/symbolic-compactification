# Engineering Readiness — Context-Grounded Campaign Closure

Decision: **`INTERNAL_ONLY`**

The production verifier and provenance workflow are usable on supported Python
versions, but the repository is not ready to expose the campaign as a
research-preview context-grounded discovery system.

| check | result | evidence |
|---|---|---|
| Clean install | PASS on Python 3.12 | isolated virtual environment installed `.[dev]` and exposed `ssc 0.3.0` |
| Default local interpreter | ENVIRONMENT MISMATCH | system `python3` is 3.9.6; project requires Python 3.10+ as documented |
| Expression input | PASS | medium example returned exact `ZERO`; mutation returned exact `NONZERO` |
| Reproducible run/provenance | PASS | `init-session --json` created a hash-bound run in a fresh temporary workspace |
| Fail-closed behavior | PASS | exact `ZERO`/`NONZERO` and documented `UNKNOWN` semantics are present |
| Typed hypotheses | RESEARCH-ONLY | schemas exist under research packages; no supported public context-hypothesis interface |
| Source provenance | PARTIAL | hash-bound expression/session provenance exists; no public paper/note extraction or curation workflow |
| Paper/note input | PARTIAL | `workspace/input/context/` preserves context files, but no public ingestion/evaluation command exists |
| Secret safety | PASS, targeted | 28 secret/redaction tests passed; tracked scan found only synthetic redacted test fixtures |
| LLM runtime path | NOT READY FOR RELEASE | key handling exists, but the supported clean environment lacks the optional OpenAI-compatible client package and no public context campaign runner is supported |

This decision makes no claim about AI scientific discovery.  It preserves the
engine as an internal, exact symbolic verification and provenance tool.
