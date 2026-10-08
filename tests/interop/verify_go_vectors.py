"""Verify packets produced by the Go implementation using the Python one.

Usage: python3 tests/interop/verify_go_vectors.py <go_vectors.json>
"""
import json, struct, sys, pathlib, hmac
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "reference" / "python"))
import bm7

d = json.load(open(sys.argv[1]))
key = d["key"].encode()
for v in d["vectors"]:
    raw = bytes.fromhex(v["packet"])
    p = bm7.Packet.decode(raw)
    assert hmac.compare_digest(p.tag, p.compute_tag(key)), "HMAC mismatch"
    assert not hmac.compare_digest(p.tag, p.compute_tag(b"wrong-key"))
    assert (int(p.message_type), p.flags, p.session_id, p.epoch, p.sequence, p.lease_ms) == \
        (v["type"], v["flags"], v["session"], v["epoch"], v["sequence"], v["lease"])
    assert p.sender_id.hex() == v["sender"]
    assert (p.priority, p.cost, int(p.state)) == (v["priority"], v["cost"], v["state"])
    assert p.encode(key) == raw, "Python re-encode differs from Go bytes"
print(f"OK: {len(d['vectors'])} Go-generated packets verified by Python")
