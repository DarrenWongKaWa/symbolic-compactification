# Table — Forward Mode gating (RQ1)

Public, frozen evidence only. Proposer is human (Mode A demos) or scripted
(`test_proposer_protocol.py`). Not a live-LLM discovery score.

| Candidate | Source | Engine result | Scientific state |
|---|---|---|---|
| \((x+1)^2\) vs \(x^2+2x+1\) | Mode A `demo_a_zero`; session CASE B | `ZERO` | admissible; may promote |
| \((x+1)^2+1\) (mutated) | external Mode A replay | `NONZERO` (residual \(-1\), counterexample \(x=-2\)) | rejected; sources unchanged |
| polygamma recurrence gap | Mode A `demo_c_unknown` | `UNKNOWN` | recorded; not promoted |
| \(x^2+2x-1\) vs \(x^2+2x+1\) | scripted proposer CASE B | `NONZERO` | current unchanged; later correct candidate may still promote |
| Proposal/HYPOTHESIS record | session protocol | not a certificate | cannot promote even if later ZERO arrives |

Newton divided-difference demo B is a second ZERO illustration of a
researcher-supplied instance. It is not a search or discovery result.
