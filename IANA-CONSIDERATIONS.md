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

## Why a Registered Port Is Requested

This section responds directly to the reviewer's objections.

### "The port can be documented and coordinated per deployment"

That is true for a closed deployment, and BM7 supports it (the port is configurable). The request is not about whether *one* operator can pick a port; it is about the following cases, where per-deployment coordination does not work:

1. **Independent implementations.** BM7 is specified so that separately written implementations interoperate (see `INTEROPERABILITY.md`). Without a common default, every pair of implementations needs out-of-band agreement before a first packet can be exchanged.
2. **No safe unregistered choice.** The only ports that need no registration are the Dynamic/Private ports (49152-65535). RFC 6335 reserves that range for ephemeral client use, so a fixed *listening* service there can collide with the local ephemeral allocator of any host, and with other services that made the same informal choice. The Python lab default (55000) has exactly this weakness.
3. **Middlebox and operator policy.** Peers on different administrative domains need to write firewall and monitoring rules for a stable, identifiable service. A per-deployment port forces those rules to be rewritten for every peering.
4. **Collision avoidance.** A registry entry gives other protocol designers a way to learn that the port is taken.

We acknowledge that none of these makes registration *necessary* for a single private deployment. They are the reason for a default value, not a claim that BM7 cannot run without one.

### "The protocol is still experimental"

BM7 v1 is now declared stable by its author: the v1 wire format and rules are frozen, and incompatible changes require a new Version value. The project does not claim that this is an IETF-reviewed standard, or that there is a second independent implementation yet. The status, the evidence collected so far, and the specific criteria that must be met before resubmission are listed in `INTEROPERABILITY.md` ("Registration Readiness"). Until those criteria are met, the project recommends that anyone running BM7 use an administrator-selected port, as described in `BM7-SPEC.md` section 25.

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

BM7 v1 is an openly published, stable specification with Python and Go implementations.

Evidence that exists today (raw output in `lab/results/local-interop-run.txt`):

* Python unit tests for encoding, HMAC, replay, epoch, quorum and election;
* Python <-> Go cross-language wire-format test with shared test vectors (`tests/interop/run.sh`).

Evidence still missing from the repository:

* published raw logs and packet capture of the maintainer's multi-host test (to be added under `evidence/`);
* IPv6 results;
* a second, independently developed implementation;
* any production or long-term deployment report.

The project does not claim that UDP/4707 is assigned until IANA completes the registration process, and it does not claim the missing evidence above.

## Requested Registry Entry

**Service Name:** bm7
**Port Number:** 4707
**Transport Protocol:** UDP
**Description:** BM7 authenticated service ownership coordination and failover
**Reference:** BM7-SPEC.md
