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

Then, from an unrelated working directory, ask to compactify a formula
with declared symbols and domain.

Do not duplicate the method. Read the installed skill. LLM judgment is never proof. Promote only on engine `ZERO`. The model does not write Exact. Presentation is not a certificate.

`examples/` is an optional case library in this repo, not an answer key.
