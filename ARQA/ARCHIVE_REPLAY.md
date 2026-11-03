# Final archive replay

- Archive: `assurancelab_ARQA_Q1_execution_2026-11-03.zip`
- Clean extraction: passed; manifest verification: passed.
- Local replay from the extracted archive: exit code `0`, status
  `CONDITIONAL_PASS`.
- Docker replay from the extracted archive: image tag `assurance-lab-arqa:final3`,
  `--network none`, exit code `0`, status `CONDITIONAL_PASS`.

The domain-majority parity limitation remains. This is bounded harness
reproducibility only; it is not independent-host or enterprise validation.
