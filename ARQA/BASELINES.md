# ARQA baseline roles

The current run is v3; the v2 baseline table and parity finding are retained
in `results_v2.json`. The v3 comparator definitions are in `BASELINES_V3.md`.

- `source_majority`: counts individual source votes and ignores correlation.
- `naive_q3`: accepts three positive sources regardless of domain.
- `domain_majority`: counts positive trust domains; strong boolean comparator.
- `dempster_like`: source-level weighted evidence fraction.
- `ARQA`: signed/fresh evidence plus distinct-domain quorum.

The domain-majority parity is retained as a blocking limitation for any claim of
algorithmic superiority.
