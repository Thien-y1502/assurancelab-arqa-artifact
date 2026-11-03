# ARQA v3 reviewer red-team

- **Construct validity:** the split-assertion control is generated from a
  known support grammar; external adjudicated evidence could behave
  differently.
- **Baseline validity:** per-assertion domain majority is stronger than the v2
  comparator, but it is still a hand-written baseline and not a published
  production system.
- **Theory:** the finite support audit checks the implemented common-cut rule;
  it is not a general Byzantine or independence theorem.
- **Threat model:** one-domain compromise, two-domain out-of-model failure,
  fan-out correlation, signature tamper, missing assertion, and split
  assertion support are explicit. Replay, stale timestamps, and cross-host
  key custody remain open.
- **Novelty:** v3 repairs the exposed parity limitation; novelty is still
  `NOT_PROVEN` until a literature-level method comparison and independently
  adjudicated multi-assertion benchmark are completed.
- **Deployment:** local HMAC signatures are not hardware roots of trust; Docker
  replay is not enterprise validation.
