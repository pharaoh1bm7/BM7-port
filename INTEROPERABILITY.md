# BM7 Interoperability

## Goal

BM7 interoperability means that independent implementations can exchange the same versioned UDP wire format and correctly process ownership and liveness information.

The protocol is implementation-independent.

## Reference Implementations

The repository contains:

* Python reference implementation;
* Go packet codec;
* cross-language packet format;
* interoperability tests;
* Wireshark material;
* public-network interoperability runner.

## Required Interoperability Tests

Before an IANA resubmission, the project MUST demonstrate:

1. Python packet generation;
2. Python packet parsing;
3. Go packet parsing;
4. Go packet generation;
5. HMAC-SHA-256 authentication;
6. malformed packet rejection;
7. replay rejection;
8. IPv4 UDP communication;
9. IPv6 UDP communication where available;
10. communication between independently routed networks;
11. failure detection;
12. ownership election;
13. recovery.

## Public-Network Test

The public-network test is documented in:

`PUBLIC-INTERNET-LAB.md`

The test MUST use independently routed endpoints.

The test MUST NOT require:

* a shared Ethernet segment;
* a shared LAN;
* VPN;
* multicast;
* broadcast.

The test SHOULD use three nodes for quorum and failover testing.

## Packet Capture

A packet capture MUST demonstrate actual UDP traffic between the test endpoints.

Example:

```bash
sudo tcpdump -ni any udp port 55000 -w bm7-public.pcap
```

The capture must be generated during an actual interoperability run.

## Security Evidence

The interoperability evidence SHOULD demonstrate:

* successful HMAC validation;
* rejection of incorrect authentication;
* replay rejection;
* malformed packet rejection.

## Failover Evidence

A three-node deployment SHOULD demonstrate:

```text
A + B + C
    |
    | B fails
    v
A + C
    |
    | quorum remains
    v
ownership election
    |
    v
new epoch
    |
    v
CLAIM
```

## IANA Readiness

The project is ready for IANA resubmission only after the public-network experiment has been successfully completed and documented.

The project MUST NOT claim that UDP/4707 is assigned before IANA approval.

The desired registration is:

```text
Service Name: bm7
Transport: UDP
Desired Port: 4707
```
