"""Loopback UDP smoke test using the reference codec (not a network-interop proof)."""
import pathlib, socket, struct, sys, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "reference" / "python"))
import bm7


class TestClient(unittest.TestCase):
    def test_udp_roundtrip(self):
        key = b"k"
        payload = bytes(16) + struct.pack("!II", 1, 1) + bytes([2]) + bytes(7)
        pkt = bm7.Packet(bm7.Msg.HELLO, 0x0002, 1, 1, 1, b"N" * 16, 1000, payload, bytes(32))
        rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        rx.bind(("127.0.0.1", 0))
        rx.settimeout(2)
        tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tx.sendto(pkt.encode(key), rx.getsockname())
        data, _ = rx.recvfrom(2048)
        self.assertEqual(bm7.Packet.decode(data).sequence, 1)
        rx.close(); tx.close()


if __name__ == "__main__":
    unittest.main()
