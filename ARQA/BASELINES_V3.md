# ARQA v3 baseline roles

- `source_majority`: per-assertion source vote; ignores correlation and
  assertion coherence.
- `naive_q3`: at least three positive sources for each assertion; ignores
  domain identity.
- `global_domain_majority`: at least three domains positive for any assertion;
  ignores missing or split assertions.
- `per_assertion_domain_majority`: at least three positive domains separately
  for every assertion; this is the strongest simple comparator in v3, and is
  deliberately challenged by the cross-assertion split control.
- `ARQA`: at least three *common* positive domains across all required
  assertions, after freshness and signature verification.

The comparator is still a synthetic rule, not an external implementation of a
production assurance system. A real-data adjudication benchmark remains open.
