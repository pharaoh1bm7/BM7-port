#!/usr/bin/env python3
"""
BM7 UDP interoperability runner.

This program provides real UDP transport for the BM7 v1 wire format.
It intentionally accepts an administrator-selected lab port because
UDP/4707 must not be used before IANA assignment.

Example:

Node A:
python3 reference/python/bm7_udp.py 
--node A 
--bind 0.0.0.0 
--port 55000 
--peers B=198.51.100.20:55000,C=203.0.113.30:55000 
--priority 100

Node B:
python3 reference/python/bm7_udp.py 
--node B 
--bind 0.0.0.0 
--port 55000 
--peers A=192.0.2.10:55000,C=203.0.113.30:55000 
--priority 200
"""

from **future** import annotations

import argparse
import hashlib
import hmac
import socket
import struct
import time
from dataclasses import dataclass

MAGIC = b"B7"
VERSION = 1
AUTH_LEN = 32

HEADER_FMT = "!2sBBHHHQQQ16sI32s"
HEADER_LEN = struct.calcsize(HEADER_FMT)

PAYLOAD_FMT = "!16sIIB3s"
PAYLOAD_LEN = struct.calcsize(PAYLOAD_FMT)

MSG_HELLO = 1
MSG_ADVERTISE = 2
MSG_CLAIM = 3
MSG_ACK = 4
MSG_RELEASE = 5
MSG_ERROR = 6

STATE_INIT = 0
STATE_DISCOVERING = 1
STATE_STANDBY = 2
STATE_ACTIVE = 3
STATE_FAILOVER = 4
STATE_RECOVERY = 5

FLAG_ACTIVE = 1
FLAG_STANDBY = 2
FLAG_RECOVERING = 4
FLAG_PREEMPT = 8
FLAG_QUORUM = 16

@dataclass
class Packet:
message_type: int
flags: int
session_id: int
epoch: int
sequence: int
sender_id: bytes
lease_ms: int
payload: bytes
tag: bytes

```
def header_without_tag(self) -> bytes:
    return struct.pack(
        HEADER_FMT,
        MAGIC,
        VERSION,
        self.message_type,
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

def compute_tag(self, key: bytes) -> bytes:
    return hmac.new(
        key,
        self.header_without_tag() + self.payload,
        hashlib.sha256,
    ).digest()

def encode(self, key: bytes) -> bytes:
    tag = self.compute_tag(key)

    header = struct.pack(
        HEADER_FMT,
        MAGIC,
        VERSION,
        self.message_type,
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

    return header + self.payload

@classmethod
def decode(cls, data: bytes) -> "Packet":
    if len(data) < HEADER_LEN:
        raise ValueError("packet shorter than BM7 header")

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

    if magic != MAGIC:
        raise ValueError("invalid BM7 magic")

    if version != VERSION:
        raise ValueError("unsupported BM7 version")

    if header_length != HEADER_LEN:
        raise ValueError("invalid header length")

    if payload_length != len(data) - HEADER_LEN:
        raise ValueError("invalid payload length")

    if not 1 <= message_type <= MSG_ERROR:
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
```

@dataclass
class Peer:
name: str
host: str
port: int
node_id: bytes
priority: int

class BM7UDPNode:

