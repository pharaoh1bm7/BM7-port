# BM7 Protocol Specification v1

## 1. Abstract

BM7 (Branch Mobility and Failover Protocol) is an application-layer UDP control protocol for coordinating service ownership, liveness, deterministic election, failure detection, failover, and recovery between independently administered nodes.

BM7 is designed to operate over ordinary routed IP networks, including communication between endpoints located on different networks and administrative domains.

A shared LAN, private subnet, VPN, overlay network, broadcast domain, or multicast domain is not required.

LAN and VPN deployments are supported as deployment environments, but they are not protocol requirements.

BM7 does not perform IP routing, packet forwarding, NAT traversal, or application-session migration.

---

## 2. Terminology

**Node**
A BM7 protocol endpoint.

**Peer**
An authorized BM7 node with which a node exchanges protocol messages.

**Service**
A logical service whose active ownership is coordinated by BM7.

**Epoch**
A monotonically increasing ownership generation.

**Sequence**
A monotonically increasing message sequence number maintained by a node.

**Lease**
A time-limited ownership validity interval.

**Quorum**
The minimum number of configured voting nodes required to authorize ownership.

**Active Owner**
The node currently holding service ownership.

---

## 3. Node States

BM7 defines the following states:

```text
INIT
DISCOVERING
STANDBY
ACTIVE
FAILOVER
RECOVERY
```

---

## 4. Ownership State Machine

Normal operation:

```text
INIT
  |
  v
DISCOVERING
  |
  v
STANDBY
  |
  | active owner failure
  v
FAILOVER
  |
  | quorum + election
  v
ACTIVE
  |
  | owner recovery
  v
RECOVERY
  |
  | controlled handback
  v
STANDBY
```

A node MUST NOT enter ACTIVE ownership unless the quorum and election rules permit the transition.

---

## 5. Ownership Epoch

Every ownership transition creates a new epoch.

An implementation MUST NOT accept an ownership claim from an older epoch when a newer ownership epoch is already known.

Epoch values are unsigned 64-bit integers.

An implementation MUST reject an ownership claim whose epoch is lower than the locally accepted ownership epoch.

---

## 6. Sequence Numbers

Every transmitted BM7 packet contains a 64-bit sequence number.

The sender MUST monotonically increase its sequence number for each transmitted packet.

For a given sender and epoch, a receiver MUST reject a packet whose sequence number is less than or equal to the highest accepted sequence number.

This provides duplicate and replay protection at the protocol layer.

---

## 7. Lease

ACTIVE ownership is time-limited.

The default lease is:

```text
10 seconds
```

The default HELLO interval is:

```text
2 seconds
```

The default failure threshold is:

```text
3 missed HELLO intervals
```

Implementations MUST allow these values to be configured.

A node MUST NOT continue claiming ACTIVE ownership after its lease has expired unless it has successfully renewed or re-established valid ownership according to the protocol rules.

---

## 8. Quorum

For N configured voting nodes:

```text
quorum = floor(N / 2) + 1
```

A node MUST have quorum before issuing a CLAIM.

For three configured nodes:

```text
A + B + C

quorum = 2
```

Therefore:

```text
A + C
```

may continue an election when B is unavailable.

A single isolated node MUST NOT claim ownership when quorum cannot be established.

---

## 9. Message Types

BM7 v1 defines six message types.

| Value | Name      | Purpose                     |
| ----: | --------- | --------------------------- |
|     1 | HELLO     | Liveness                    |
|     2 | ADVERTISE | Service/state advertisement |
|     3 | CLAIM     | Ownership claim             |
|     4 | ACK       | Acknowledgement             |
|     5 | RELEASE   | Ownership release           |
|     6 | ERROR     | Protocol error              |

Unknown message types MUST be rejected.

---

## 10. Wire Format

BM7 uses a fixed binary header followed by a fixed 32-byte payload.

All integer values are encoded in network byte order (big-endian).

### Header

```text
Offset  Size  Field
0       2     Magic
2       1     Version
3       1     Message Type
4       2     Flags
6       2     Header Length
8       2     Payload Length
10      8     Session ID
18      8     Epoch
26      8     Sequence
34      16    Sender ID
50      4     Lease (milliseconds)
54      32    Authentication Tag
```

Total header size:

```text
86 bytes
```

### Payload

```text
Offset  Size  Field
0       16    Service ID
16      4     Priority
20      4     Network Cost
24      1     State
25      7     Reserved (MUST be zero on transmit, ignored on receipt)
```

Total payload size:

```text
32 bytes
```

Therefore a normal BM7 packet is:

```text
86 + 32 = 118 bytes
```

---

## 11. Magic and Version

Magic:

```text
ASCII "B7"
```

Version:

```text
1
```

A receiver MUST reject packets with an unsupported version.

A future wire-format version remains distinguishable through the Version field.

---

## 12. Flags

|    Value | Meaning    |
| -------: | ---------- |
| `0x0001` | ACTIVE     |
| `0x0002` | STANDBY    |
| `0x0004` | RECOVERING |
| `0x0008` | PREEMPT    |
| `0x0010` | QUORUM     |

A BM7 v1 receiver MUST reject a packet that has any flag bit set other than those defined above. New flags require a new Version value.

---

## 13. Service and Node Identification

`Service ID` is a 128-bit identifier representing the logical service being coordinated.

`Sender ID` is a 128-bit logical identifier for the BM7 node.

