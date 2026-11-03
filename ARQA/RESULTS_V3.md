# ARQA v3 multi-assertion results

The v2 result is retained in `results_v2.json`; v3 is a repair experiment, not
a replacement of the earlier negative evidence. The new benchmark requires a
single common set of three domains to support every required assertion
(`availability`, `backup`, and `access`). The `false_split_assertions` control
gives each assertion three positive domains but rotates the supports, so a
per-assertion domain-majority rule passes while no common three-domain cut
exists.

| Method | In-model false PASS | True coverage | Split-assertion false PASS | Out-of-model abstention |
|---|---:|---:|---:|---:|
| ARQA | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Per-assertion domain majority | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| Global domain majority | 0.3333 | 1.0000 | 1.0000 | 1.0000 |
| Source majority | 0.3333 | 1.0000 | 1.0000 | 1.0000 |
| Naive q3 | 0.6667 | 1.0000 | 1.0000 | 0.0000 |

The v3 contract is satisfied. This supports a bounded claim that common-cut
coherence rejects this synthetic cross-assertion split where independent
per-assertion domain majorities accept. It does not prove superiority on real
enterprise evidence, hardware attestation, or arbitrary fault processes.

The result uses five seeds and 5,000 episodes per method. The finite audit
enumerates 32,768 support-state combinations and six declared fault cases.