```
def __init__(
    self,
    name: str,
    bind_host: str,
    bind_port: int,
    priority: int,
    peers: list[Peer],
    key: bytes,
    service_id: bytes,
):
    self.name = name
    self.node_id = hashlib.sha256(name.encode()).digest()[:16]

    self.bind_host = bind_host
    self.bind_port = bind_port

    self.priority = priority
    self.peers = peers
    self.key = key
    self.service_id = service_id

    self.session_id = int.from_bytes(
        hashlib.sha256(
            self.node_id + str(time.time_ns()).encode()
        ).digest()[:8],
        "big",
    )

    self.epoch = 0
    self.sequence = 0
    self.state = STATE_INIT

    self.last_seen: dict[bytes, float] = {}
    self.last_seq: dict[bytes, int] = {}
    self.peer_epochs: dict[bytes, int] = {}

    self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

    # IPv6 socket with dual-stack support where available.
    try:
        self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    except OSError:
        pass

    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    self.sock.bind((bind_host, bind_port))

def payload(self) -> bytes:
    return struct.pack(
        PAYLOAD_FMT,
        self.service_id,
        self.priority,
        0,
        self.state,
        b"\0\0\0",
    )

def make_packet(
    self,
    message_type: int,
    lease_ms: int = 0,
    flags: int = 0,
) -> bytes:

    self.sequence += 1

    packet = Packet(
        message_type=message_type,
        flags=flags,
        session_id=self.session_id,
        epoch=self.epoch,
        sequence=self.sequence,
        sender_id=self.node_id,
        lease_ms=lease_ms,
        payload=self.payload(),
        tag=b"",
    )

    return packet.encode(self.key)

def send_to_peer(
    self,
    peer: Peer,
    packet: bytes,
) -> None:

    try:
        self.sock.sendto(packet, (peer.host, peer.port))
        print(
            f"[TX] {self.name} -> {peer.name} "
            f"{peer.host}:{peer.port} "
            f"{len(packet)} bytes"
        )
    except OSError as exc:
        print(
            f"[TX-ERROR] {self.name} -> {peer.name}: {exc}"
        )

def broadcast(self, packet: bytes) -> None:
    for peer in self.peers:
        self.send_to_peer(peer, packet)

def send_hello(self) -> None:
    packet = self.make_packet(MSG_HELLO)
    self.broadcast(packet)

def send_advertise(self) -> None:
    packet = self.make_packet(MSG_ADVERTISE)
    self.broadcast(packet)

def send_claim(self) -> None:
    self.epoch += 1
    self.state = STATE_ACTIVE

    packet = self.make_packet(
        MSG_CLAIM,
        lease_ms=10000,
        flags=FLAG_ACTIVE | FLAG_QUORUM,
    )

    self.broadcast(packet)

    print(
        f"[CLAIM] node={self.name} epoch={self.epoch}"
    )

def peer_name(self, node_id: bytes) -> str:
    if node_id == self.node_id:
        return self.name

    for peer in self.peers:
        if peer.node_id == node_id:
            return peer.name

    return node_id.hex()[:16]

def receive_once(self, timeout: float = 0.2) -> None:
    self.sock.settimeout(timeout)

    try:
        data, address = self.sock.recvfrom(65535)
    except socket.timeout:
        return

    try:
        packet = Packet.decode(data)

        expected = packet.compute_tag(self.key)

        if not hmac.compare_digest(
            packet.tag,
            expected,
        ):
            raise ValueError("authentication failure")

        if packet.sender_id == self.node_id:
            return

        now = time.monotonic()

        previous_epoch = self.peer_epochs.get(
            packet.sender_id,
            0,
        )

        previous_sequence = self.last_seq.get(
            packet.sender_id,
            0,
        )

        if packet.epoch < previous_epoch:
            raise ValueError("stale epoch")

        if (
            packet.epoch == previous_epoch
            and packet.sequence <= previous_sequence
        ):
            raise ValueError("replay/duplicate")

        self.peer_epochs[packet.sender_id] = packet.epoch
        self.last_seq[packet.sender_id] = packet.sequence
        self.last_seen[packet.sender_id] = now

        sender = self.peer_name(packet.sender_id)

        names = {
            MSG_HELLO: "HELLO",
            MSG_ADVERTISE: "ADVERTISE",
            MSG_CLAIM: "CLAIM",
            MSG_ACK: "ACK",
            MSG_RELEASE: "RELEASE",
            MSG_ERROR: "ERROR",
        }

        print(
            f"[RX] {self.name} <- {sender} "
            f"{names[packet.message_type]} "
            f"epoch={packet.epoch} "
            f"seq={packet.sequence} "
            f"from={address}"
        )

    except ValueError as exc:
        print(
            f"[DROP] {self.name} rejected packet "
            f"from={address}: {exc}"
        )

def run(self) -> None:
    print()
    print("BM7 Public-Network Interoperability Runner")
    print("--------------------------------------------")
    print(f"Node:     {self.name}")
    print(f"Node ID:  {self.node_id.hex()}")
    print(f"Bind:     [{self.bind_host}]:{self.bind_port}")
    print(f"Priority: {self.priority}")
    print()
    print(
        "NOTE: this port is an administrator-selected "
        "laboratory port."
    )
    print(
        "Do NOT describe it as an IANA-assigned BM7 port."
    )
    print()

    last_hello = 0.0
    last_advertise = 0.0

    while True:
        now = time.monotonic()

        if now - last_hello >= 2.0:
            self.send_hello()
            last_hello = now

        if now - last_advertise >= 10.0:
            self.send_advertise()
            last_advertise = now

        self.receive_once(0.2)
```

def parse_peer(value: str) -> Peer:
"""
Format:

```
    NAME=HOST:PORT:PRIORITY
"""

name, endpoint, priority = value.split("=", 1)[0], value.split("=", 1)[1].rsplit(":", 1)[0], value.rsplit(":", 1)[1]

host, port = endpoint.rsplit(":", 1)

node_id = hashlib.sha256(
    name.encode()
).digest()[:16]

return Peer(
    name=name,
    host=host,
    port=int(port),
    node_id=node_id,
    priority=int(priority),
)
```

def main() -> None:
parser = argparse.ArgumentParser()

```
parser.add_argument(
    "--node",
    required=True,
)

parser.add_argument(
    "--bind",
    default="::",
)

parser.add_argument(
    "--port",
    type=int,
    required=True,
)

parser.add_argument(
    "--priority",
    type=int,
    required=True,
)

parser.add_argument(
    "--peer",
    action="append",
    default=[],
    help="NAME=HOST:PORT:PRIORITY",
)

parser.add_argument(
    "--secret",
    default="bm7-lab-shared-secret",
)

parser.add_argument(
    "--service",
    default="bm7-public-lab",
)

parser.add_argument(
    "--claim",
    action="store_true",
)

args = parser.parse_args()

peers = [
    parse_peer(value)
    for value in args.peer
]

service_id = hashlib.sha256(
    args.service.encode()
).digest()[:16]

node = BM7UDPNode(
    name=args.node,
    bind_host=args.bind,
    bind_port=args.port,
    priority=args.priority,
    peers=peers,
    key=args.secret.encode(),
    service_id=service_id,
)

if args.claim:
    node.send_claim()

node.run()
```

if **name** == "**main**":
main()
