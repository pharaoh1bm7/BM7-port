# IANA Considerations

No IANA assignment is assumed by this repository.

The project currently uses an administrator-selected experimental UDP port. The repository must not describe any Dynamic/Private port as the BM7 service port.

RFC 6335 distinguishes User Ports (1024–49151), which can be assigned by IANA, from Dynamic/Private Ports (49152–65535), which are not assigned. A future User Port request therefore needs a concrete service-identifier justification rather than merely choosing a convenient number.

Potential future registry request:

- Service Name: bm7
- Transport Protocol: UDP
- Description: BM7 Branch Mobility and Failover Protocol — authenticated peer coordination for service ownership, failure detection, deterministic election, failover and recovery.
- Port Number: To be assigned