Neither identifier is an IP address.

This allows a node's network address to change without changing its logical BM7 identity.

---

## 14. Network Transport

BM7 uses UDP.

Supported address families:

```text
IPv4
IPv6
```

BM7 does not require:

* broadcast;
* multicast;
* Ethernet adjacency;
* private addressing;
* VPN;
* overlay networking.

A BM7 peer may be reached using an IPv4 address, IPv6 address, or DNS-resolved endpoint.

The protocol uses ordinary UDP unicast communication.

---

## 15. Public-Network Operation

Public routed operation is a supported BM7 deployment model.

Example:

```text
+-------------+                     +-------------+
| BM7 Node A  |                     | BM7 Node B  |
| Network A   |                     | Network B   |
+------+------+                     +------+------+
       |                                    |
       | UDP                                 | UDP
       +------------- Internet --------------+
```

The nodes may be located in different:

* networks;
* data centers;
* cloud providers;
* geographic regions;
* administrative domains.

BM7 does not change its wire format when operating across these networks.

Network-layer access control, firewall rules, NAT configuration, and routing remain deployment responsibilities.

---

## 16. Authentication

Every BM7 packet is authenticated using HMAC-SHA-256.

The Authentication Tag covers:

```text
Header with Authentication Tag zeroed
+
Payload
```

A receiver MUST verify authentication before applying any ownership state change.

Invalid authentication MUST result in packet rejection.

---

## 17. Failure Detection

Nodes periodically transmit HELLO messages.

Default:

```text
HELLO interval = 2 seconds
failure threshold = 3 intervals
```

A peer is considered unavailable when no valid authenticated HELLO or other accepted BM7 message has been received within the configured failure interval.

Implementations MUST avoid unlimited retransmission.

---

## 18. Election

Election ordering is deterministic:

1. higher Priority wins;
2. lower Network Cost wins;
3. lower Sender ID wins.

The same election inputs MUST produce the same winner on all participating nodes.

A node MUST NOT claim ownership if another eligible node has a valid active lease and has higher election priority.

---

## 19. Failover

After detecting owner failure:

1. the node verifies quorum;
2. the node verifies that the previous owner's lease is no longer valid;
3. the node calculates the deterministic election winner;
4. the winner increments its epoch;
5. the winner transmits CLAIM;
6. peers validate the CLAIM;
7. the winner enters ACTIVE state.

---

## 20. Recovery

A returning node enters RECOVERY.

It MUST NOT immediately override an active owner.

The returning node waits for the configured recovery/preemption policy.

If the election rules permit a new ownership transition, the node creates a new epoch and performs a normal BM7 CLAIM.

---

## 21. Split-Brain Protection

BM7 uses:

* quorum;
* monotonically increasing epochs;
* sequence numbers;
* leases;
* deterministic election;
* authenticated messages.

A minority partition MUST NOT claim ownership without quorum.

A stale or replayed CLAIM MUST NOT change ownership state.

---

## 22. UDP Traffic Requirements

BM7 is a control-plane protocol.

Normal traffic consists of small UDP datagrams.

Implementations MUST:

* bound periodic traffic;
* avoid broadcast storms;
* avoid unlimited retries;
* rate-limit generated ERROR messages;
* avoid amplification;
* reject malformed packets without generating large responses.

The default HELLO rate is one packet every two seconds per configured peer.

---

## 23. Security Considerations

BM7 protects against:

* forged packets;
* packet modification;
* replayed packets;
* stale ownership claims;
* unauthorized peers;
* malformed protocol input.

HMAC-SHA-256 provides message authentication and integrity.

Sequence numbers and epochs provide replay/staleness protection.

Operators remain responsible for secret distribution, rotation, firewall policy, endpoint exposure, and denial-of-service protection.

---

## 24. Interoperability

An implementation is BM7 v1 interoperable when it can:

* encode the defined binary format;
* decode the defined binary format;
* authenticate packets;
* reject invalid packets;
* implement the six defined message types;
* implement epoch validation;
* implement sequence validation;
* implement lease handling;
* implement quorum;
* implement deterministic election;
* operate over IPv4;
* operate over IPv6.

Independent implementations MUST be able to exchange packets without depending on implementation-specific JSON or internal data structures.

---

## 25. Port Selection

BM7 implementations MUST allow the UDP port to be configured.

Until a default port is registered, operators MUST select an administrator-controlled UDP port and document it for all peers. A port in the Dynamic/Private range (for example 55000/UDP) is acceptable for laboratory use but is not recommended for long-lived deployments, because it can collide with ephemeral port allocation.

No port is assigned to BM7. A development port MUST NOT be represented as an assigned BM7 service.

---

## 26. IANA Considerations

This document requests registration of:

```text
Service Name: bm7
Transport Protocol: UDP
Requested Port: 4707
```

The purpose is to provide a default port for independently written implementations and for network operators writing policy. Registration is not required for BM7 to function in a coordinated deployment; the port is configurable (section 25).

See `IANA-CONSIDERATIONS.md` for the justification and `INTEROPERABILITY.md` for the evidence required before the request is submitted.

---

## 27. Status

BM7 version 1 is a stable specification. Its wire format and protocol rules will not change incompatibly within version 1; incompatible changes require a new Version value.

This document does not claim that UDP/4707 has been assigned.

The project must not represent 4707 as an assigned IANA port until the registry assignment has been granted.
