# ARQA bounded local results

## Current result: v3 multi-assertion repair

The current `results.json` is the v3 run. It passes the preregistered
multi-assertion common-cut contract (`BOUNDED_LOCAL_MULTI_ASSERTION_PASS`). See
`RESULTS_V3.md`, `EXPERIMENT_CONTRACT_V3.json`, and `CLAIMS_V3.md` for the
current claim boundary. The v2 result remains retained in `results_v2.json` as
negative evidence.

The balanced v1 run is retained in `results_v1.json`. It showed that a simple
domain-majority baseline can already match ARQA on a balanced boolean task.
This prevented an unsupported superiority claim.

The preregistered v2 redesign added a heterogeneous fan-out topology
`[20,1,1,1,1]` and retained the balanced topology.

| Method | In-model false PASS | True PASS coverage | Fan-out false PASS | Out-of-model abstention |
|---|---:|---:|---:|---:|
| ARQA | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Source majority | 0.5000 | 1.0000 | 1.0000 | 1.0000 |
| Naive q3 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| Dempster-like | 0.5000 | 1.0000 | 1.0000 | 1.0000 |
| Domain majority | 0.0000 | 1.0000 | 0.0000 | 1.0000 |

## Interpretation

ARQA passes the bounded safety/coverage contract and separates from source-level
majority/fusion under fan-out correlation. However, `domain_majority` has the
same result on this boolean task. The scientific status is therefore
`CONDITIONAL_PASS`, not a superiority claim. A Q1 paper requires a richer
multi-assertion/cut-set benchmark where the proof certificate contributes
information beyond a hand-written domain-majority rule.
