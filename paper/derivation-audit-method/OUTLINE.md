# Paper structure (frozen)

1. Introduction
2. Problem Formulation
3. Threat Model: Why LLM reasoning cannot certify itself
4. Typed Derivation Representation
5. Source-Grounded Obligation Compilation
6. Exact and Rule-Based Certificates
7. Evidence Integrity and Generated Reviewer Tables
8. Implementation
9. Evaluation
    9.1 Synthetic / public demonstrations
    9.2 Adversarial soundness tests
    9.3 Published theoretical-physics field validation
10. Limitations
11. Discussion
12. Conclusion

Appendix:

- schemas
- status semantics
- reproduction details
- additional audit rows

Introduction story: the motivation is **not** “LLMs are smart.” It is that
AI/CAS workflows conflate generated explanation with mathematical
authority, and a reviewer needs a machine-auditable layer that says
exactly which step was checked, under which assumptions, with which
certificate class, and how to reproduce it.
