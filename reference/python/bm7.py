#!/usr/bin/env python3
"""BM7 v0.3 reference implementation. Standard library only."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import secrets
import socket
import struct
import time
from dataclasses import dataclass, field
from enum import IntEnum


MAGIC = b"B7"
VERSION = 1
AUTH_LEN = 32

HEADER_FMT = "!2sBBHHHQQQ16sI32s"
HEADER_LEN = struct.calcsize(HEADER_FMT)

# 16 Service ID + 4 Priority + 4 Cost + 1 State + 7 Reserved = 32
PAYLOAD_FMT = "!16sIIB7s"
PAYLOAD_LEN = struct.calcsize(PAYLOAD_FMT)

PACKET_LEN = HEADER_LEN + PAYLOAD_LEN


class Msg(IntEnum):
    HELLO = 1
    ADVERTISE = 2
    CLAIM = 3
    ACK = 4
    RELEASE = 5
    ERROR = 6


class State(IntEnum):
    INIT = 0
    DISCOVERING = 1
    STANDBY = 2
    ACTIVE = 3
    FAILOVER = 4
    RECOVERY = 5


FLAG_ACTIVE = 0x0001
FLAG_STANDBY = 0x0002
FLAG_RECOVERING = 0x0004
FLAG_PREEMPT = 0x0008
FLAG_QUORUM = 0x0010

KNOWN_FLAGS = (
    FLAG_ACTIVE
    | FLAG_STANDBY
    | FLAG_RECOVERING
    | FLAG_PREEMPT
    | FLAG_QUORUM
)


@dataclass(frozen=True)
class Rank:
    priority: int
    cost: int
    node_id: bytes

    def key(self):
        return (-self.priority, self.cost, self.node_id)


@dataclass
class Peer:
    node_id: bytes
    priority: int = 0
    cost: int = 0
    last_seen: float = 0
    epoch: int = 0
    seq: int = 0
    session: int = 0
    state: State = State.INIT
    lease_until: float = 0


@dataclass
class Packet:
    message_type: Msg
    flags: int
    session_id: int
    epoch: int
    sequence: int
    sender_id: bytes
    lease_ms: int
    payload: bytes
    tag: bytes

    def __post_init__(self):
        if len(self.sender_id) != 16:
            raise ValueError("sender_id must be 16 bytes")

    @property
    def service_id(self):
        return self.payload[:16]

    @property
    def priority(self):
        return struct.unpack("!I", self.payload[16:20])[0]

    @property
    def cost(self):
        return struct.unpack("!I", self.payload[20:24])[0]

    @property
    def state(self):
        try:
            return State(self.payload[24])
        except (ValueError, IndexError):
            return State.INIT

    def header_without_tag(self):
        return struct.pack(
            HEADER_FMT,
            MAGIC,
            VERSION,
            int(self.message_type),
            self.flags,
            HEADER_LEN,
            len(self.payload),
            self.session_id,
            self.epoch,
            self.sequence,
            self.sender_id,
            self.lease_ms,
            b"\0" * AUTH_LEN,
        )

    def compute_tag(self, key):
        return hmac.new(
            key,
            self.header_without_tag() + self.payload,
            hashlib.sha256,
        ).digest()

    def encode(self, key):
        if len(self.payload) != PAYLOAD_LEN:
            raise ValueError("BM7 v1 payload must be 32 bytes")

        tag = self.compute_tag(key)

        return (
            struct.pack(
                HEADER_FMT,
                MAGIC,
                VERSION,
                int(self.message_type),
                self.flags,
                HEADER_LEN,
                len(self.payload),
                self.session_id,
                self.epoch,
                self.sequence,
                self.sender_id,
                self.lease_ms,
                tag,
            )
            + self.payload
        )

    @classmethod
    def decode(cls, data):
        if len(data) < HEADER_LEN:
            raise ValueError("short packet")

        (
            magic,
            version,
            message_type,
            flags,
            header_length,
            payload_length,
            session_id,
            epoch,
            sequence,
            sender_id,
            lease_ms,
            tag,
        ) = struct.unpack(HEADER_FMT, data[:HEADER_LEN])

        if (
            magic != MAGIC
            or version != VERSION
            or header_length != HEADER_LEN
            or payload_length != len(data) - HEADER_LEN
        ):
            raise ValueError("invalid header")

        if payload_length != PAYLOAD_LEN:
            raise ValueError("invalid payload length")

        if flags & ~KNOWN_FLAGS:
            raise ValueError("unknown flag")

        try:
            message_type = Msg(message_type)
        except ValueError:
            raise ValueError("unknown message type")

        return cls(
            message_type,
            flags,
            session_id,
            epoch,
            sequence,
            sender_id,
            lease_ms,
            data[HEADER_LEN:],
            tag,
        )


@dataclass
class BM7Node:
    node_id: bytes
    service_id: bytes
    priority: int
    cost: int
    peers: set[bytes]
    key: bytes

    hello_interval: float = 2.0
    failure_threshold: int = 3
    lease_seconds: float = 10.0
    hold_down: float = 10.0
    preemption_delay: float = 5.0

    session_id: int = field(
        default_factory=lambda: secrets.randbits(64)
    )

    epoch: int = 0
    seq: int = 0
    state: State = State.INIT

    peers_state: dict[bytes, Peer] = field(default_factory=dict)

    active_owner: bytes | None = None
    active_lease_until: float = 0

    last_change: float = field(
        default_factory=time.monotonic
    )

    def __post_init__(self):
        if len(self.node_id) != 16:
            raise ValueError("node_id must be 16 bytes")

        if len(self.service_id) != 16:
            raise ValueError("service_id must be 16 bytes")

        self.peers = set(self.peers)
        self.peers.add(self.node_id)

        self.peers_state[self.node_id] = Peer(
            self.node_id,
            self.priority,
            self.cost,
            time.monotonic(),
            self.epoch,
            0,
            self.session_id,
            self.state,
            0,
        )

    def rank(self, node_id):
        peer = self.peers_state[node_id]
        return Rank(
            peer.priority,
            peer.cost,
            node_id,
        )

    def quorum(self):
        return len(self.peers) // 2 + 1

    def live_voters(self, now=None):
        now = time.monotonic() if now is None else now

        cutoff = (
            self.hello_interval
            * self.failure_threshold
        )

        return {
            node_id
            for node_id in self.peers
            if (
                node_id == self.node_id
                or (
                    node_id in self.peers_state
                    and now
                    - self.peers_state[node_id].last_seen
                    <= cutoff
                )
            )
        }

    def has_quorum(self, now=None):
        return (
            len(self.live_voters(now))
            >= self.quorum()
        )

    def election_winner(self, now=None):
        live = self.live_voters(now)

        if len(live) < self.quorum():
            return None

        return min(
            live,
            key=lambda node_id:
                self.rank(node_id).key(),
        )

    def _payload(self, state):
        return struct.pack(
            PAYLOAD_FMT,
            self.service_id,
            self.priority,
            self.cost,
            int(state),
            b"\0" * 7,
        )

    def packet(
        self,
        message_type,
        state=None,
        lease_ms=0,
        flags=0,
    ):
        self.seq += 1

        state = (
            self.state
            if state is None
            else state
        )

        if self.has_quorum():
            flags |= FLAG_QUORUM

        return Packet(
            message_type,
            flags,
            self.session_id,
            self.epoch,
            self.seq,
            self.node_id,
            lease_ms,
            self._payload(state),
            b"",
        ).encode(self.key)

    def hello(self):
        return self.packet(
            Msg.HELLO,
            self.state,
        )

    def advertise(self):
        return self.packet(
            Msg.ADVERTISE,
            self.state,
        )

    def should_claim(self, now=None):
        now = (
            time.monotonic()
            if now is None
            else now
        )

        if not self.has_quorum(now):
            return False

        if self.election_winner(now) != self.node_id:
            return False

        if (
            self.active_owner
            and self.active_owner != self.node_id
            and self.active_lease_until > now
        ):
            return False

        return (
            self.active_owner is None
            or now - self.last_change
            >= self.preemption_delay
        )

    def claim(self, now=None):
        now = (
            time.monotonic()
            if now is None
            else now
        )

        if not self.has_quorum(now):
            raise RuntimeError(
                "cannot claim without quorum"
            )

        if self.election_winner(now) != self.node_id:
            raise RuntimeError(
                "node is not election winner"
            )

        if (
            self.active_owner
            and self.active_owner != self.node_id
            and self.active_lease_until > now
        ):
            raise RuntimeError(
                "current owner lease has not expired"
            )

        self.epoch = max(
            [self.epoch]
            + [
                peer.epoch
                for peer in self.peers_state.values()
            ]
        ) + 1

        self.state = State.ACTIVE
        self.active_owner = self.node_id

        self.active_lease_until = (
            now + self.lease_seconds
        )

        self.last_change = now

        return self.packet(
            Msg.CLAIM,
            State.ACTIVE,
            int(self.lease_seconds * 1000),
            FLAG_ACTIVE | FLAG_QUORUM,
        )

    def observe(self, data, now=None):
        now = (
            time.monotonic()
            if now is None
            else now
        )

        message = Packet.decode(data)

        if not hmac.compare_digest(
            message.tag,
            message.compute_tag(self.key),
        ):
            raise ValueError(
                "bad authentication tag"
            )

        if message.service_id != self.service_id:
            raise ValueError(
                "wrong service"
            )

        if message.sender_id == self.node_id:
            raise ValueError(
                "self packet"
            )

        if message.sender_id not in self.peers:
            raise ValueError(
                "unknown peer"
            )

        peer = self.peers_state.setdefault(
            message.sender_id,
            Peer(message.sender_id),
        )

        if message.epoch < self.epoch:
            return False

        if (
            message.session_id == peer.session
            and message.epoch == peer.epoch
            and message.sequence <= peer.seq
        ):
            return False

        if message.message_type == Msg.CLAIM:

            if not (
                message.flags
                & FLAG_ACTIVE
            ):
                return False

            if not (
                message.flags
                & FLAG_QUORUM
            ):
                return False

            if message.lease_ms <= 0:
                return False

            if message.epoch <= self.epoch:
                return False

            if not self.has_quorum(now):
                return False

            if (
                self.election_winner(now)
                != message.sender_id
            ):
                return False

        elif (
            message.message_type
            == Msg.RELEASE
            and self.active_owner
            != message.sender_id
        ):
            return False

        peer.priority = message.priority
        peer.cost = message.cost
        peer.last_seen = now
        peer.epoch = message.epoch
        peer.seq = message.sequence
        peer.session = message.session_id
        peer.state = message.state

        peer.lease_until = (
            now + message.lease_ms / 1000
            if message.lease_ms
            else 0
        )

        if message.epoch > self.epoch:
            self.epoch = message.epoch

        if message.message_type == Msg.CLAIM:

            self.active_owner = (
                message.sender_id
            )

            self.active_lease_until = (
                peer.lease_until
            )

            self.state = State.STANDBY
            self.last_change = now

        elif (
            message.message_type == Msg.RELEASE
            and self.active_owner
            == message.sender_id
        ):

            self.active_owner = None
            self.active_lease_until = 0
            self.last_change = now

        return True


def make_node(
    name,
    priority,
    peers=None,
    key=b"demo-secret",
):
    node_id = hashlib.sha256(
        name.encode()
    ).digest()[:16]

    service_id = hashlib.sha256(
        b"bm7-demo-service"
    ).digest()[:16]

    return BM7Node(
        node_id,
        service_id,
        priority,
        0,
        set(peers or {node_id}),
        key,
    )


def demo():

    a = make_node("A", 100)
    b = make_node("B", 200)
    c = make_node("C", 150)

    ids = {
        a.node_id,
        b.node_id,
        c.node_id,
    }

    now = time.monotonic()

    priorities = {
        a.node_id: 100,
        b.node_id: 200,
        c.node_id: 150,
    }

    for node in (a, b, c):

        node.peers = set(ids)

        node.peers_state = {
            node_id: Peer(
                node_id,
                priorities[node_id],
                0,
                now,
                0,
                0,
                1,
                State.STANDBY,
                0,
            )
            for node_id in ids
        }

    # B failed.
    for node in (a, c):
        node.peers_state[
            b.node_id
        ].last_seen = now - 20

    a.peers_state[
        c.node_id
    ].last_seen = now

    c.peers_state[
        a.node_id
    ].last_seen = now

    c.last_change = now - 10

    assert (
        c.election_winner(now)
        == c.node_id
    )

    assert c.should_claim(now)

    packet = c.claim(now)

    assert a.observe(
        packet,
        now,
    )

    assert (
        a.active_owner
        == c.node_id
    )

    # Replay must be rejected.
    assert not a.observe(
        packet,
        now,
    )

    print(
        f"BM7 demo OK: "
        f"{PACKET_LEN}-byte packet, "
        f"quorum/election/epoch/lease/"
        f"HMAC/replay"
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--demo",
        action="store_true",
    )

    args = parser.parse_args()

    if args.demo:
        demo()
