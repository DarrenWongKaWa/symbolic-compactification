# Limitations

This tool certifies exact local residuals. It does not certify papers,
novelty, physical models, or undeclared folklore.

`ZERO` means the encoded residual simplified to exact engine `ZERO` under
the recorded route, namespace, and assumptions. A rule certificate is not
engine `ZERO`. `UNKNOWN` never promotes.

## Forward derivation

- The candidate is judged only as written. A nearby identity that was not
  submitted is not certified.
- Substitution identities that are not declared in the workspace (for
  example \(e_{21}=-e_{12}\)) are not silently applied.
- Timeouts, parse failures, and unsupported syntax are `UNKNOWN` or hard
  failures. They are not near-misses.

## Paper audit

- Inventory reads local UTF-8 LaTeX or Markdown. It does not understand
  PDFs or render glyphs.
- LaTeX is not algebra. Files under `expressions/` are researcher
  transcriptions.
- Adjacent equation numbers are not a derivation. Only source-supported
  relations are checked.
- Many scientifically real steps have no supported residual (`NOT_LOWERED`,
  `UNSUPPORTED`, structural). That is an encoding gap, not a proof or a
  refutation.
- `INTEGRAL_ARGUMENT` is not a local residual. Finite Laurent or series
  coefficient `ZERO` is not a remainder proof. An `ASYMPTOTIC_CLAIM` stays
  uncertified without a remainder certificate.
- Brillouin-zone integration by parts is `CERTIFIED_BY_RULE` (local Leibniz
  `ZERO` plus a declared torus rule). SymPy did not evaluate the integral.

## Assumption surface

Certification uses `real: true` symbols, optional `nonzero`, and declared
functions. Positivity, inequalities, excluded poles, parameter identities,
boundaries, symmetries, and limit order are outside the machine-enforced
surface. Writing them in notes does not make them operational.

## Optional proposers

A human, CAS, or model may write a candidate or suggest an audit relation.
None of those sources is a certificate. Core verification needs no API key.
Optional model helpers are disabled under `SSC_PRIVATE_OFFLINE=1`.

## Closed research campaigns

Representation-invention and related discovery campaigns remain closed.
See [history/scientific-experiments-closed.md](history/scientific-experiments-closed.md)
and [research-evidence.md](research-evidence.md).
