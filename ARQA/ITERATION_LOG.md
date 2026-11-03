# ARQA iteration log

## v1 — balanced topology

The first frozen run used five domains with three sources per domain. ARQA had
zero false PASS in the declared one-domain fault model and full positive-case
coverage, but source-majority and domain-majority also had zero false PASS in
the balanced topology. The result was therefore not sufficient to support a
distinctive Q1 claim.

## v2 — preregistered redesign

The redesign adds a heterogeneous fan-out topology with one correlated domain
publishing 20 sources and four domains publishing one source each. The declared
fault budget remains one compromised domain. This is not a post-hoc removal of
the v1 result; v1 remains archived as `results_v1.json`. The v2 success rule
requires baseline separation on the fan-out stress case.
