import sys
import time
import socket
import unittest

sys.path.insert(
    0,
    "reference/python",
)

import bm7


class BM7Tests(unittest.TestCase):

    def setUp(self):

        self.a = bm7.make_node(
            "A",
            100,
        )

        self.b = bm7.make_node(
            "B",
            200,
        )

        self.c = bm7.make_node(
            "C",
            150,
        )

        self.ids = {
            self.a.node_id,
            self.b.node_id,
            self.c.node_id,
        }

        self.now = time.monotonic()

        priorities = {
            self.a.node_id: 100,
            self.b.node_id: 200,
            self.c.node_id: 150,
        }

        for node in (
            self.a,
            self.b,
            self.c,
        ):

            node.peers = set(self.ids)

            node.peers_state = {
                node_id: bm7.Peer(
                    node_id,
                    priorities[node_id],
                    0,
                    self.now,
                    0,
                    0,
                    1,
                    bm7.State.STANDBY,
                    0,
                )
                for node_id in self.ids
            }

    def test_wire_format(self):

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

        self.assertEqual(
            len(self.a.hello()),
            118,
        )

    def test_bad_key(self):

        packet = self.a.hello()

        self.b.key = b"wrong-key"

        with self.assertRaises(
            ValueError
        ):
            self.b.observe(
                packet,
                self.now,
            )

    def test_wrong_service(self):

        packet = self.a.hello()

        self.b.service_id = b"x" * 16

        with self.assertRaises(
            ValueError
        ):
            self.b.observe(
                packet,
                self.now,
            )

    def test_replay_rejected(self):

        packet = self.a.hello()

        self.b.observe(
            packet,
            self.now,
        )

        self.assertFalse(
            self.b.observe(
                packet,
                self.now,
            )
        )

    def test_no_quorum_claim(self):

        self.c.peers_state[
            self.a.node_id
        ].last_seen = (
            self.now - 20
        )

        self.c.peers_state[
            self.b.node_id
        ].last_seen = (
            self.now - 20
        )

        with self.assertRaises(
            RuntimeError
        ):
            self.c.claim(
                self.now
            )

    def test_deterministic_election(self):

        # B failed.
        for node in (
            self.a,
            self.c,
        ):
            node.peers_state[
                self.b.node_id
            ].last_seen = (
                self.now - 20
            )

        self.c.last_change = (
            self.now - 10
        )

        self.assertEqual(
            self.c.election_winner(
                self.now
            ),
            self.c.node_id,
        )

        packet = self.c.claim(
            self.now
        )

        self.assertTrue(
            self.a.observe(
                packet,
                self.now,
            )
        )

        self.assertEqual(
            self.a.active_owner,
            self.c.node_id,
        )

    def test_non_winner_cannot_claim(
        self
    ):

        for node in (
            self.a,
            self.c,
        ):
            node.peers_state[
                self.b.node_id
            ].last_seen = (
                self.now - 20
            )

        self.a.last_change = (
            self.now - 10
        )

        with self.assertRaises(
            RuntimeError
        ):
            self.a.claim(
                self.now
            )

    def test_real_udp_socket(
        self
    ):

        sender = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        receiver = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        sender.bind(
            ("127.0.0.1", 0)
        )

        receiver.bind(
            ("127.0.0.1", 0)
        )

        packet = self.a.hello()

        sender.sendto(
            packet,
            receiver.getsockname(),
        )

        data, _ = receiver.recvfrom(
            2048
        )

        self.assertEqual(
            len(data),
            118,
        )

        self.assertTrue(
            self.b.observe(
                data,
                self.now,
            )
        )

        sender.close()
        receiver.close()


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )
