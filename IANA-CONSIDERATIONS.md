# IANA Considerations

## Requested Assignment

BM7 requests a User Port assignment in the IANA Service Name and Transport Protocol Port Number Registry.

| Field              | Requested Value |
| ------------------ | --------------- |
| Service Name       | `bm7`           |
| Transport Protocol | UDP             |
| Requested Port     | 4707            |
| Reference          | `BM7-SPEC.md`   |
| Assignee           | Belal Eladawy   |

## Service Description

BM7 is an application-layer UDP service for authenticated coordination of service ownership between independently administered nodes.

BM7 provides:

* peer liveness;
* service advertisement;
* deterministic ownership election;
* failure detection;
* failover;
* recovery;
* epoch and lease management;
* replay protection;
* authenticated control messages.

BM7 is designed to operate between nodes on different IP networks, including publicly routed IPv4 and IPv6 networks.

LAN, VPN and private-network deployments are supported but are not required.

## Why UDP

BM7 is a lightweight control-plane protocol.

Its messages are small, independently authenticated datagrams containing state, sequence, epoch and lease information.

The protocol does not require a byte-stream transport.

UDP allows BM7 to operate with explicit application-level liveness and lease timers.

BM7 does not use UDP for bulk data transfer.

## Why a Registered Port Is Required

BM7 is intended for interoperability between independently implemented nodes.

A stable service port provides a consistent service identifier for:

* compatible implementations;
* firewall policy;
* network monitoring;
* service classification;
* service discovery;
* cross-vendor interoperability.

An administrator-selected port would make the service identifier deployment-specific and would prevent a stable default endpoint from being used by independent BM7 implementations.

BM7 uses a single UDP service port for all protocol messages.

## Public Network Use

BM7 is not restricted to intranets, LANs or VPNs.

A conforming deployment may consist of nodes located in:

* different cloud providers;
* different data centers;
* different autonomous networks;
* different geographic regions;
* different administrative domains.

The protocol operates using ordinary routed UDP connectivity over IPv4 or IPv6.

## Security

BM7 uses HMAC-SHA-256 for message authentication and integrity.

Replay protection, sequence validation, epochs and leases prevent stale or replayed ownership messages from changing service state.

Malformed and unauthenticated packets are rejected without changing ownership state.

## UDP Traffic Control

BM7 uses bounded periodic control traffic.

Implementations use configurable heartbeat intervals, failure thresholds and retry behavior.

Implementations MUST rate-limit generated traffic and MUST NOT create unbounded responses to incoming UDP packets.

BM7 does not use broadcast or multicast as a requirement.

## Versioning

The BM7 wire header contains a Version field.

Unsupported versions are rejected without modifying ownership state.

Future protocol versions retain the same stable service identifier and do not require a separate port merely because the wire format version changes.

## Development Status

BM7 is an openly published experimental protocol with reference implementations in Python and Go and interoperability test material.

The protocol specification is maintained independently of the implementations.

The project does not claim that UDP/4707 is assigned until IANA completes the registration process.

## Requested Registry Entry

**Service Name:** bm7
**Port Number:** 4707
**Transport Protocol:** UDP
**Description:** BM7 authenticated service ownership coordination and failover
**Reference:** BM7-SPEC.md
