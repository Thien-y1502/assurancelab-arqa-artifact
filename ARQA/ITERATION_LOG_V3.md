# ARQA v3 iteration log

1. v1 balanced boolean topology exposed parity with domain-majority.
2. v2 heterogeneous fan-out separated ARQA from source-level majority but did
   not break domain-majority parity.
3. v3 adds a preregistered multi-assertion common-cut benchmark. The decision
   rule is not changed to fit the observed result; the benchmark tests the
   previously identified missing mechanism: cross-assertion coherence.
4. The v3 run passed its bounded contract. External adjudication, formal proof,
   and independent-host validation remain required.
