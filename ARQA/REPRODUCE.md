# ARQA reproduction

```powershell
python handoff\q1_execution_2026-11-03\ARQA\run_arqa.py
python handoff\q1_execution_2026-11-03\ARQA\run_arqa_v2.py
python handoff\q1_execution_2026-11-03\ARQA\run_arqa_v3.py
```

The first command reproduces the balanced v1 result; the second reproduces the
preregistered fan-out redesign and writes `results.json`/`results_v2.json`.
Docker is recorded as unavailable in the result metadata.
