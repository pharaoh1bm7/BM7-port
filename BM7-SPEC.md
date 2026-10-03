# BM7 Protocol Specification v0.2

**Status:** Experimental protocol specification
**Transport:** UDP
**Service Name:** `bm7`
**Requested User Port:** 4707

---

## 1. Scope

BM7 (Branch Mobility and Failover Protocol) is an application-layer UDP protocol for coordinated service ownership, liveness, failure detection, deterministic election, failover, and recovery between independently administered nodes communicating over IP networks.

A primary supported deployment model is communication between nodes located on **different IP networks and administrative domains**, including publicly routed IPv4 and IPv6 networks.

Examples include:

* active/standby service nodes in different cloud providers;
* geographically separated service gateways;
* independent data-center service nodes;
* disaster-recovery nodes located in different networks;
* distributed service endpoints operated by separate network administrators;
* branch or site nodes connected through ordinary routed IP connectivity.

LANs, private routed networks, and VPN/overlay networks are also supported, but they are **not required by the protocol** and are not the defining deployment model.

BM7 does not implement IP routing, NAT, packet forwarding, or application-session migration. It provides a standardized UDP control plane that allows compatible implementations to coordinate service ownership across IP-connected nodes.

---

## 2. Design Objective

The primary interoperability objective of BM7 is to allow independently implemented BM7 nodes to recognize and communicate with the same service using a stable UDP service identifier.

A BM7 implementation MUST NOT require that all participating nodes belong to the same LAN, private address space, VPN, or administrative network.

A conforming implementation MUST support communication using ordinary IPv4 or IPv6 UDP reachability between configured BM7 endpoints.

---

## 3. Terminology

* **Node:** A BM7 endpoint implementing this specification.
* **Peer:** Another BM7 node with which a node is authorized to exchange BM7 messages.
* **Service:** A logical resource whose active ownership is coordinated.
* **Epoch:** Monotonically increasing ownership generation.
* **Sequence:** Per-sender message sequence number.
* **Lease:** Time-limited claim to serve a service.
* **Quorum:** Majority of configured voting peers.
* **Preferred:** Administratively preferred owner.
* **Active:** Node currently holding service ownership.
* **Endpoint:** An IPv4 or IPv6 address and UDP port at which a BM7 node is reachable.

---

## 4. Network Model

BM7 operates at the application layer over UDP.

A BM7 deployment may contain nodes such as:

```text
          Public IP Network / Internet
                    |
        +-----------+-----------+
        |                       |
   +----+----+             +----+----+
   | Node A  |             | Node B  |
   | Cloud 1 |             | Cloud 2 |
   +---------+             +---------+
        |                       |
        +-----------+-----------+
                    |
              Service State
```

Node A and Node B may be located on different networks, providers, autonomous systems, geographic regions, or administrative domains.

The protocol does not assume that the peers share:

* an Ethernet segment;
* a private IP subnet;
* a broadcast domain;
* a VPN;
* an overlay network;
* a common network administrator.

BM7 messages are ordinary UDP datagrams exchanged between reachable endpoints.

---

## 5. Endpoint Requirements

A conforming BM7 deployment MUST provide a reachable UDP endpoint for every participating peer.

An endpoint consists of:

```text
IP address + UDP port
```

The endpoint MAY use:

* a globally routable IPv4 address;
* a globally routable IPv6 address;
* a DNS-resolved address;
* an address reachable through an explicitly configured routed network.

The protocol does not require NAT traversal.

When a node is behind NAT or a stateful firewall, the deployment MUST provide a mechanism that permits the required UDP traffic. Such a mechanism may include port forwarding, a publicly reachable gateway, or another network-level mechanism.

NAT traversal is intentionally outside the BM7 wire protocol.

---

## 6. Transport

* Transport protocol: UDP
* Address families: IPv4 and IPv6
* Default requested service port: UDP/4707
* Reliability: protocol-level timers, sequence numbers, duplicate detection, leases, and retransmission where required
* Authentication: HMAC-SHA-256
* Service identification: stable BM7 service name and assigned UDP port
* Maximum protocol datagram size: implementations SHOULD remain below the IPv4 path MTU to avoid fragmentation

The protocol does not depend on broadcast or multicast.

Unicast communication is the normal BM7 operating mode.

---

## 7. Public-Network Operation

Public-network communication is a normative supported use of BM7.

For example, two independent organizations or cloud environments MAY operate compatible BM7 nodes:

```text
Node A
203.0.113.10:4707
        |
        | UDP
        |
     Internet
        |
        | UDP
        |
198.51.100.20:4707
Node B
```

The nodes use the same BM7 service identifier and wire format regardless of the network on which they are deployed.

The protocol does not change its message format when communicating across the public Internet.

The same protocol therefore supports:

```text
LAN
 |
Routed Network
 |
Public Internet
 |
IPv4 / IPv6
 |
Cloud / Data Center
```

without defining separate protocol variants.

---

## 8. Peer Configuration

BM7 does not require automatic peer discovery.

A peer MAY be configured using:

* a literal IPv4 address;
* a literal IPv6 address;
* a DNS hostname;
* an externally managed service-discovery mechanism.

