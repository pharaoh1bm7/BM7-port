# BM7 — Branch Service Continuity

BM7 is an experimental control-plane protocol for branch-level service continuity.

It coordinates temporary service ownership transfer between network branches when a primary branch becomes unavailable, and provides controlled handback when the primary branch recovers.

## Project Status

Experimental / Research Reference Implementation

BM7 is not a replacement for:

* BGP
* OSPF
* IS-IS
* VRRP
* HSRP
* SD-WAN
* Stateful NAT/connection tracking

Instead, BM7 coordinates service ownership and instructs the underlying data-plane mechanisms when ownership should change.

## Core Model

Normal operation:

```
Customer Prefix
      |
      v
   Branch B
   PRIMARY
```

Failure:

```
Customer Prefix
      |
      v
   Branch C
   SERVING
```

Recovery:

```
Branch C
    |
    | state synchronization
    v
Branch B
  PRIMARY

Branch C
  STANDBY
```

## Core Concepts

BM7 uses:

* Heartbeats
* Authenticated control messages
* Sequence numbers
* Ownership epochs
* Temporary leases
* State synchronization
* Quorum protection
* Route ownership coordination
* Controlled return handover

## Example

A customer network is normally owned by Branch B:

```
10.20.0.0/24 -> Branch B
```

If Branch B fails:

```
10.20.0.0/24 -> Branch C
```

When Branch B returns:

```
Branch C -> synchronize state -> Branch B
Branch B -> PRIMARY
Branch C -> STANDBY
```

## Security

The reference implementation uses HMAC-SHA256 for message authentication.

BM7 prevents stale ownership using:

* Epoch numbers
* Sequence numbers
* Timestamps
* Lease expiration
* Quorum validation

Production deployments should use stronger identity and key-management mechanisms such as certificate-based node authentication.

## Development Port

The reference implementation uses:

```
UDP/4707
```

This is a development/test port only.

It is not an IANA-assigned BM7 port unless and until IANA assigns one.

## Repository

The project is intended to contain:

```
BM7/
├── README.md
├── BM7-SPEC.md
├── ARCHITECTURE.md
├── SECURITY.md
│
├── reference/
│   └── bm7_reference.py
│
└── tests/
    └── test_bm7.py
```

## Running the Reference Implementation

Python 3.10+ is recommended.

Run the reference implementation:

```
python reference/bm7_reference.py
```

Run tests:

```
python tests/test_bm7.py
```

No external Python packages are required.

## Important Limitation

The reference implementation validates the BM7 control-plane state machine.

It does not directly manipulate production routing tables, BGP sessions, NAT tables, or customer traffic.

A real deployment requires integration with a data-plane system such as FRRouting, Linux routing, stateful NAT/conntrack synchronization, or an equivalent network platform.

## License

Choose an appropriate open-source license before publishing the repository.
