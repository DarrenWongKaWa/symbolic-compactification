# Research notes

This example is the frozen `thermal-10-polygamma-order2-recurrence` proof-gap
diagnostic repackaged for field use. The source-stated recurrence is submitted
to exactly the same verifier path as the other demos. The expected result is
`UNKNOWN`, so no scientific state may be promoted.

The mathematical source excludes the polygamma pole set
`z = 0, -1, -2, ...`. The v0.1 assumptions file records `z` as real and
nonzero, but cannot encode an excluded discrete set. This limitation is
visible rather than silently repaired. Even with a fuller external domain
statement, the current exact route does not certify this special-function
recurrence.

`UNKNOWN` is not partial confirmation, likely truth, or likely falsity. It is
a proof gap and a successful demonstration of fail-closed behavior.
