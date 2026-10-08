# BM7 Public-Network Interoperability Lab

## Purpose

This lab demonstrates BM7 communication between independently routed IP endpoints.

The purpose of this test is to verify that BM7 does not require:

* a shared LAN;
* a shared private subnet;
* a VPN;
* an Ethernet broadcast domain;
* multicast;
* a common administrative network.

The lab uses an administrator-selected temporary UDP port.

The temporary port is NOT an IANA-assigned BM7 service port.

Until IANA approves a BM7 assignment, implementations MUST NOT describe UDP/4707 as assigned.

---

# 1. Required Environment

Use three hosts when testing quorum and failover.

Example:

```text
Node A
Public IPv4: A.A.A.A

Node B
Public IPv4: B.B.B.B

Node C
Public IPv4: C.C.C.C
```

The hosts SHOULD be located on different IP networks.

For the strongest test, use different cloud providers or independent networks.

Example:

```text
Cloud A
    |
    | Internet
    |
Cloud B
    |
    | Internet
    |
Cloud C
```

The nodes must be able to send UDP packets to one another.

Open the temporary UDP test port in the host firewall and cloud security group.

Example test port:

```text
55000/UDP
```

Do not describe this port as an assigned BM7 service port.

---

# 2. Install

On every node:

```bash
git clone https://github.com/pharaoh1bm7/BM7-port.git
cd BM7-port
python3 --version
```

Run the existing local tests:

```bash
python3 -m unittest discover -s tests -v
```

Run the existing protocol demo:

```bash
python3 reference/python/bm7.py --demo
```

---

# 3. Start Node A

Assume:

```text
Node A = A.A.A.A
Node B = B.B.B.B
Node C = C.C.C.C
```

Run on Node A:

```bash
python3 reference/python/bm7_udp.py \
  --node A \
  --bind :: \
  --port 55000 \
  --priority 100 \
  --peer B=B.B.B.B:55000:200 \
  --peer C=C.C.C.C:55000:150
```

---

# 4. Start Node B

Run on Node B:

```bash
python3 reference/python/bm7_udp.py \
  --node B \
  --bind :: \
  --port 55000 \
  --priority 200 \
  --peer A=A.A.A.A:55000:100 \
  --peer C=C.C.C.C:55000:150
```

---

# 5. Start Node C

Run on Node C:

```bash
python3 reference/python/bm7_udp.py \
  --node C \
  --bind :: \
  --port 55000 \
  --priority 150 \
  --peer A=A.A.A.A:55000:100 \
  --peer B=B.B.B.B:55000:200
```

All three nodes should begin showing:

```text
[TX] ...
[RX] ...
```

The received messages should include:

```text
HELLO
ADVERTISE
```

---

# 6. Packet Capture

On one node run:

```bash
sudo tcpdump -ni any udp port 55000 -w bm7-public.pcap
```

Allow the test to run for at least 60 seconds.

Stop tcpdump with:

```text
Ctrl+C
```

Inspect the capture:

```bash
tcpdump -nn -r bm7-public.pcap
```

The capture MUST demonstrate UDP datagrams exchanged between the public IP addresses of the participating nodes.

---

# 7. Authentication Test

All nodes must use the same secret.

For example:

```text
bm7-public-test-secret
```

Run Node A with:

```bash
--secret bm7-public-test-secret
```

Run Node B and C with the same value.

Change the secret on one node.

That node MUST reject packets from the other nodes with an authentication failure.

Expected behavior:

```text
[DROP] ... authentication failure
```

---

# 8. Replay Test

Capture a valid BM7 packet.

Replay the packet toward a running node.

The receiver MUST reject a packet whose epoch and sequence are not newer than the last accepted packet.

Expected behavior:

```text
[DROP] ... replay/duplicate
```

---

# 9. Failure Test

Start all three nodes.

Verify continuous HELLO traffic.

Stop Node B.

Node A and Node C should continue communicating.

The experiment must record:

1. last HELLO received from B;
2. time B became unreachable;
3. continued communication between A and C;
4. resulting service ownership decision.

---

# 10. Quorum Test

With three nodes:

```text
A
B
C
```

a majority is:

```text
2 / 3
```

Therefore A and C can retain quorum when B fails.

A two-node deployment is intentionally insufficient to demonstrate majority-based failover.

---

# 11. Recovery Test

Restart the failed node.

The returning node enters recovery.

The test MUST record:

1. node restart;
2. new HELLO messages;
3. recovery state;
4. ownership decision;
5. epoch transition if ownership changes.

A returning preferred node MUST NOT immediately force ownership without the BM7 election and recovery rules being satisfied.

---

# 12. Evidence Package

Before an IANA resubmission, the repository SHOULD contain:

```text
evidence/
├── bm7-public.pcap
├── interoperability.log
├── authentication-test.log
├── replay-test.log
├── failure-test.log
└── recovery-test.log
```

The evidence SHOULD contain timestamps and the public endpoints used for the test.

Private keys and authentication secrets MUST NOT be committed.

---

# 13. Required Result

The final interoperability report should be able to state:

> Three BM7 nodes were operated on independently routed IP networks. The nodes exchanged authenticated BM7 UDP messages without requiring a shared LAN, VPN, multicast, or broadcast domain. Packet captures demonstrated ordinary UDP communication between the independently routed endpoints.

This statement MUST only be made after the experiment has actually been performed.

---

# 14. IANA Port Status

The laboratory port is temporary.

It does not constitute a BM7 service assignment.

The requested future service is:

```text
Service Name: bm7
Transport: UDP
Desired Port: 4707
```

UDP/4707 MUST NOT be used as an assigned BM7 service identifier until IANA approves the request.
