# ARQA v3 Docker reproduction

This file is updated after the v3 archive replay. The v2 Docker result remains
documented in `DOCKER_REPRO_STATUS.md`.

- Image: `assurance-lab-arqa:v3-20261103`
- Image digest: `sha256:66aaaeaa4027d7f615b64c903f6a4094f848e6059d52082afc400bf5521742f5`
- Command: `docker run --rm --network none ... assurance-lab-arqa:v3-20261103`
- Exit code: `0`
- Result: `DOCKER_PASS_BOUNDED_MULTI_ASSERTION`

This confirms container replay of the v3 local harness. It does not establish
enterprise deployment, hardware-root attestation, or independent-host
replication.
