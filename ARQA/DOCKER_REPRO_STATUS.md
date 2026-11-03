# ARQA Docker reproduction

- Image: `assurance-lab-arqa:20261103`
- Image digest: `sha256:82efa7e5a0536b5e24ca48605d2a8f4a7b13189197a57451a13fbdf7728e8708`
- Base image: `python:3.12-slim` (local cached digest)
- Command: `docker run --rm --network none ... assurance-lab-arqa:20261103`
- Exit code: `0`
- Network: disabled
- Result: `DOCKER_PASS_BOUNDED_CONDITIONAL_ARQA`

The domain-majority parity limitation remains unchanged after container replay.
This is not independent-host or enterprise validation.
