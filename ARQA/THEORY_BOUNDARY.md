# ARQA theory boundary

The runner executes signed HMAC envelopes and finite support/cut-set checks. It
does not prove Byzantine agreement, trusted hardware attestation, or cross-host
independence. The intended theorem still needs:

1. an explicit fault-domain hypergraph and admissible compromised-set family;
2. safety proof for PASS under the declared family;
3. liveness proof under availability/freshness assumptions;
4. a multi-assertion benchmark where domain-majority parity is broken;
5. independent implementation of the cut-set checker.
