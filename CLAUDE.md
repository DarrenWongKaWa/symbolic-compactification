# CLAUDE.md

Claude Code adapter. The scientific method is **not** defined here.

Canonical skill:

`skills/symbolic-compactification/SKILL.md`

Install (user scope, from any directory):

```bash
gh skill install DarrenWongKaWa/symbolic-compactification symbolic-compactification --agent claude-code --scope user
```

Alternative (plugin marketplace, after this repo is the catalog):

```text
/plugin marketplace add DarrenWongKaWa/symbolic-compactification
/plugin install symbolic-compactification@symbolic-compactification
```

Then, from an unrelated working directory, ask:

> Audit https://arxiv.org/abs/2604.04520.

Do not duplicate the method. Read the installed skill. LLM judgment is never proof. Promote only on engine `ZERO`. Presentation is not a certificate.

Golden HTML (this repo only): `examples/guo-evidence-ledger/`.
Anan benchmark: `examples/2604.04520/v3/`.
