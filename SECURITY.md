# BM7 Security Model

## 1. Security Objective

BM7 controls service ownership.

Therefore, unauthorized BM7 messages could potentially cause:

* Route takeover
* Service interruption
* Traffic redirection
* State corruption
* Split brain
* Denial of service

Security is therefore a core protocol requirement.

## 2. Threat Model

BM7 assumes that the network may contain:

* Malicious packets
* Replay attempts
* Spoofed node identities
* Compromised peers
* Packet modification
* Packet injection
* Delayed messages
* Network partitions

## 3. Authentication

The reference implementation uses:

```
HMAC-SHA256
```

Each trusted node shares a secret with the BM7 trust domain.

The message authentication code covers the canonical message.

Invalid MACs are rejected.

## 4. Node Identity

Every BM7 node has a unique logical identifier.

Example:

```
branch-a
branch-b
branch-c
```

Production implementations should bind node identity to cryptographic credentials.

Recommended future model:

```
Node ID
   |
   v
Certificate
   |
   v
Public Key
   |
   v
Authenticated BM7 peer
```

## 5. Replay Protection

BM7 uses:

* Epoch
* Sequence number
* Timestamp

An attacker should not be able to capture:

```
FAILURE_CLAIM
```

and replay it later.

The receiving node must validate the message freshness and ownership epoch.

## 6. Epoch Security

Epoch is the ownership generation.

Example:

```
Epoch 100
   |
   v
Primary fails
   |
   v
Epoch 101
```

A message attempting to restore epoch 100 ownership after epoch 101 has been established must be rejected.

## 7. Lease Security

Temporary ownership expires.

Reference lease:

```
15 seconds
```

The serving node must renew the lease.

An expired lease invalidates temporary ownership.

## 8. Quorum

A node must not be able to take over a service merely because it cannot reach the primary.

This distinction is critical:

```
"I cannot reach B"
```

does not necessarily mean:

```
"B is dead."
```

Therefore BM7 requires an authority/quorum mechanism before ownership transfer.

## 9. Split Brain

Split brain occurs when two nodes believe they own the same service.

BM7 mitigates this through:

```
Quorum
  +
Epoch
  +
Lease
  +
Ownership validation
```

These mechanisms must be implemented together.

## 10. Key Management

The reference implementation uses a shared secret for simplicity.

Production deployments should provide:

* Secure key storage
* Key rotation
* Per-node credentials
* Credential revocation
* Certificate validation
* Protection against key extraction

## 11. Denial of Service

BM7 messages are control-plane traffic.

Implementations should enforce:

* Rate limiting
* Maximum message size
* Maximum outstanding requests
* Bounded retransmission
* Peer allowlists
* Authentication before expensive processing

BM7 must not allow unauthenticated peers to consume unlimited resources.

## 12. Transport Security

UDP does not provide authentication or encryption.

BM7 therefore provides authentication at the protocol layer.

Future implementations may use:

* DTLS
* QUIC
* Another authenticated secure transport

Any transport change must preserve the BM7 security model.

## 13. Confidentiality

The reference implementation provides integrity and authentication.

It does not provide payload confidentiality.

If customer-sensitive metadata is transmitted, production deployments should use encryption.

## 14. Compromised Node

If a trusted BM7 node is compromised, cryptographic authentication alone is insufficient.

The deployment must support:

```
Node revocation
Credential rotation
Ownership quarantine
Operator intervention
```

## 15. Security Limitations

This reference implementation is not production-grade security software.

It is intended to demonstrate protocol behavior.

Before production use, the implementation requires:

* Independent security review
* Fuzz testing
* Packet parser hardening
* Key-management design
* Formal threat analysis
* Interoperability testing
* Fault injection

## 16. Security Principle

BM7 should fail closed.

If ownership cannot be authenticated or authorized, the node should not claim service ownership.
# BM7 Security Model

## 1. Security Objective

BM7 controls service ownership.

Therefore, unauthorized BM7 messages could potentially cause:

* Route takeover
* Service interruption
* Traffic redirection
* State corruption
* Split brain
* Denial of service

Security is therefore a core protocol requirement.

## 2. Threat Model

BM7 assumes that the network may contain:

* Malicious packets
* Replay attempts
* Spoofed node identities
* Compromised peers
* Packet modification
* Packet injection
* Delayed messages
* Network partitions

## 3. Authentication

The reference implementation uses:

```
HMAC-SHA256
```

Each trusted node shares a secret with the BM7 trust domain.

The message authentication code covers the canonical message.

Invalid MACs are rejected.

## 4. Node Identity

Every BM7 node has a unique logical identifier.

Example:

```
branch-a
branch-b
branch-c
```

Production implementations should bind node identity to cryptographic credentials.

Recommended future model:

```
Node ID
   |
   v
Certificate
   |
   v
Public Key
   |
   v
Authenticated BM7 peer
```

## 5. Replay Protection

BM7 uses:

* Epoch
* Sequence number
* Timestamp

An attacker should not be able to capture:

```
FAILURE_CLAIM
```

and replay it later.

The receiving node must validate the message freshness and ownership epoch.

## 6. Epoch Security

Epoch is the ownership generation.

Example:

```
Epoch 100
   |
   v
Primary fails
   |
   v
Epoch 101
```

A message attempting to restore epoch 100 ownership after epoch 101 has been established must be rejected.

## 7. Lease Security

Temporary ownership expires.

Reference lease:

```
15 seconds
```

The serving node must renew the lease.

An expired lease invalidates temporary ownership.

## 8. Quorum

A node must not be able to take over a service merely because it cannot reach the primary.

This distinction is critical:

```
"I cannot reach B"
```

does not necessarily mean:

```
"B is dead."
```

Therefore BM7 requires an authority/quorum mechanism before ownership transfer.

## 9. Split Brain

Split brain occurs when two nodes believe they own the same service.

BM7 mitigates this through:

```
Quorum
  +
Epoch
  +
Lease
  +
Ownership validation
```

These mechanisms must be implemented together.

## 10. Key Management

The reference implementation uses a shared secret for simplicity.

Production deployments should provide:

* Secure key storage
* Key rotation
* Per-node credentials
* Credential revocation
* Certificate validation
* Protection against key extraction

## 11. Denial of Service

BM7 messages are control-plane traffic.

Implementations should enforce:

* Rate limiting
* Maximum message size
* Maximum outstanding requests
* Bounded retransmission
* Peer allowlists
* Authentication before expensive processing

BM7 must not allow unauthenticated peers to consume unlimited resources.

## 12. Transport Security

UDP does not provide authentication or encryption.

BM7 therefore provides authentication at the protocol layer.

Future implementations may use:

* DTLS
* QUIC
* Another authenticated secure transport

Any transport change must preserve the BM7 security model.

## 13. Confidentiality

The reference implementation provides integrity and authentication.

It does not provide payload confidentiality.

If customer-sensitive metadata is transmitted, production deployments should use encryption.

## 14. Compromised Node

If a trusted BM7 node is compromised, cryptographic authentication alone is insufficient.

The deployment must support:

```
Node revocation
Credential rotation
Ownership quarantine
Operator intervention
```

## 15. Security Limitations

This reference implementation is not production-grade security software.

It is intended to demonstrate protocol behavior.

Before production use, the implementation requires:

* Independent security review
* Fuzz testing
* Packet parser hardening
* Key-management design
* Formal threat analysis
* Interoperability testing
* Fault injection

## 16. Security Principle

BM7 should fail closed.

If ownership cannot be authenticated or authorized, the node should not claim service ownership.
