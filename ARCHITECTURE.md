# BM7 Architecture

BM7 is an application-layer coordination protocol operating over ordinary UDP/IP connectivity.

```text
             Routed IP Networks / Internet

        +-----------------------------+
        |                             |
   +----+----+                   +----+----+
   | Node A  |                   | Node B  |
   | Network |<------ UDP ------>| Network |
   |    A    |                   |    B    |
   +---------+                   +---------+
        |                             |
        |             UDP             |
        +--------------+--------------+
                       |
                  +----+----+
                  | Node C  |
                  | Network |
                  |    C    |
                  +---------+
```

The participating nodes do not need to share:

* a LAN;
* a subnet;
* a broadcast domain;
* a VPN;
* an overlay;
* a private address space.

LAN, VPN and private routed deployments remain possible, but they are deployment choices rather than protocol requirements.

## Protocol Layers

```text
+----------------------------------+
| Service / Application             |
+----------------------------------+
| BM7 Ownership & Failover Control |
+----------------------------------+
| UDP                              |
+----------------------------------+
| IPv4 / IPv6                      |
+----------------------------------+
```

## BM7 Responsibilities

BM7 provides:

1. peer liveness;
2. service advertisement;
3. authentication;
4. replay protection;
5. deterministic election;
6. quorum;
7. ownership epochs;
8. leases;
9. failover;
10. recovery.

## Outside BM7

BM7 does not provide:

* IP routing;
* NAT traversal;
* packet forwarding;
* application data transport;
* arbitrary TCP session migration.

A deployment may integrate BM7 ownership state with routing, firewall, proxy, NAT, gateway, or application-service mechanisms.

## Transport

BM7 uses UDP unicast.

The protocol does not require broadcast or multicast.

During development, a temporary administrator-selected UDP port is used.

The requested IANA service is:

```text
Service Name: bm7
Transport: UDP
Requested Port: 4707
```

UDP/4707 must not be represented as assigned until IANA grants the assignment.
