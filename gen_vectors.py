"""Generate BM7 test vectors with the Python reference implementation.

Usage: python3 tests/interop/gen_vectors.py <out.json>
"""
import json, struct, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "reference" / "python"))
import bm7

KEY = b"bm7-interop-test-key"

def vec(name, mtype, flags, sess, epoch, seq, sender, lease, prio, cost, state):
    payload = bytes(range(16)) + struct.pack("!II", prio, cost) + bytes([state]) + b"\0" * 7
    p = bm7.Packet(bm7.Msg(mtype), flags, sess, epoch, seq, sender, lease, payload, b"\0" * 32)
    return {"name": name, "type": mtype, "flags": flags, "session": sess, "epoch": epoch,
            "sequence": seq, "sender": sender.hex(), "lease": lease, "priority": prio,
            "cost": cost, "state": state, "packet": p.encode(KEY).hex()}

vectors = [
    vec("hello", 1, 0x0002, 7, 1, 1, b"A" * 16, 10000, 100, 10, 2),
    vec("advertise", 2, 0x0002, 7, 1, 2, b"B" * 16, 10000, 200, 5, 2),
    vec("claim", 3, 0x0001 | 0x0010, 7, 2, 3, b"C" * 16, 10000, 150, 1, 3),
    vec("ack", 4, 0x0001, 2**63, 2**40, 2**50, b"\xff" * 16, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 3),
    vec("release", 5, 0x0004, 0, 0, 0, bytes(16), 0, 0, 0, 5),
    vec("error", 6, 0, 1, 1, 1, b"E" * 16, 1, 1, 1, 0),
]
json.dump({"key": KEY.decode(), "vectors": vectors}, open(sys.argv[1], "w"), indent=1)
print(f"wrote {len(vectors)} vectors")
