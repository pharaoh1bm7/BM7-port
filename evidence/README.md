# BM7 — Protocol Evidence

This section provides reproducible laboratory evidence for the BM7 protocol, including packet integrity, deterministic election, lease handling, epoch progression, active-role advertisement, and preferred-return preemption.

---

## 1. Protocol Validation Summary

```text
BM7 demo OK
HEADER_LEN=86
PAYLOAD_LEN=32
PACKET_LEN=118
quorum=OK
deterministic-election=OK
epoch=OK
lease=OK
HMAC=OK
replay-protection=OK
active-lease-advertisement=OK
stable-election=OK
preferred-return-preemption=OK
```

### Verified properties

| Property                    | Result      |
| --------------------------- | ----------- |
| Packet construction         | `118 bytes` |
| Quorum                      | `OK`        |
| Deterministic election      | `OK`        |
| Epoch handling              | `OK`        |
| Lease handling              | `OK`        |
| HMAC authentication         | `OK`        |
| Replay protection           | `OK`        |
| Active lease advertisement  | `OK`        |
| Stable election             | `OK`        |
| Preferred-return preemption | `OK`        |

---

# 2. Node A — BM7 Startup and Observation

### Command

```bash
python3 lab/udp_node.py --node A
```

### Startup

```text
[START] Node A priority=100 UDP/55001
BM7 node listening on UDP/55001
Packet size: 118 bytes
```

### Initial discovery

```text
[RX] ('::1', 55002, 0, 0) HELLO epoch=0 seq=1
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=0 seq=2

[RX] ('::1', 55003, 0, 0) HELLO epoch=0 seq=1
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=0 seq=2
```

### Epoch 1

```text
[RX] ('::1', 55002, 0, 0) CLAIM epoch=1 seq=7
[RX] ('::1', 55002, 0, 0) HELLO epoch=1 seq=8
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=1 seq=9
```

**Transition:** `epoch 0 → epoch 1`

---

### Epoch 2

```text
[RX] ('::1', 55003, 0, 0) CLAIM epoch=2 seq=33
[RX] ('::1', 55003, 0, 0) HELLO epoch=2 seq=34
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=2 seq=35
```

**Transition:** `epoch 1 → epoch 2`

---

### Epoch 3

```text
[RX] ('::1', 55002, 0, 0) CLAIM epoch=3 seq=9
[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=50
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=51
```

**Transition:** `epoch 2 → epoch 3`

---

# 3. Node B — Initial Active Election

### Command

```bash
python3 lab/udp_node.py --node B
```

### Startup

```text
[START] Node B priority=200 UDP/55002
BM7 node listening on UDP/55002
Packet size: 118 bytes
```

### Neighbor discovery

```text
[RX] ('::1', 55003, 0, 0) HELLO epoch=0 seq=1
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=0 seq=2

[RX] ('::1', 55001, 0, 0) HELLO epoch=0 seq=3
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=0 seq=4
```

### Active election

```text
[STATE] local node became ACTIVE epoch=1
```

> **TRANSITION — B becomes ACTIVE**

B has the highest configured priority:

```text
Node B priority = 200
Node C priority = 150
Node A priority = 100
```

The election therefore establishes B as the active node.

---

# 4. Node B — Stable Operation

After becoming active, B continues receiving HELLO and ADVERTISE messages from the other nodes.

```text
[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=7
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=8

[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=7
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=8

[RX] ('::1', 55001, 0, 0) HELLO epoch=1 seq=9
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=1 seq=10

[RX] ('::1', 55003, 0, 0) HELLO epoch=1 seq=9
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=1 seq=10
```

**Result:** BM7 remains in a stable active/standby state while heartbeats and advertisements continue.

---

# 5. Node C — Election and Takeover

### Command

```bash
python3 lab/udp_node.py --node C
```

### Startup

```text
[START] Node C priority=150 UDP/55003
BM7 node listening on UDP/55003
Packet size: 118 bytes
```