Once an endpoint is resolved, BM7 uses the same wire protocol for communication.

A configured peer is identified logically by its Node ID rather than by its IP address.

This allows an implementation to change the peer's reachable address without changing the logical identity of the peer.

---

## 9. Binary Wire Format

All integer fields are unsigned and encoded in network byte order (big-endian).

### 9.1 Common Header

| Field              | Size |
| ------------------ | ---: |
| Magic              |    2 |
| Version            |    1 |
| Message Type       |    1 |
| Flags              |    2 |
| Header Length      |    2 |
| Payload Length     |    2 |
| Session ID         |    8 |
| Epoch              |    8 |
| Sequence           |    8 |
| Sender ID          |   16 |
| Lease (ms)         |    4 |
| Authentication Tag |   32 |

Header size: 86 bytes.

Magic is ASCII `B7`.

Version 1 is defined by this specification.

---

## 10. Message Types

| Value | Message   |
| ----: | --------- |
|     1 | HELLO     |
|     2 | ADVERTISE |
|     3 | CLAIM     |
|     4 | ACK       |
|     5 | RELEASE   |
|     6 | ERROR     |

Unknown message types MUST be rejected.

---

## 11. Flags

|    Value | Meaning    |
| -------: | ---------- |
| `0x0001` | ACTIVE     |
| `0x0002` | STANDBY    |
| `0x0004` | RECOVERING |
| `0x0008` | PREEMPT    |
| `0x0010` | QUORUM     |

Unknown non-critical flag bits MAY be ignored.

---

## 12. Payload Format

HELLO, ADVERTISE, CLAIM, ACK and RELEASE use:

| Field        | Size |
| ------------ | ---: |
| Service ID   |   16 |
| Priority     |    4 |
| Network Cost |    4 |
| State        |    1 |
| Reserved     |    3 |

Payload size: 32 bytes.

State values:

| Value | State       |
| ----: | ----------- |
|     0 | INIT        |
|     1 | DISCOVERING |
|     2 | STANDBY     |
|     3 | ACTIVE      |
|     4 | FAILOVER    |
|     5 | RECOVERY    |

ERROR payload is UTF-8 diagnostic text limited to 1024 bytes.

---

## 13. Liveness

Default values:

* HELLO interval: 2 seconds
* Failure threshold: 3 missed intervals
* Nominal failure detection: approximately 6 seconds
* Lease: 10 seconds
* Recovery hold-down: 10 seconds
* Preemption delay: 5 seconds

Implementations MUST make these values configurable.

A BM7 implementation MUST NOT generate unlimited heartbeat traffic.

---

## 14. UDP Traffic and Congestion Control

BM7 uses bounded periodic control traffic.

The default HELLO interval is 2 seconds and implementations MUST provide configurable rate limiting.

Implementations MUST:

1. avoid broadcast storms;
2. avoid uncontrolled retransmission;
3. apply exponential backoff or equivalent bounded retry behavior when repeated messages fail;
4. limit error responses to avoid amplification;
5. avoid responding to unauthenticated packets with large responses;
6. avoid generating more traffic in response to congestion than the configured rate permits.

BM7 does not use UDP as an unbounded bulk-data transport.

BM7 messages are small control-plane datagrams.

---

## 15. Election

Election ordering is deterministic:

1. higher administrative priority wins;
2. lower network cost wins;
3. lexicographically smaller Node ID wins.

A node MAY claim ACTIVE only while quorum exists.

A node observing a valid higher-ranked active owner MUST NOT preempt it unless the owner is considered failed and its lease has expired.

---

## 16. Failover

When the active owner becomes unavailable:

1. surviving peers continue liveness exchange;
2. the failed owner is detected after the configured failure threshold;
3. peers determine whether quorum exists;
4. the winning node increments the ownership epoch;
5. the winning node issues a CLAIM;
6. other peers validate the CLAIM;
7. the winning node becomes ACTIVE.

A CLAIM is valid only when:

* authentication succeeds;
* epoch is valid;
* sequence is fresh;
* the sender is an authorized peer;
* the sender has quorum;
* the lease is non-zero.

---

## 17. Recovery

When a preferred node returns, it enters RECOVERY.

It MUST wait for the configured recovery hold-down and preemption delay.

If it has the preferred election rank, it MAY request ownership using a new epoch.

The current owner MUST NOT relinquish ownership merely because the preferred node has returned.

Ownership changes require a valid BM7 election and epoch transition.

---

## 18. Split-Brain Prevention

BM7 uses:

* majority quorum;
* monotonically increasing epochs;
* authenticated messages;
* per-sender sequence numbers;
* time-limited leases;
* deterministic election;
* replay rejection.

A minority partition MUST NOT claim service ownership when it cannot obtain the required quorum.

---

## 19. Authentication

BM7 version 1 uses HMAC-SHA-256.

The Authentication Tag covers the complete packet except the Authentication Tag field itself.

Implementations MUST authenticate a packet before applying any ownership state change.

Key distribution is outside the BM7 wire protocol and MAY be handled by:

* local configuration;
* an operating-system secret store;
* an external key-management system;
* another authenticated provisioning mechanism.

