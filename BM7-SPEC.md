# BM7 Protocol Specification v0.1

**Status:** Experimental protocol specification

## 1. Scope

BM7 (Branch Mobility and Failover Protocol) is an application-layer UDP protocol for a configured group of cooperating peers that coordinate ownership of a service. A BM7 deployment can be used between branches, sites, data-center gateways, cloud gateways, or service nodes.

BM7 transports coordination state; it does not itself implement routing, NAT, packet forwarding, or application-session migration. An implementation may integrate BM7 state with a local routing, firewall, proxy, or service-control mechanism.

## 2. Terminology

- **Peer:** configured BM7 node.
- **Service:** logical resource whose active owner is coordinated.
- **Epoch:** monotonically increasing ownership generation.
- **Sequence:** per-sender message sequence number.
- **Lease:** time-limited claim to serve a service.
- **Quorum:** majority of configured voting peers.
- **Preferred:** administratively preferred owner.
- **Active:** node currently claiming service ownership.

## 3. Architecture

BM7 peers communicate directly over UDP. The path may be a LAN, routed network, IPv4/IPv6 network, or VPN/overlay. NAT traversal is not provided by BM7; deployments must provide reachable UDP endpoints.

## 4. Transport

- Transport: UDP
- Address families: IPv4 and IPv6
- Reliability: protocol-level timers, sequence numbers, duplicate detection and retransmission where required
- Authentication: HMAC-SHA-256 over the complete packet except the Authentication Tag field
- Development port: administrator-selected local port; no fixed dynamic-port number is part of the protocol

## 5. Binary Wire Format

All integer fields are unsigned and encoded in network byte order (big-endian).

### 5.1 Common header

| Field | Size |
|---|---:|
| Magic | 2 |
| Version | 1 |
| Message Type | 1 |
| Flags | 2 |
| Header Length | 2 |
| Payload Length | 2 |
| Session ID | 8 |
| Epoch | 8 |
| Sequence | 8 |
| Sender ID | 16 |
| Lease (ms) | 4 |
| Authentication Tag | 32 |

Header size is 86 bytes.

Magic is ASCII `B7`. Version 1 is defined by this specification.

### 5.2 Message types

| Value | Name |
|---:|---|
| 1 | HELLO |
| 2 | ADVERTISE |
| 3 | CLAIM |
| 4 | ACK |
| 5 | RELEASE |
| 6 | ERROR |

Unknown message types are rejected.

### 5.3 Flags

- `0x0001` ACTIVE
- `0x0002` STANDBY
- `0x0004` RECOVERING
- `0x0008` PREEMPT
- `0x0010` QUORUM

Unknown flag bits are ignored unless a future specification marks them critical.

## 6. Payload Format

The payload uses fixed fields for version 1.

### HELLO / ADVERTISE / CLAIM / ACK / RELEASE

| Field | Size |
|---|---:|
| Service ID | 16 |
| Priority | 4 |
| Network Cost | 4 |
| State | 1 |
| Reserved | 3 |

State values:

- 0 INIT
- 1 DISCOVERING
- 2 STANDBY
- 3 ACTIVE
- 4 FAILOVER
- 5 RECOVERY

Payload length is 32 bytes.

ERROR payload is UTF-8 diagnostic text, limited to 1024 bytes.

## 7. Peer Discovery

BM7 does not require broadcast discovery. A deployment may use configured unicast peers, multicast where available, or an external configuration mechanism. The protocol remains identical after peer addresses are known.

## 8. Hello and Failure Detection

Default values:

- Hello interval: 2 seconds
- Failure threshold: 3 missed intervals
- Nominal failure detection: approximately 6 seconds
- Lease: 10 seconds
- Recovery hold-down: 10 seconds
- Preemption delay: 5 seconds

Implementations MUST make timers configurable.

## 9. Election

Election ordering is deterministic:

1. higher administrative priority wins;
2. lower network cost wins;
3. lexicographically smaller Node ID wins.

A node may claim ACTIVE only while it has quorum. A node observing a valid higher-ranked active owner does not preempt it unless the owner is considered failed and the lease has expired.

## 10. Failover

When the active owner becomes unavailable, surviving peers continue HELLO exchange. After failure detection and when quorum exists, they elect an owner using the deterministic ordering and increment the epoch before issuing a CLAIM.

A CLAIM is valid only when:

- authentication succeeds;
- epoch is not older than the receiver's current epoch;
- sequence is fresh for the sender;
- the sender is a configured peer;
- the sender has quorum;
- the claim's lease is non-zero.

## 11. Recovery

When a preferred node returns, it enters RECOVERY. It must wait for the hold-down and preemption delay. If it has the preferred election rank, it starts a new epoch and requests ownership. The current owner must relinquish only after accepting a higher valid epoch and observing quorum.

## 12. Sequence Numbers and Duplicate Detection

Receivers maintain the highest accepted sequence per sender/session/epoch. Packets with a sequence number at or below the accepted value are rejected as duplicates or replay attempts.

## 13. Split-Brain Prevention

BM7 uses several independent safeguards:

- majority quorum;
- monotonically increasing epochs;
- authenticated messages;
- per-sender sequence numbers;
- time-limited leases;
- deterministic tie-breaking.

A deployment with two isolated groups that cannot obtain a majority MUST NOT allow either minority group to claim ownership.

## 14. Authentication

BM7 v1 uses HMAC-SHA-256. Key distribution is outside the protocol and MUST be handled by deployment configuration or an external key-management system.

The protocol does not define a new encryption algorithm.

## 15. Error Handling

Malformed packets, invalid lengths, unsupported versions, invalid message types, unauthenticated packets, unknown peers, stale epochs and replayed sequences are rejected without changing service ownership state.

Implementations MUST NOT crash on malformed UDP datagrams.

## 16. IPv4 / IPv6

The protocol has no IP-address fields in the wire header. Sender identity is a logical 128-bit Node ID, so the same packet format works over IPv4 and IPv6.

## 17. NAT / VPN Considerations

BM7 is suitable for routed and VPN overlays. It does not perform NAT traversal. Peers must have bidirectional UDP reachability or an overlay that supplies it. Deployments behind stateful NATs should ensure the configured Hello interval keeps the mapping alive.

## 18. Security Considerations

Threats include spoofing, replay, unauthorized peers, packet modification, flooding and stale ownership claims. HMAC provides message authentication and integrity but not confidentiality. Rate limiting and operational key rotation are deployment responsibilities.

## 19. Interoperability

An implementation is interoperable when it can parse, validate, authenticate, generate and act on the version-1 wire format without implementation-specific extensions. The repository contains Python and Go implementations plus cross-language test vectors.

## 20. IANA Considerations

This experimental document does not claim an IANA-assigned port.

A future request for a User Port would need to justify a stable service identifier and explain why an administrator-selected/dynamic port is not sufficient, consistent with RFC 6335. Dynamic ports (49152–65535) are not assignable and must not be treated as a permanent service identifier.

Requested future service name: `bm7`
Transport: UDP
Reference: a stable published specification to be supplied only if the registration is pursued.

## 21. Interoperability and Conformance Requirements

A conforming implementation MUST:

- implement the common header exactly;
- use network byte order;
- validate lengths before parsing;
- authenticate before applying state changes;
- reject stale/replayed messages;
- implement the defined election ordering;
- enforce quorum before ACTIVE claims;
- implement lease expiry;
- avoid accepting malformed packets as valid control messages.
