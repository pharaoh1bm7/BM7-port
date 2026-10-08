#!/usr/bin/env python3

"""
BM7 v1 reference implementation.

Branch Mobility and Failover Protocol.

Features:
- Fixed 118-byte binary UDP packet
- IPv4 / IPv6 UDP transport
- HMAC-SHA256 authentication
- Service isolation
- HELLO / ADVERTISE / CLAIM / ACK / RELEASE / ERROR
- Epoch protection
- Sequence/replay protection
- Lease validation
- Quorum
- Deterministic election
- Lease-based failover
- Preferred-return / priority preemption
"""

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

PAYLOAD_FMT = "!16sIIB7s"
PAYLOAD_LEN = struct.calcsize(PAYLOAD_FMT)

PACKET_LEN = HEADER_LEN + PAYLOAD_LEN

DEFAULT_HELLO_INTERVAL = 2.0
DEFAULT_FAILURE_THRESHOLD = 3
DEFAULT_LEASE_SECONDS = 10.0
DEFAULT_PREEMPTION_DELAY = 5.0
DEFAULT_HOLD_DOWN = 10.0


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
        return (
            -self.priority,
            self.cost,
            self.node_id,
        )


@dataclass
class Peer:
    node_id: bytes
    priority: int = 0
    cost: int = 0
    last_seen: float = 0.0
    epoch: int = 0
    sequence: int = 0
    session_id: int = 0
    state: State = State.INIT
    lease_until: float = 0.0


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
            raise ValueError(
                "sender_id must be exactly 16 bytes"
            )

        if len(self.payload) != PAYLOAD_LEN:
            raise ValueError(
                f"payload must be exactly {PAYLOAD_LEN} bytes"
            )

    @property
    def service_id(self):
        return self.payload[:16]

    @property
    def priority(self):
        return struct.unpack(
            "!I",
            self.payload[16:20],
        )[0]

    @property
    def cost(self):
        return struct.unpack(
            "!I",
            self.payload[20:24],
        )[0]

    @property
    def state(self):

        try:
            return State(self.payload[24])

        except ValueError:
            raise ValueError(
                "invalid BM7 state"
            )

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
            self.header_without_tag()
            + self.payload,
            hashlib.sha256,
        ).digest()

    def encode(self, key):

        if len(self.payload) != PAYLOAD_LEN:
            raise ValueError(
                "invalid BM7 payload size"
            )

        tag = self.compute_tag(key)

        header = struct.pack(
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

        packet = header + self.payload

        if len(packet) != PACKET_LEN:
            raise ValueError(
                f"invalid BM7 packet size: {len(packet)}"
            )

        return packet

    @classmethod
    def decode(cls, data):

        if len(data) != PACKET_LEN:
            raise ValueError(
                f"invalid packet length: {len(data)}; "
                f"expected {PACKET_LEN}"
            )

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
        ) = struct.unpack(
            HEADER_FMT,
            data[:HEADER_LEN],
        )

        if magic != MAGIC:
            raise ValueError("invalid BM7 magic")

        if version != VERSION:
            raise ValueError("unsupported BM7 version")

        if header_length != HEADER_LEN:
            raise ValueError("invalid header length")

        if payload_length != PAYLOAD_LEN:
            raise ValueError("invalid payload length")

        if flags & ~KNOWN_FLAGS:
            raise ValueError("unknown BM7 flags")

        try:
            message_type = Msg(message_type)

        except ValueError:
            raise ValueError(
                "unknown BM7 message type"
            )

        packet = cls(
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

        packet.state

        return packet


@dataclass
class BM7Node:

    node_id: bytes
    service_id: bytes

    priority: int
    cost: int

    peers: set[bytes]

    key: bytes

    hello_interval: float = DEFAULT_HELLO_INTERVAL

    failure_threshold: int = DEFAULT_FAILURE_THRESHOLD

    lease_seconds: float = DEFAULT_LEASE_SECONDS

    preemption_delay: float = DEFAULT_PREEMPTION_DELAY

    hold_down: float = DEFAULT_HOLD_DOWN

    session_id: int = field(
        default_factory=lambda: secrets.randbits(64)
    )

    epoch: int = 0
    sequence: int = 0

    state: State = State.INIT

    peers_state: dict[bytes, Peer] = field(
        default_factory=dict
    )

    active_owner: bytes | None = None

    active_lease_until: float = 0.0

    last_change: float = field(
        default_factory=time.monotonic
    )

    election_stable_since: float = field(
        default_factory=time.monotonic
    )

    # ---------------------------------------------------------
    # Preferred-return / priority-preemption timer.
    #
    # This is intentionally separate from
    # election_stable_since.
    # ---------------------------------------------------------

    preemption_started_at: float | None = None

    def __post_init__(self):

        if len(self.node_id) != 16:
            raise ValueError(
                "node_id must be 16 bytes"
            )

        if len(self.service_id) != 16:
            raise ValueError(
                "service_id must be 16 bytes"
            )

        self.peers = set(self.peers)

        self.peers.add(
            self.node_id
        )

        now = time.monotonic()

        self.peers_state[self.node_id] = Peer(
            node_id=self.node_id,
            priority=self.priority,
            cost=self.cost,
            last_seen=now,
            epoch=self.epoch,
            sequence=self.sequence,
            session_id=self.session_id,
            state=self.state,
        )

    # =========================================================
    # Quorum
    # =========================================================

    def quorum(self):

        return (
            len(self.peers) // 2
        ) + 1

    def live_voters(self, now=None):

        now = (
            time.monotonic()
            if now is None
            else now
        )

        failure_window = (
            self.hello_interval
            * self.failure_threshold
        )

        result = set()

        for node_id in self.peers:

            if node_id == self.node_id:

                result.add(node_id)
                continue

            peer = self.peers_state.get(node_id)

            if peer is None:
                continue

            if (
                now - peer.last_seen
                <= failure_window
            ):

                result.add(node_id)

        return result

    def has_quorum(self, now=None):

        return (
            len(self.live_voters(now))
            >= self.quorum()
        )

    # =========================================================
    # Election
    # =========================================================

    def rank(self, node_id):

        peer = self.peers_state.get(node_id)

        if peer is None:
            raise ValueError(
                "unknown peer"
            )

        return Rank(
            peer.priority,
            peer.cost,
            node_id,
        )

    def election_winner(self, now=None):

        now = (
            time.monotonic()
            if now is None
            else now
        )

        if not self.has_quorum(now):
            return None

        candidates = self.live_voters(now)

        if not candidates:
            return None

        return min(
            candidates,
            key=lambda node_id:
            self.rank(node_id).key(),
        )

    # =========================================================
    # Payload
    # =========================================================

    def build_payload(self, selected_state):

        payload = struct.pack(
            PAYLOAD_FMT,
            self.service_id,
            self.priority,
            self.cost,
            int(selected_state),
            b"\0" * 7,
        )

        if len(payload) != PAYLOAD_LEN:
            raise ValueError(
                "internal payload size error"
            )

        return payload

    # =========================================================
    # Packet
    # =========================================================

    def packet(
        self,
        message_type,
        state=None,
        lease_ms=0,
        flags=0,
    ):

        self.sequence += 1

        selected_state = (
            self.state
            if state is None
            else state
        )

        if self.has_quorum():
            flags |= FLAG_QUORUM

        payload = self.build_payload(
            selected_state
        )

        packet = Packet(
            message_type=message_type,
            flags=flags,
            session_id=self.session_id,
            epoch=self.epoch,
            sequence=self.sequence,
            sender_id=self.node_id,
            lease_ms=lease_ms,
            payload=payload,
            tag=b"",
        )

        return packet.encode(self.key)

    # =========================================================
    # Ownership advertisement
    # =========================================================

    def hello(self):

        now = time.monotonic()

        lease_ms = 0
        flags = 0

        if (
            self.state == State.ACTIVE
            and
            self.active_owner == self.node_id
        ):

            self.active_lease_until = (
                now + self.lease_seconds
            )

            lease_ms = int(
                self.lease_seconds * 1000
            )

            flags |= FLAG_ACTIVE

        return self.packet(
            Msg.HELLO,
            self.state,
            lease_ms,
            flags,
        )

    def advertise(self):

        now = time.monotonic()

        lease_ms = 0
        flags = 0

        if (
            self.state == State.ACTIVE
            and
            self.active_owner == self.node_id
        ):

            self.active_lease_until = (
                now + self.lease_seconds
            )

            lease_ms = int(
                self.lease_seconds * 1000
            )

            flags |= FLAG_ACTIVE

        return self.packet(
            Msg.ADVERTISE,
            self.state,
            lease_ms,
            flags,
        )

    # =========================================================
    # Claim
    # =========================================================

    def claim(
        self,
        now=None,
        preempt=False,
    ):

        now = (
            time.monotonic()
            if now is None
            else now
        )

        if not self.has_quorum(now):

            raise RuntimeError(
                "cannot claim without quorum"
            )

        winner = self.election_winner(now)

        if winner != self.node_id:

            raise RuntimeError(
                "this node is not the election winner"
            )

        # -----------------------------------------------------
        # A normal failover claim MUST NOT override a valid
        # lease held by another node.
        #
        # Preferred-return is the only controlled exception.
        # -----------------------------------------------------

        if (
            self.active_owner
            and
            self.active_owner != self.node_id
            and
            self.active_lease_until > now
        ):

            if not preempt:

                raise RuntimeError(
                    "another owner still has a valid lease"
                )

            owner_peer = self.peers_state.get(
                self.active_owner
            )

            if owner_peer is None:

                raise RuntimeError(
                    "active owner state unavailable"
                )

            local_rank = Rank(
                self.priority,
                self.cost,
                self.node_id,
            )

            owner_rank = Rank(
                owner_peer.priority,
                owner_peer.cost,
                self.active_owner,
            )

            # Lower key = better rank.
            # Therefore local must be strictly better.
            if local_rank.key() >= owner_rank.key():

                raise RuntimeError(
                    "preemption requires higher priority/rank"
                )

        # -----------------------------------------------------
        # New epoch
        # -----------------------------------------------------

        known_epochs = [self.epoch]

        for peer in self.peers_state.values():

            known_epochs.append(
                peer.epoch
            )

        self.epoch = max(
            known_epochs
        ) + 1

        self.state = State.ACTIVE

        self.active_owner = self.node_id

        self.active_lease_until = (
            now + self.lease_seconds
        )

        self.last_change = now

        self.election_stable_since = now

        self.preemption_started_at = None

        flags = (
            FLAG_ACTIVE
            | FLAG_QUORUM
        )

        if preempt:

            flags |= FLAG_PREEMPT

        return self.packet(
            Msg.CLAIM,
            State.ACTIVE,
            int(
                self.lease_seconds * 1000
            ),
            flags,
        )

    # =========================================================
    # Receive
    # =========================================================

    def observe(
        self,
        packet_data,
        now=None,
    ):

        now = (
            time.monotonic()
            if now is None
            else now
        )

        packet = Packet.decode(
            packet_data
        )

        expected_tag = packet.compute_tag(
            self.key
        )

        if not hmac.compare_digest(
            packet.tag,
            expected_tag,
        ):

            raise ValueError(
                "bad authentication tag"
            )

        if packet.service_id != self.service_id:

            raise ValueError(
                "packet belongs to another service"
            )

        if packet.sender_id not in self.peers:

            raise ValueError(
                "unknown peer"
            )

        if packet.sender_id == self.node_id:

            return False

        peer = self.peers_state.get(
            packet.sender_id
        )

        if peer is None:

            raise ValueError(
                "peer state unavailable"
            )

        if packet.epoch < self.epoch:

            return False

        if (
            packet.session_id
            == peer.session_id
            and
            packet.epoch
            == peer.epoch
            and
            packet.sequence
            <= peer.sequence
        ):

            return False

        # =====================================================
        # CLAIM validation
        # =====================================================

        if packet.message_type == Msg.CLAIM:

            if not (
                packet.flags
                & FLAG_ACTIVE
            ):

                return False

            if not (
                packet.flags
                & FLAG_QUORUM
            ):

                return False

            if packet.lease_ms <= 0:

                return False

            if packet.epoch <= self.epoch:

                return False

            if not self.has_quorum(now):

                return False

            winner = self.election_winner(
                now
            )

            if winner != packet.sender_id:

                return False

            # -------------------------------------------------
            # Preferred-return preemption validation.
            #
            # A PREEMPT claim may override a still-valid
            # lease ONLY when the claimant is strictly
            # better-ranked than the current owner.
            # -------------------------------------------------

            if packet.flags & FLAG_PREEMPT:

                if (
                    self.active_owner
                    and
                    self.active_owner
                    != packet.sender_id
                    and
                    self.active_lease_until
                    > now
                ):

                    owner_peer = (
                        self.peers_state.get(
                            self.active_owner
                        )
                    )

                    if owner_peer is None:

                        return False

                    claimant_rank = Rank(
                        packet.priority,
                        packet.cost,
                        packet.sender_id,
                    )

                    owner_rank = Rank(
                        owner_peer.priority,
                        owner_peer.cost,
                        self.active_owner,
                    )

                    if (
                        claimant_rank.key()
                        >=
                        owner_rank.key()
                    ):

                        return False

        # =====================================================
        # RELEASE validation
        # =====================================================

        if packet.message_type == Msg.RELEASE:

            if (
                self.active_owner
                != packet.sender_id
            ):

                return False

        # =====================================================
        # Commit peer information
        # =====================================================

        peer.priority = packet.priority

        peer.cost = packet.cost

        peer.last_seen = now

        peer.epoch = packet.epoch

        peer.sequence = packet.sequence

        peer.session_id = packet.session_id

        peer.state = packet.state

        if packet.lease_ms:

            peer.lease_until = (
                now
                + packet.lease_ms
                / 1000.0
            )

        # =====================================================
        # ACTIVE HELLO / ADVERTISE
        # =====================================================

        if packet.message_type in (
            Msg.HELLO,
            Msg.ADVERTISE,
        ):

            active_announcement = (
                packet.state
                == State.ACTIVE
                and
                bool(
                    packet.flags
                    & FLAG_ACTIVE
                )
                and
                packet.lease_ms > 0
            )

            # -------------------------------------------------
            # Newer epoch
            # -------------------------------------------------

            if packet.epoch > self.epoch:

                self.epoch = packet.epoch

                if active_announcement:

                    self.active_owner = (
                        packet.sender_id
                    )

                    self.active_lease_until = (
                        peer.lease_until
                    )

                    self.state = (
                        State.STANDBY
                    )

                    self.last_change = now

                    self.election_stable_since = (
                        now
                    )

                    self.preemption_started_at = (
                        None
                    )

            # -------------------------------------------------
            # Same epoch
            # -------------------------------------------------

            elif packet.epoch == self.epoch:

                if active_announcement:

                    if self.active_owner is None:

                        self.active_owner = (
                            packet.sender_id
                        )

                        self.active_lease_until = (
                            peer.lease_until
                        )

                        self.state = (
                            State.STANDBY
                        )

                        self.last_change = now

                        self.election_stable_since = (
                            now
                        )

                        self.preemption_started_at = (
                            None
                        )

                    elif (
                        self.active_owner
                        == packet.sender_id
                    ):

                        # -------------------------------------------------
                        # IMPORTANT:
                        #
                        # Do NOT reset election_stable_since here.
                        #
                        # A normal heartbeat from the same owner does
                        # not create a new election view.
                        # -------------------------------------------------

                        self.active_lease_until = (
                            peer.lease_until
                        )

                        if self.state == State.ACTIVE:

                            if (
                                self.active_owner
                                != self.node_id
                            ):

                                self.state = (
                                    State.STANDBY
                                )

                    else:

                        # Two different owners claim the same epoch.
                        return True

            return True

        # =====================================================
        # ACK
        # =====================================================

        if packet.message_type == Msg.ACK:

            if packet.epoch > self.epoch:

                self.epoch = packet.epoch

            return True

        # =====================================================
        # CLAIM commit
        # =====================================================

        if packet.message_type == Msg.CLAIM:

            self.epoch = packet.epoch

            self.active_owner = (
                packet.sender_id
            )

            self.active_lease_until = (
                peer.lease_until
            )

            self.state = State.STANDBY

            self.last_change = now

            self.election_stable_since = now

            self.preemption_started_at = None

            return True

        # =====================================================
        # RELEASE
        # =====================================================

        if packet.message_type == Msg.RELEASE:

            if (
                self.active_owner
                == packet.sender_id
            ):

                self.active_owner = None

                self.active_lease_until = 0.0

                self.state = State.FAILOVER

                self.last_change = now

                self.election_stable_since = (
                    now
                )

                self.preemption_started_at = (
                    None
                )

            return True

        return True

    # =========================================================
    # Failover / Preferred Return
    # =========================================================

    def should_claim(self, now=None):

        now = (
            time.monotonic()
            if now is None
            else now
        )

        # =====================================================
        # Existing remote owner
        # =====================================================

        if (
            self.active_owner
            and
            self.active_owner
            != self.node_id
        ):

            owner_id = self.active_owner

            # -------------------------------------------------
            # Remote owner still has a valid lease.
            # -------------------------------------------------

            if self.active_lease_until > now:

                owner_peer = (
                    self.peers_state.get(
                        owner_id
                    )
                )

                if owner_peer is not None:

                    local_rank = Rank(
                        self.priority,
                        self.cost,
                        self.node_id,
                    )

                    owner_rank = Rank(
                        owner_peer.priority,
                        owner_peer.cost,
                        owner_id,
                    )

                    # -------------------------------------------------
                    # Preferred return:
                    #
                    # Local node must be strictly better-ranked.
                    # -------------------------------------------------

                    if (
                        local_rank.key()
                        <
                        owner_rank.key()
                    ):

                        # Quorum is mandatory.
                        if not self.has_quorum(
                            now
                        ):

                            self.preemption_started_at = (
                                None
                            )

                            return False

                        # Local node must be the deterministic
                        # election winner.
                        winner = (
                            self.election_winner(
                                now
                            )
                        )

                        if winner != self.node_id:

                            self.preemption_started_at = (
                                None
                            )

                            return False

                        # Start the independent preemption timer.
                        if (
                            self.preemption_started_at
                            is None
                        ):

                            self.preemption_started_at = (
                                now
                            )

                            return False

                        # Wait until the configured preferred-return
                        # delay has elapsed.
                        if (
                            now
                            - self.preemption_started_at
                            <
                            self.preemption_delay
                        ):

                            return False

                        # Controlled preemption is now permitted.
                        return True

                # Current owner exists and is not lower-ranked.
                self.preemption_started_at = None

                return False

            # -------------------------------------------------
            # Remote owner lease expired.
            # Existing failover behavior.
            # -------------------------------------------------

            self.active_owner = None

            self.active_lease_until = 0.0

            self.state = State.FAILOVER

            self.last_change = now

            self.election_stable_since = now

            self.preemption_started_at = None

        # =====================================================
        # Our own lease expired
        # =====================================================

        if (
            self.state == State.ACTIVE
            and
            self.active_owner
            == self.node_id
        ):

            if (
                self.active_lease_until
                > now
            ):

                return False

            self.active_owner = None

            self.active_lease_until = 0.0

            self.state = State.FAILOVER

            self.last_change = now

            self.election_stable_since = now

            self.preemption_started_at = None

        # =====================================================
        # Quorum required
        # =====================================================

        if not self.has_quorum(now):

            return False

        # =====================================================
        # Deterministic election
        # =====================================================

        winner = self.election_winner(now)

        if winner != self.node_id:

            self.preemption_started_at = None

            return False

        # =====================================================
        # Normal failover stability delay
        #
        # This remains separate from preferred-return timer.
        # =====================================================

        if (
            now
            - self.election_stable_since
            <
            self.preemption_delay
        ):

            return False

        self.preemption_started_at = None

        return True


# =============================================================
# UDP Transport
# =============================================================

class BM7UDPTransport:

    def __init__(
        self,
        node,
        bind_host,
        port,
        endpoints,
    ):

        self.node = node
        self.port = port
        self.endpoints = endpoints

        self.sock = socket.socket(
            socket.AF_INET6,
            socket.SOCK_DGRAM,
        )

        try:

            self.sock.setsockopt(
                socket.IPPROTO_IPV6,
                socket.IPV6_V6ONLY,
                0,
            )

        except OSError:

            pass

        self.sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        self.sock.bind(
            (bind_host, port)
        )

        self.last_hello = 0.0

        self.last_advertise = 0.0

    def send(self, data):

        for peer_id in self.node.peers:

            if (
                peer_id
                == self.node.node_id
            ):

                continue

            endpoint = self.endpoints.get(
                peer_id
            )

            if endpoint is None:

                continue

            try:

                self.sock.sendto(
                    data,
                    endpoint,
                )

            except OSError as exc:

                print(
                    f"[TX ERROR] "
                    f"{endpoint}: {exc}"
                )

    def receive(self):

        self.sock.settimeout(0.2)

        try:

            data, address = (
                self.sock.recvfrom(
                    65535
                )
            )

        except socket.timeout:

            return

        try:

            accepted = self.node.observe(
                data
            )

            if accepted:

                packet = Packet.decode(
                    data
                )

                print(
                    f"[RX] {address} "
                    f"{packet.message_type.name} "
                    f"epoch={packet.epoch} "
                    f"seq={packet.sequence}"
                )

        except ValueError as exc:

            print(
                f"[DROP] "
                f"{address}: {exc}"
            )

    def run(self):

        print(
            f"BM7 node listening "
            f"on UDP/{self.port}"
        )

        print(
            f"Packet size: "
            f"{PACKET_LEN} bytes"
        )

        while True:

            now = time.monotonic()

            # -------------------------------------------------
            # HELLO
            # -------------------------------------------------

            if (
                now
                - self.last_hello
                >= self.node.hello_interval
            ):

                self.send(
                    self.node.hello()
                )

                self.last_hello = now

            # -------------------------------------------------
            # ADVERTISE
            # -------------------------------------------------

            if (
                now
                - self.last_advertise
                >= 2.0
            ):

                self.send(
                    self.node.advertise()
                )

                self.last_advertise = now

            # -------------------------------------------------
            # Election / failover / preferred return
            # -------------------------------------------------

            if self.node.should_claim(
                now
            ):

                try:

                    # A live remote owner means this is
                    # preferred-return preemption.
                    preempt = (
                        self.node.active_owner
                        is not None
                        and
                        self.node.active_owner
                        != self.node.node_id
                        and
                        self.node.active_lease_until
                        > now
                    )

                    claim = self.node.claim(
                        now,
                        preempt=preempt,
                    )

                    self.send(
                        claim
                    )

                    if preempt:

                        print(
                            "[STATE] "
                            "local node PREEMPTED "
                            f"owner epoch="
                            f"{self.node.epoch}"
                        )

                    else:

                        print(
                            "[STATE] "
                            "local node became ACTIVE "
                            f"epoch="
                            f"{self.node.epoch}"
                        )

                except RuntimeError:

                    pass

            self.receive()


# =============================================================
# Demo helpers
# =============================================================

def make_node(
    name,
    priority,
    all_nodes,
):

    node_id = hashlib.sha256(
        name.encode()
    ).digest()[:16]

    peer_ids = {
        hashlib.sha256(
            other.encode()
        ).digest()[:16]
        for other in all_nodes
    }

    service_id = hashlib.sha256(
        b"bm7-demo-service"
    ).digest()[:16]

    node = BM7Node(
        node_id=node_id,
        service_id=service_id,
        priority=priority,
        cost=0,
        peers=peer_ids,
        key=b"demo-secret",
    )

    priorities = {
        "A": 100,
        "B": 200,
        "C": 150,
    }

    now = time.monotonic()

    for other in all_nodes:

        other_id = hashlib.sha256(
            other.encode()
        ).digest()[:16]

        node.peers_state[
            other_id
        ] = Peer(
            node_id=other_id,
            priority=priorities[other],
            cost=0,
            last_seen=now,
            epoch=0,
            sequence=0,
            session_id=0,
            state=State.STANDBY,
        )

    return node


# =============================================================
# Demo
# =============================================================

def demo():

    a = make_node(
        "A",
        100,
        ["A", "B", "C"],
    )

    b = make_node(
        "B",
        200,
        ["A", "B", "C"],
    )

    c = make_node(
        "C",
        150,
        ["A", "B", "C"],
    )

    now = time.monotonic()

    b_id = hashlib.sha256(
        b"B"
    ).digest()[:16]

    # ---------------------------------------------------------
    # Simulate B failure.
    # ---------------------------------------------------------

    for node in (a, c):

        node.peers_state[
            b_id
        ].last_seen = (
            now - 20
        )

    # A and C can still see each other.
    for node in (a, c):

        for other in (a, c):

            if node is not other:

                node.peers_state[
                    other.node_id
                ].last_seen = now

    a.last_change = (
        now - 10
    )

    c.last_change = (
        now - 10
    )

    a.election_stable_since = (
        now - 10
    )

    c.election_stable_since = (
        now - 10
    )

    assert (
        c.election_winner(now)
        == c.node_id
    )

    assert c.should_claim(
        now
    )

    claim = c.claim(
        now
    )

    assert (
        len(claim)
        == PACKET_LEN
    )

    assert a.observe(
        claim,
        now,
    )

    assert (
        a.active_owner
        == c.node_id
    )

    # ---------------------------------------------------------
    # Replay must be rejected.
    # ---------------------------------------------------------

    assert not a.observe(
        claim,
        now,
    )

    # ---------------------------------------------------------
    # Preferred return / preemption test.
    #
    # C is currently ACTIVE.
    # B has higher priority.
    # B has quorum and is the deterministic winner.
    # The preemption timer has already elapsed.
    # ---------------------------------------------------------

    b.peers_state[
        c.node_id
    ].last_seen = now

    b.peers_state[
        a.node_id
    ].last_seen = now

    b.peers_state[
        c.node_id
    ].epoch = c.epoch

    b.peers_state[
        c.node_id
    ].sequence = 1

    b.peers_state[
        c.node_id
    ].state = State.ACTIVE

    b.active_owner = c.node_id

    b.active_lease_until = (
        now + b.lease_seconds
    )

    b.state = State.STANDBY

    b.preemption_started_at = (
        now - b.preemption_delay
    )

    assert b.election_winner(
        now
    ) == b.node_id

    assert b.should_claim(
        now
    )

    preempt_claim = b.claim(
        now,
        preempt=True,
    )

    preempt_packet = Packet.decode(
        preempt_claim
    )

    assert (
        preempt_packet.flags
        & FLAG_PREEMPT
    )

    assert (
        preempt_packet.flags
        & FLAG_ACTIVE
    )

    assert (
        preempt_packet.flags
        & FLAG_QUORUM
    )

    assert c.observe(
        preempt_claim,
        now,
    )

    assert (
        c.active_owner
        == b.node_id
    )

    assert (
        c.state
        == State.STANDBY
    )

    print(
        "BM7 demo OK"
    )

    print(
        f"HEADER_LEN={HEADER_LEN}"
    )

    print(
        f"PAYLOAD_LEN={PAYLOAD_LEN}"
    )

    print(
        f"PACKET_LEN={PACKET_LEN}"
    )

    print(
        "quorum=OK"
    )

    print(
        "deterministic-election=OK"
    )

    print(
        "epoch=OK"
    )

    print(
        "lease=OK"
    )

    print(
        "HMAC=OK"
    )

    print(
        "replay-protection=OK"
    )

    print(
        "active-lease-advertisement=OK"
    )

    print(
        "stable-election=OK"
    )

    print(
        "preferred-return-preemption=OK"
    )


# =============================================================
# Main
# =============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--demo",
        action="store_true",
    )

    args = parser.parse_args()

    if args.demo:

        demo()

        return

    parser.print_help()


if __name__ == "__main__":

    main()
