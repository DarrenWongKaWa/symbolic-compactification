# Case admission gate

A candidate enters DEV only if all hold:

1. source provenance exists and is public or in-repo frozen;
2. `ScientificAssumptionContract` is complete;
3. every verifier-domain hypothesis is DECLARED or DERIVED;
4. target structure is nontrivial (not CSE, not obvious LGG, not
   notation-leaked);
5. frozen symbolic baselines can run on the source expression;
6. a grounded source catalog can be generated;
7. proposer-visible context has no gold names / target wording.

Rejected cases are **preserved**, not deleted.

Guo is not admitted as DEV/TEST for this line. It may appear only as
a sealed diagnostic after TEST.
