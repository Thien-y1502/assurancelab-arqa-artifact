# ARQA execution status

The current `results.json` is the v3 multi-assertion repair and has bounded
status `PASS`. The v2 conditional result is preserved separately and remains
part of the audit trail.

The local runner uses signed HMAC envelopes and an explicit five-domain
correlation topology. The finite cut audit is an implementation boundary check;
it is not a Byzantine theorem and does not establish cross-host independence.
