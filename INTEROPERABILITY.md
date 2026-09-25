# Interoperability

The Python and Go implementations implement the same version-1 packet format.

Cross-language vectors are generated from the deterministic codec and HMAC rules. A future independent implementation can use `BM7-SPEC.md` alone; it should not need to inspect either reference implementation.

## Required evidence before an IANA resubmission

- reproducible test suite;
- Python/Go interoperability;
- packet captures from real UDP traffic;
- failure and recovery lab results;
- malformed/replay/security tests;
- at least one independently operated deployment or implementation if available;
- documentation of the exact problem BM7 solves and how it differs from existing protocols.