BM7 does not define a new encryption algorithm.

---

## 20. Replay Protection

Receivers maintain the highest accepted sequence number for each sender/session/epoch context.

Packets that are stale or duplicated MUST NOT cause ownership changes.

Implementations MUST reject replayed CLAIM and RELEASE messages.

---

## 21. Versioning

The Version field identifies the BM7 wire format.

A receiver that does not support a received version MUST reject the message without changing service ownership state.

Future versions MUST preserve the ability of implementations to distinguish incompatible wire formats.

Version-specific behavior MUST NOT require a new UDP service port.

The BM7 service identifier therefore remains version-independent.

---

## 22. IPv4 and IPv6

BM7 contains no IPv4- or IPv6-specific addresses in the protocol header.

The Sender ID is a logical 128-bit identifier.

The same wire format therefore operates over both IPv4 and IPv6.

---

## 23. Failure and Malformed Packet Handling

Implementations MUST reject:

* malformed packets;
* invalid lengths;
* unsupported versions;
* unsupported message types;
* unauthenticated packets;
* unknown peers;
* stale epochs;
* replayed sequences;
* invalid leases.

Malformed UDP datagrams MUST NOT cause an implementation to crash.

Invalid packets MUST NOT modify ownership state.

---

## 24. Interoperability

An implementation is interoperable when it can:

* parse the common header;
* validate packet lengths;
* authenticate packets;
* process all defined message types;
* implement the defined election algorithm;
* enforce quorum;
* enforce lease expiration;
* reject replayed messages;
* operate over IPv4;
* operate over IPv6;
* communicate with an implementation written independently from the reference implementation.

The reference repository contains Python and Go implementations and interoperability test material.

---

## 25. Public Internet Interoperability Requirement

Public-network interoperability is part of BM7 conformance testing.

A complete interoperability test SHOULD include at least two nodes located on different IP networks.

The test MUST verify:

1. UDP reachability;
2. HELLO exchange;
3. authentication;
4. service advertisement;
5. ownership election;
6. failure detection;
7. epoch transition;
8. failover;
9. recovery;
10. replay rejection.

The test environment SHOULD use ordinary routed IP connectivity rather than assuming a shared LAN.

---

## 26. Service Identifier

BM7 is intended to provide a stable service identifier for compatible implementations.

A stable service identifier allows:

* firewall policies to identify BM7 traffic;
* network monitoring systems to classify BM7 traffic;
* service discovery systems to identify BM7 endpoints;
* independently implemented BM7 software to use the same default endpoint;
* operators to deploy compatible implementations without assigning an arbitrary application-specific port to every deployment.

The service identifier is therefore part of interoperability rather than merely an implementation convenience.

---

## 27. Why a Fixed User Port Is Useful

BM7 is a control-plane protocol intended to operate between independently implemented nodes.

Using an administrator-selected port for every deployment would make the service identifier deployment-specific.

A registered UDP service port provides a stable rendezvous point for BM7 implementations and allows network infrastructure to consistently identify BM7 traffic.

The requested port is one UDP service port only.

BM7 does not request multiple ports for separate protocol functions.

The same UDP service carries HELLO, ADVERTISE, CLAIM, ACK, RELEASE and ERROR messages.

---

## 28. Security Considerations

Threats include:

* spoofing;
* replay;
* unauthorized peers;
* packet modification;
* stale ownership claims;
* malicious failover attempts;
* UDP flooding;
* malformed packet attacks.

HMAC-SHA-256 provides message authentication and integrity.

Rate limiting protects the UDP control plane from excessive traffic.

Operators remain responsible for:

* secret management;
* firewall policy;
* endpoint exposure;
* key rotation;
* monitoring;
* denial-of-service protection.

---

## 29. IANA Considerations

This specification requests registration of:

* Service Name: `bm7`
* Transport: UDP
* Requested User Port: 4707

The requested registration is for the BM7 application-layer service.

The requested port is intended to identify the BM7 control-plane service consistently across independent implementations and deployments.

BM7 is not restricted to LAN, intranet, VPN, or private-network operation.

The protocol explicitly supports communication between independently administered nodes across publicly routed IPv4 and IPv6 networks.

The requested port is not used as a security mechanism and does not imply trust.

---

## 30. Experimental Status

BM7 is currently an experimental protocol with an openly published specification and reference implementations.

The protocol is intentionally versioned and implementation-independent.

The project does not claim that UDP/4707 is assigned until an IANA assignment is granted.

Until assignment, implementations MUST NOT represent UDP/4707 as an IANA-assigned BM7 port.

---

## 31. Conformance Summary

A conforming BM7 implementation MUST:

* implement the common header;
* use network byte order;
* validate lengths before parsing;
* authenticate before state changes;
* reject stale and replayed messages;
* implement deterministic election;
* enforce quorum;
* implement leases;
* implement version handling;
* support IPv4;
* support IPv6;
* support ordinary routed UDP connectivity;
* implement rate limiting;
* reject malformed packets safely;
* avoid dependence on LAN, VPN, broadcast or multicast;
* support communication between independently routed endpoints.