### Initial communication

```text
[RX] ('::1', 55001, 0, 0) HELLO epoch=0 seq=3
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=0 seq=4

[RX] ('::1', 55002, 0, 0) HELLO epoch=0 seq=3
[RX] ('::1', 55002, 0, 0) ADVERTISE epoch=0 seq=4
```

### Election progression

```text
[RX] ('::1', 55002, 0, 0) CLAIM epoch=1 seq=7
```

C continues receiving advertisements and monitoring the active state.

### Takeover

```text
[STATE] local node became ACTIVE epoch=2
```

> **TRANSITION — C becomes ACTIVE**

This demonstrates the BM7 active-role transition to C under the tested failure/election scenario.

---

# 6. Epoch Progression

The captured traffic demonstrates monotonically increasing epochs:

```text
epoch=0
   ↓
epoch=1
   ↓
epoch=2
   ↓
epoch=3
```

Observed claims include:

```text
CLAIM epoch=1
CLAIM epoch=2
CLAIM epoch=3
```

> **Purpose:** The epoch provides a monotonically advancing generation identifier for ownership transitions and prevents stale leadership information from being treated as current.

---

# 7. Node B — Recovery and Preferred Return

### Command

```bash
python3 lab/udp_node.py --node B
```

### Recovery observation

```text
[START] Node B priority=200 UDP/55002
BM7 node listening on UDP/55002
Packet size: 118 bytes
```

B observes the current epoch and advertisements:

```text
[RX] ('::1', 55001, 0, 0) HELLO epoch=2 seq=43
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=2 seq=44

[RX] ('::1', 55003, 0, 0) HELLO epoch=2 seq=44
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=2 seq=45
```

### Preferred-return transition

```text
[STATE] local node PREEMPTED owner epoch=3
```

> **TRANSITION — Preferred-return / preemption**

The returning higher-priority owner does not simply create a competing active state. Instead, BM7 performs the defined preemption transition.

---

# 8. Final Stable State

The protocol continues exchanging HELLO and ADVERTISE messages after the transition:

```text
[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=49
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=50

[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=50
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=51

[RX] ('::1', 55001, 0, 0) HELLO epoch=3 seq=51
[RX] ('::1', 55001, 0, 0) ADVERTISE epoch=3 seq=52

[RX] ('::1', 55003, 0, 0) HELLO epoch=3 seq=52
[RX] ('::1', 55003, 0, 0) ADVERTISE epoch=3 seq=53
```

The protocol validation reports:

```text
stable-election=OK
preferred-return-preemption=OK
```

---

# 9. End-to-End BM7 Transition

The complete tested state progression is:

```text
B ACTIVE
    │
    │ failure / ownership loss
    ▼
C ACTIVE
    │
    │ B recovery
    ▼
B PREEMPTED OWNER
    │
    │ preferred-return handling
    ▼
Stable BM7 election state
```

### Core protocol properties demonstrated

```text
✓ Deterministic election
✓ Quorum validation
✓ Epoch-based ownership progression
✓ Lease handling
✓ Active lease advertisement
✓ HMAC authentication
✓ Replay protection
✓ Stable election
✓ Preferred-return preemption
```

---

# 10. Evidence Conclusion

The captured BM7 laboratory output demonstrates that the implementation is not limited to a static UDP message exchange. The test exercises stateful node coordination, ownership election, epoch progression, active-state advertisement, lease handling, authentication, replay protection, and preferred-return behavior.

The implementation was tested using three BM7 nodes with different priorities:

```text
Node A → priority 100 → UDP/55001
Node B → priority 200 → UDP/55002
Node C → priority 150 → UDP/55003
```

The protocol validation concludes:

```text
BM7 demo OK
quorum=OK
deterministic-election=OK
epoch=OK
lease=OK
HMAC=OK
replay-protection=OK
active-lease-advertisement=OK
stable-election=OK
preferred-return-preemption=OK
```
