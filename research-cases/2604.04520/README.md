# arXiv:2604.04520 — Anan, Kitamura, Morimoto

Nonreciprocal current induced by dissipation in TR-symmetric systems.

**Canonical output is V3.1** (same V3 statuses, shorter page). Open
[`v3/audit.html`](v3/audit.html) or [`index.html`](index.html).
Markdown twin: [`v3/audit.md`](v3/audit.md).
Evidence model: [`evidence/audit.json`](evidence/audit.json).

```text
input/           TeX + corrected inventory.json
evidence/        canonical audit.json  (do not recertify in the renderer)
v3/              current product: V3.1 five-layer page (V1 colours + V2 claims)
v1/              historical visual-ledger baseline
v2/              historical claim-ledger baseline
comparison/      V1/V2/V3 notes
```

V1 and V2 are regression/reference artifacts. They are not competing
current versions.

Regenerate V3 (does not overwrite V1 or V2):

```bash
python examples/2604.04520/tools/inventory.py
python examples/2604.04520/tools/build_audit.py
python examples/2604.04520/tools/render.py --check
```

Colour grammar (HTML): dark green Exact · hatched Exact if A · blue
structural/cite · orange inspect · dark red ≠0. Numerical support is
orange. Human Accept does not stamp Exact.
