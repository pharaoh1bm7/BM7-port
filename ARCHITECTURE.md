# BM7 Architecture

## 1. Overview

BM7 separates the control plane from the data plane.

The control plane determines:

```
Who owns the service?

Is the primary branch alive?

Which branch should take over?

Is the takeover authorized?

Has state been synchronized?

Can ownership return?
```

The data plane performs:

```
Routing
Forwarding
NAT
Packet processing
Customer traffic handling
```

## 2. Reference Topology

```
                        INTERNET / CORE
                          |
             +------------+------------+
             |            |            |
             v            v            v
         Branch A      Branch B      Branch C
                        PRIMARY       STANDBY
                           |
                     Customer Network
                      10.20.0.0/24
```

BM7 agents communicate between trusted branches.

## 3. Normal Operation

Branch B owns:

```
10.20.0.0/24
```

BM7 state:

```
B = PRIMARY
C = STANDBY
```

C continuously monitors B.

## 4. Failure

If B becomes unavailable:

```
B
X
```

C detects failure.

C must not immediately assume ownership without checking takeover authority.

The logical sequence is:

```
HEARTBEAT FAILURE
       |
       v
   QUORUM CHECK
       |
       v
   EPOCH + 1
       |
       v
  OWNERSHIP CLAIM
       |
       v
     LEASE
       |
       v
  ROUTE ACTIVATION
       |
       v
    SERVING
```

## 5. Recovery

When B returns:

```
B = RETURNING
C = SERVING
```

State is synchronized.

After successful synchronization:

```
B = PRIMARY
C = STANDBY
```

## 6. Control Plane

BM7 controls:

```
Peer health
Ownership
Epoch
Lease
State synchronization
Route ownership
Session ownership
Recovery
```

## 7. Data Plane

The data plane remains independent.

Example:

```
BM7
 |
 +----> FRRouting
 |
 +----> Linux routes
 |
 +----> Conntrack
 |
 +----> NAT
 |
 +----> SD-WAN
```

## 8. Split Brain Protection

Consider:

```
Branch B isolated
Branch C active
Branch A active
```

A and C can establish quorum.

The isolated B cannot independently establish a new ownership generation.

Epochs prevent stale ownership.

Example:

```
B epoch 100
C epoch 101
```

C's epoch supersedes B's old state.

## 9. State Replication

The primary continuously replicates relevant state to standby nodes.

Possible state:

```
Service ID
Network prefix
Service owner
Session metadata
Route metadata
Ownership epoch
```

The reference implementation stores this state in memory.

A production system should use a persistent and transactional state mechanism.

## 10. Failure Domains

BM7 should account for:

```
Node failure
Link failure
Router failure
Power failure
Process failure
Control-plane isolation
```

A network operator must distinguish between:

```
Node failure
```

and:

```
Communication failure
```

because communication loss does not necessarily mean the remote branch has actually failed.

## 11. Production Integration

A production architecture could be:

```
+----------------------+
|      BM7 Agent       |
+----------+-----------+
           |
   +-------+-------+
   |               |
   v               v
Routing          State
Adapter          Adapter
   |               |
   v               v
 FRR            Conntrack
   |
   v
Linux Kernel
   |
   v
Customer Traffic
```

## 12. Design Principle

BM7 is an orchestration protocol.

It should not duplicate functionality already provided by established routing protocols.

Its purpose is to coordinate ownership and continuity across branch boundaries.
