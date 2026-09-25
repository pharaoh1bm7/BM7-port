# BM7 — Branch Mobility and Failover Protocol

BM7 is a UDP application-layer protocol for coordinated service ownership and failover between cooperating nodes such as branches, sites, data-center gateways, or service nodes.

BM7 is **not** a Python failover script. The wire protocol is defined independently in `BM7-SPEC.md`; the Python and Go implementations are reference implementations of that specification.

## Protocol goals

- peer discovery / liveness
- service advertisement
- deterministic active-owner election
- failure detection
- controlled failover and recovery
- split-brain mitigation using epochs, leases, sequence numbers and quorum
- replay and duplicate rejection
- authenticated messages with HMAC-SHA-256
- IPv4/IPv6 transport through UDP
- operation across LAN, routed networks and VPN/overlay paths
- implementation-independent binary wire format

## Repository status

This repository is an **implementation and interoperability lab**, not evidence that an IANA assignment has been granted. No BM7 port is assumed to be registered.

During development, choose an administrator-selected local UDP port. Do not treat a Dynamic/Private port as the BM7 service identifier. RFC 6335 states that Dynamic ports (49152–65535) are not assigned and must not be used as service identifiers.

## Quick start

### Python

```bash
python3 reference/python/bm7.py --demo
```

### Tests

```bash
python3 -m unittest discover -s tests -v
```

### Go

```bash
cd reference/go
GO111MODULE=off go test ./...
```

## Experimental deployment

Set an administrator-selected port, for example:

```bash
export BM7_PORT=55000
```

The number above is only a local lab choice; it is not an assigned BM7 port.
