# AssuranceLab ARQA artifact

Reproducibility repository for the **Assertion-Relation Quorum Assurance
(ARQA)** multi-assertion experiment.

The current package is **v3**. It requires one common quorum of domains to
support every required assertion. The earlier v2 conditional result is
retained in `ARQA/results_v2.json` as negative evidence.

## What is included

- `ARQA/EXPERIMENT_CONTRACT_V3.json` — frozen multi-assertion contract.
- `ARQA/run_arqa_v3.py` — deterministic runner.
- `ARQA/results.json` and `ARQA/results_v3.json` — executed result.
- `ARQA/raw_episodes_v3.jsonl` — generated evidence summaries.
- `ARQA/BASELINES_V3.md`, `ARQA/RESULTS_V3.md`, `ARQA/CLAIMS_V3.md`.
- `ARQA/THEORY_BOUNDARY_V3.md`, `ARQA/REDTEAM_V3.md`.
- `src/assurance_lab/` — source snapshot used by the runner.
- `ARQA/Dockerfile` — container replay for v3.
- `MANIFEST.sha256` — file-integrity manifest.

## Reproduce locally

Python 3.12 is the reference runtime and the runner has no third-party
dependencies.

```bash
python ARQA/run_arqa_v3.py
python -c "import json; print(json.load(open('ARQA/results.json'))['status'])"
```

Expected status: `PASS` with claim state
`BOUNDED_LOCAL_MULTI_ASSERTION_PASS`.

## Reproduce in Docker

```bash
docker build --pull=false -f ARQA/Dockerfile -t assurancelab-arqa-artifact .
docker run --rm --network none assurancelab-arqa-artifact
```

The v3 contract uses five seeds × 1,000 episodes, three assertions and an
exhaustive 32,768-row finite support audit. Docker confirms container replay;
it does not establish hardware-root attestation, enterprise effectiveness or
independent-host replication.

## Scientific boundary

The v3 result shows that common-cut coherence rejects the synthetic
cross-assertion split that per-assertion domain-majority accepts. It does not
prove a general Byzantine theorem, production key custody, cloud reliability,
or Q1 novelty. Read `ARQA/CLAIMS_V3.md` before making claims.

## License and citation

Code and artifact metadata are released under Apache-2.0. Cite the associated
paper only after acceptance; until then, cite the repository commit and
`MANIFEST.sha256`.
