# ARQA reviewer red-team

- **Novelty:** remote-attestation transport and TEE interoperability are prior
  art; the claim must stay at business-level decision safety.
- **Theory:** domain-majority parity is a real limitation; no superiority claim
  is permitted until a multi-assertion cut-set benchmark breaks the parity.
- **Threat model:** one compromised domain, correlated fan-out, replay,
  freshness and signature tamper are explicit; stronger attacks are open.
- **Experiment:** local HMAC signatures do not establish hardware roots of trust
  or cross-host independence.
- **Release:** Docker and independent-host validation are open.
