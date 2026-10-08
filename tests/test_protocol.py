import sys
import socket
import time
import unittest

sys.path.insert(
    0,
    "reference/python",
)

import bm7


class TestBM7(unittest.TestCase):

    def setUp(self):

        self.a = bm7.make_node(
            "A",
            100,
            ["A", "B", "C"],
        )

        self.b = bm7.make_node(
            "B",
            200,
            ["A", "B", "C"],
        )

        self.c = bm7.make_node(
            "C",
            150,
            ["A", "B", "C"],
        )

        self.nodes = [
            self.a,
            self.b,
            self.c,
        ]

        self.now = time.monotonic()

        priorities = {
            self.a.node_id: 100,
            self.b.node_id: 200,
            self.c.node_id: 150,
        }

        ids = {
            self.a.node_id,
            self.b.node_id,
            self.c.node_id,
        }

        for node in self.nodes:

            for node_id in ids:

                if node_id == node.node_id:
                    continue

                node.peers_state[
                    node_id
                ] = bm7.Peer(
                    node_id=node_id,
                    priority=priorities[node_id],
                    cost=0,
                    last_seen=self.now,
                    epoch=0,
                    sequence=0,
                    session_id=0,
                    state=bm7.State.STANDBY,
                )

    def test_wire_size(self):

        self.assertEqual(
            bm7.HEADER_LEN,
            86,
        )

        self.assertEqual(
            bm7.PAYLOAD_LEN,
            32,
        )

        self.assertEqual(
            bm7.PACKET_LEN,
            118,
        )

        packet = self.a.hello()

        self.assertEqual(
            len(packet),
            118,
        )

    def test_encode_decode(self):

        raw = self.a.hello()

        packet = bm7.Packet.decode(
            raw
        )

        self.assertEqual(
            packet.message_type,
            bm7.Msg.HELLO,
        )

        self.assertEqual(
            packet.service_id,
            self.a.service_id,
        )

        self.assertEqual(
            packet.priority,
            100,
        )

    def test_wrong_key_rejected(self):

        raw = self.a.hello()

        self.b.key = (
            b"wrong-secret"
        )

        with self.assertRaises(
            ValueError
        ):

            self.b.observe(
                raw,
                self.now,
            )

    def test_wrong_service_rejected(self):

        raw = self.a.hello()

        self.b.service_id = (
            b"X" * 16
        )

        with self.assertRaises(
            ValueError
        ):

            self.b.observe(
                raw,
                self.now,
            )

    def test_replay_rejected(self):

        raw = self.a.hello()

        self.b.observe(
            raw,
            self.now,
        )

        result = self.b.observe(
            raw,
            self.now,
        )

        self.assertFalse(result)

    def test_quorum(self):

        self.assertEqual(
            self.a.quorum(),
            2,
        )

        self.assertTrue(
            self.a.has_quorum(
                self.now
            )
        )

    def test_election(self):

        b_id = self.b.node_id

        for node in (
            self.a,
            self.c,
        ):

            node.peers_state[
                b_id
            ].last_seen = (
                self.now - 20
            )

        self.assertEqual(
            self.a.election_winner(
                self.now
            ),
            self.c.node_id,
        )

        self.assertEqual(
            self.c.election_winner(
                self.now
            ),
            self.c.node_id,
        )

    def test_non_winner_cannot_claim(self):

        b_id = self.b.node_id

        for node in (
            self.a,
            self.c,
        ):

            node.peers_state[
                b_id
            ].last_seen = (
                self.now - 20
            )

        with self.assertRaises(
            RuntimeError
        ):

            self.a.claim(
                self.now
            )

    def test_valid_claim(self):

        b_id = self.b.node_id

        for node in (
            self.a,
            self.c,
        ):

            node.peers_state[
                b_id
            ].last_seen = (
                self.now - 20
            )

        self.c.last_change = (
            self.now - 10
        )

        claim = self.c.claim(
            self.now
        )

        self.assertEqual(
            len(claim),
            118,
        )

        accepted = self.a.observe(
            claim,
            self.now,
        )

        self.assertTrue(
            accepted
        )

        self.assertEqual(
            self.a.active_owner,
            self.c.node_id,
        )

    def test_real_udp(self):

        tx = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        rx = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        tx.bind(
            ("127.0.0.1", 0)
        )

        rx.bind(
            ("127.0.0.1", 0)
        )

        try:

            raw = self.a.hello()

            tx.sendto(
                raw,
                rx.getsockname(),
            )

            rx.settimeout(2)

            data, _ = (
                rx.recvfrom(2048)
            )

            self.assertEqual(
                len(data),
                118,
            )

            accepted = (
                self.b.observe(
                    data,
                    self.now,
                )
            )

            self.assertTrue(
                accepted
            )

        finally:

            tx.close()
            rx.close()


if __name__ == "__main__":

    unittest.main(
        verbosity=2
    )
