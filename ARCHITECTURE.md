# BM7 Architecture

```text
                 routed network / VPN / LAN
             +-------------------------------+
             |                               |
          +--+--+                         +--+--+
          | A   |<---- BM7 UDP ---------->| B   |
          +--+--+                         +--+--+
             ^                               ^
             |                               |
             +------------+------------------+
                          |
                       +--+--+
                       | C   |
                       +-----+
```

BM7 is the coordination plane. The data plane remains external to BM7 and may be implemented by routing, firewall, proxy, NAT, or application service controls.

The implementation is intentionally split into:

1. protocol codec;
2. authentication and replay validation;
3. peer liveness;
4. election;
5. service ownership state machine;
6. transport adapter.
