# arXiv:2604.04520 — Anan, Kitamura, Morimoto

Nonreciprocal current induced by dissipation in TR-symmetric systems.

V1 is the conservative equation-ledger baseline. V2 is a claim-map audit
of the same paper. V1 is not overwritten.

```text
input/           TeX + corrected inventory.json
evidence/        canonical audit.json
v1/              frozen V1 HTML + Markdown
v2/              claim-map HTML + Markdown
```

Regenerate V2 (does not touch V1):

```bash
python examples/2604.04520/tools/inventory.py
python examples/2604.04520/tools/build_audit.py
python examples/2604.04520/tools/render.py --check
```

Open `v2/audit.html`. Compare with `V1_V2_COMPARISON.md`.
