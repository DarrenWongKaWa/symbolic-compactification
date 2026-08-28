# Owner latent

Consistency of a claimed latent object with operators and member roles.
Not discovery: this package does not invent F, bind catalog members, or
construct Guo masters.

```
latent_compatible(hyp | fields) -> True | False | UNKNOWN
```

Fields: `latent_object`, `operators`, `member_roles` (plus optional
`latent_variables`, `nodes`, `member_ids`, `representation_type`).

Checks: argument compatibility, derivative order, special-function head,
shared vars, multiplicity, recurrence compatibility, role/kind pairing.

`UNKNOWN` is fail-closed. Use `as_bool` before `compose_family_verdict`
because the string `UNKNOWN` is truthy in Python.
