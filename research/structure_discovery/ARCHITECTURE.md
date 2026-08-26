# Method v3 architecture (structure discovery)

Experimental. Engine 0.3.0 semantics unchanged. Not merged into the stable package.

```
                 Expression E  +  declared context C
                              ↓
                 Structural observations (facts only)
                              ↓
                 Structure Hypothesis Agent  →  H1, H2, …
                              ↓
                 Candidate Constructor  →  R(E,H)
                              ↓
                 Verifier  ZERO | NONZERO | UNKNOWN
                              ↓
                 certified scientific representation
                 (state changes only on ZERO)
```

One discoverer, one constructor. No ensemble.

Discoverer does not emit a complete expression as truth.
Constructor does not decide truth.
Verifier does not search for abstractions.

Named auxiliaries are hypotheses. Success requires a gold-matching type
and/or a ZERO reconstruction. A name for the whole of E is not discovery.
