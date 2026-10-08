# BM7 Security Model

BM7 v1 authenticates every state-changing message with HMAC-SHA-256.

## Properties

- integrity: HMAC
- peer authentication: pre-shared deployment key plus configured Node IDs
- replay resistance: epoch + per-sender sequence tracking
- stale ownership resistance: lease expiration + epoch ordering
- split-brain mitigation: majority quorum
- malformed input handling: strict length/type validation

## Non-goals

BM7 does not invent cryptographic primitives and does not provide payload confidentiality. If confidentiality is required, deploy BM7 inside a protected transport/overlay such as a site VPN or use an appropriate external security mechanism.

## Key management

Key provisioning, rotation and revocation are deployment responsibilities. Implementations MUST fail closed when authentication is configured and a packet has an invalid tag.
