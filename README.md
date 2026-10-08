# BM7 — Branch Mobility and Failover Protocol

BM7 is a stable (v1) UDP application-layer protocol for coordinated service ownership, failure detection, deterministic election, failover and recovery between independently administered nodes.

## Important

BM7 is designed to operate across IP networks.

A BM7 deployment does **not** require:

* the same LAN;
* the same private subnet;
* a VPN;
* an overlay network;
* broadcast;
* multicast;
* a shared administrative network.

BM7 can operate between independently routed IPv4 and IPv6 endpoints, including nodes located in different data centers, cloud providers, geographic regions and administrative domains.

## What BM7 Does

BM7 provides a standardized control plane for deciding which node owns a logical service.

The protocol provides:

* peer liveness;
* service advertisement;
* deterministic owner election;
* failure detection;
* controlled failover;
* recovery;
* leases;
* epochs;
* quorum;
* sequence numbers;
* replay protection;
* HMAC-SHA-256 authentication;
* IPv4 and IPv6 support;
* implementation-independent binary wire format.

BM7 does not perform IP routing, NAT traversal, packet forwarding or application-session migration.

Instead, an implementation may use the BM7 ownership state to control a local service, gateway, proxy, routing policy or other service-management mechanism.

## Public Network Example

A BM7 deployment may look like:

```text
       Public IP Network
              |
      +-------+-------+
      |               |
+-----+-----+   +-----+-----+
| BM7 Node A|   | BM7 Node B|
| Cloud A   |   | Cloud B   |
+-----------+   +-----------+
      |               |
      +-------+-------+
              |
       Coordinated Service
```

The two nodes may be located on completely different IP networks.

They communicate using ordinary UDP.

## Protocol

The complete wire protocol is defined in:

* `BM7-SPEC.md`

Architecture:

* `ARCHITECTURE.md`

Interoperability:

* `INTEROPERABILITY.md`

IANA considerations:

* `IANA-CONSIDERATIONS.md`

Security:

* `SECURITY.md`

## Message Types

BM7 currently defines:

| Message   | Purpose                     |
| --------- | --------------------------- |
| HELLO     | Peer liveness               |
| ADVERTISE | Service state advertisement |
| CLAIM     | Ownership claim             |
| ACK       | Acknowledgement             |
| RELEASE   | Ownership release           |
| ERROR     | Protocol error              |

All ownership-changing messages are authenticated.

## Failover Model

A simplified BM7 ownership transition is:

```text
        ACTIVE
           |
       peer failure
           |
       detection
           |
        QUORUM?
        /     \
      NO       YES
      |         |
   STANDBY    ELECTION
                |
              CLAIM
                |
              ACTIVE
```

Ownership changes use epochs, leases, sequence numbers and quorum to reduce split-brain conditions.

## Transport

BM7 uses UDP.

The requested IANA service is:

```text
Service Name: bm7
Transport: UDP
Requested Port: 4707
```

UDP/4707 is **not currently an assigned IANA port**.

The project must not describe UDP/4707 as assigned until IANA approves the request.

## Why a Default Port Is Requested

BM7 is intended to be interoperable between independently implemented software.

A stable service port allows network operators and implementations to identify BM7 traffic consistently.

It also provides a common default endpoint for compatible implementations instead of requiring every deployment to invent a different application-specific port.

BM7 uses one service port for all protocol messages.

## Security

BM7 uses HMAC-SHA-256 for authentication and integrity.

The protocol also provides:

* sequence validation;
* replay rejection;
* epoch validation;
* lease expiration;
* quorum requirements;
* deterministic election;
* malformed-packet rejection.

Operators remain responsible for key management and network-level filtering.

## Development Status

BM7 v1 is declared stable by its author. The wire format and protocol rules in `BM7-SPEC.md` are frozen for version 1; incompatible changes require a new Version value.

The repository contains reference implementations and interoperability material.

| Area | Status |
| ---- | ------ |
| Wire format (Python and Go, shared test vectors) | Tested, `tests/interop/run.sh` |
| Node logic (election, quorum, leases) | Python only, unit-tested on loopback |
| Public-network / multi-host test | Performed by the maintainer; raw logs and packet capture to be added under `evidence/` |
| IPv6 | Not documented yet |
| Independent second implementation | Not yet available (Python and Go implementations are by the same author) |

See `INTEROPERABILITY.md` ("Registration Readiness") for what is required before a port request is resubmitted.

The protocol specification is independent of the implementation language.

The project is intended to demonstrate a real interoperable application-layer UDP protocol rather than a single-host failover script.

## Repository Structure

```text
BM7-port/
├── BM7-SPEC.md
├── ARCHITECTURE.md
├── IANA-CONSIDERATIONS.md
├── INTEROPERABILITY.md
├── SECURITY.md
├── reference/
├── tests/
├── lab/
└── wireshark/
```

## License

MIT
