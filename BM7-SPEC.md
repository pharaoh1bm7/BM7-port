# BM7 Protocol Specification

## 1. Abstract

BM7 is a control-plane protocol designed to coordinate branch-level service continuity in distributed network infrastructures.

BM7 allows a surviving network branch to temporarily assume ownership of services and associated network state from a failed primary branch.

When the original branch recovers, BM7 performs controlled state synchronization and service handback.

BM7 does not replace an underlying routing or forwarding protocol.

## 2. Terminology

### Primary

The branch currently owning a service.

### Standby

A branch prepared to assume service ownership.

### Serving

A branch currently serving a service after takeover.

### Epoch

A monotonically increasing ownership generation.

### Lease

A time-limited authorization to maintain temporary ownership.

### Quorum

The minimum number of trusted nodes required to authorize a takeover.

### Service

A logical customer-facing network service associated with a prefix and state.

## 3. Node Roles

A BM7 node may have one of the following states:

```
PRIMARY
STANDBY
SERVING
RETURNING
ISOLATED
```

## 4. State Machine

Normal operation:

```
PRIMARY
   |
   | primary failure
   v
TAKEOVER
   |
   v
SERVING
   |
   | primary recovery
   v
RETURNING
   |
   | commit
   v
STANDBY
```

The reference implementation represents TAKEOVER as a transition operation rather than a persistent role.

## 5. Ownership Epoch

Every ownership change increments the epoch.

Example:

```
Branch B
epoch = 100
```

After failure:

```
Branch C
epoch = 101
```

An ownership claim with epoch 100 must not override an established ownership state at epoch 101.

Epoch comparison is mandatory for ownership decisions.

## 6. Sequence Numbers

Each BM7 node maintains a monotonically increasing sequence number.

Every outbound control message receives a new sequence number.

Receivers must reject messages that violate the expected anti-replay policy.

## 7. Timestamp

BM7 messages contain a timestamp.

Implementations should reject messages outside an implementation-defined validity window.

The reference implementation uses the timestamp for state tracking while the complete production wire implementation should enforce a strict clock-skew policy.

## 8. Lease

Temporary service ownership is protected by a lease.

Reference value:

```
15 seconds
```

The serving node must renew its lease before expiration.

If the lease expires, the node must no longer claim active temporary ownership.

## 9. Quorum

A takeover must not occur without sufficient authority.

The reference implementation requires at least two available trusted nodes.

Example:

```
A + C available
B failed
```

C may obtain takeover authority.

However:

```
C only
```

is insufficient under the reference quorum policy.

This prevents isolated nodes from independently claiming ownership.

## 10. Message Types

### HELLO

Establishes a BM7 peer relationship.

### HELLO_ACK

Acknowledges HELLO.

### HEARTBEAT

Confirms peer availability.

### HEARTBEAT_ACK

Acknowledges HEARTBEAT.

### STATE_DIGEST

Provides a compact representation of local state.

### STATE_REQUEST

Requests synchronized state.

### STATE_RESPONSE

Returns synchronized state.

### FAILURE_CLAIM

Requests ownership after detecting primary failure.

### FAILURE_CLAIM_ACK

Accepts or rejects the ownership claim.

### ROUTE_CLAIM

Requests ownership of an associated network prefix.

### ROUTE_CLAIM_ACK

Acknowledges route ownership.

### SESSION_CLAIM

Requests ownership of session state.

### SESSION_CLAIM_ACK

Acknowledges session ownership.

### LEASE_RENEW

Renews temporary ownership.

### LEASE_ACK

Acknowledges lease renewal.

### RETURN_PREPARE

Begins controlled return to the original primary.

### RETURN_READY

Confirms that the returning primary has synchronized state.

### RETURN_COMMIT

Commits the ownership handback.

### RETURN_ACK

Confirms successful handback.

### ERROR

Reports a protocol error.

## 11. Logical Message Format

BM7 messages contain:

```
Version
Message Type
Source ID
Destination ID
Epoch
Sequence
Timestamp
Payload Length
Payload
Authentication Tag
```

## 12. Reference Encoding

The reference implementation uses JSON internally.

Example:

```
{
    "v": 1,
    "type": "HEARTBEAT",
    "src": "branch-c",
    "dst": "branch-b",
    "epoch": 101,
    "seq": 42,
    "ts": 1770000000,
    "payload": {}
}
```

The message is authenticated using HMAC-SHA256.

## 13. Network Transport

Reference transport:

```
UDP
```

Development port:

```
4707
```

The port is not considered officially assigned unless an appropriate registry assigns it.

## 14. Failover Procedure

### Step 1

Primary normally owns the service.

### Step 2

Standby monitors the primary using HEARTBEAT.

### Step 3

Heartbeat failure is detected.

### Step 4

The standby verifies that takeover authority exists.

### Step 5

The standby increments its ownership epoch.

### Step 6

The standby claims service ownership.

### Step 7

The underlying data plane is instructed to activate the service route.

### Step 8

The standby becomes SERVING.

## 15. Recovery Procedure

When the original primary returns:

### Step 1

The returning node establishes communication.

### Step 2

Current service state is synchronized.

### Step 3

The serving node enters RETURNING.

### Step 4

The returning node becomes PRIMARY.

### Step 5

The serving node releases temporary ownership.

### Step 6

The serving node becomes STANDBY.

## 16. Data Plane

BM7 does not itself forward customer traffic.

An implementation may integrate with:

* BGP
* FRRouting
* Linux routing
* VRRP
* Stateful NAT
* Conntrack synchronization
* SD-WAN systems

BM7 determines ownership.

The data plane performs forwarding.

## 17. Session Continuity

Changing a route does not automatically preserve arbitrary TCP, UDP, VoIP, or NAT sessions.

A production BM7 deployment therefore requires compatible session-state handling.

Possible mechanisms include:

* Conntrack synchronization
* Stateful NAT replication
* Stable service endpoints
* Application-level session recovery

BM7 must not claim that route failover alone guarantees existing-session continuity.

## 18. Security Requirements

Implementations must provide:

* Peer authentication
* Message integrity
* Replay protection
* Epoch validation
* Sequence validation
* Ownership authorization
* Lease validation

The reference implementation uses HMAC-SHA256.

## 19. Failure Handling

A BM7 node must reject:

* Invalid authentication
* Unsupported protocol versions
* Unknown peers
* Stale epochs
* Expired leases
* Unauthorized ownership claims
* Takeovers without quorum

## 20. Interoperability

Future implementations should publish:

* Protocol version
* Supported message types
* Authentication method
* Supported state synchronization mechanisms
* Data-plane integration method

## 21. IANA Consideration

The project may request:

```
Service Name: bm7
Transport: UDP
Requested Port: 4707
```

The requested port is not guaranteed to be assigned.

## 22. Status

This document describes an experimental research protocol and reference implementation.

It should not be interpreted as an Internet Standard.
