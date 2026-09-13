from dataclasses import dataclass, field
from enum import Enum
import hashlib
import hmac
import json
import time


BM7_VERSION = 1
BM7_PORT = 4707
LEASE_SECONDS = 15


class Role(str, Enum):
    PRIMARY = "PRIMARY"
    STANDBY = "STANDBY"
    SERVING = "SERVING"
    RETURNING = "RETURNING"
    ISOLATED = "ISOLATED"


@dataclass
class ServiceState:
    service_id: str
    prefix: str
    owner: str
    sessions: dict = field(default_factory=dict)


@dataclass
class Node:
    node_id: str
    peers: set
    secret: bytes

    epoch: int = 0
    role: Role = Role.STANDBY
    lease_until: float = 0
    seq: int = 0

    services: dict = field(default_factory=dict)
    peer_last_seen: dict = field(default_factory=dict)

    def _canonical(self, message):
        return json.dumps(
            message,
            sort_keys=True,
            separators=(",", ":")
        ).encode("utf-8")

    def sign(self, message):
        return hmac.new(
            self.secret,
            self._canonical(message),
            hashlib.sha256
        ).hexdigest()

    def verify(self, message, mac):
        expected = self.sign(message)
        return hmac.compare_digest(
            expected,
            mac
        )

    def packet(self, message_type, peer, **payload):

        self.seq += 1

        message = {
            "v": BM7_VERSION,
            "type": message_type,
            "src": self.node_id,
            "dst": peer,
            "epoch": self.epoch,
            "seq": self.seq,
            "ts": int(time.time()),
            "payload": payload,
        }

        mac = self.sign(message)

        return message, mac

    def heartbeat(self, peer):

        return self.packet(
            "HEARTBEAT",
            peer
        )

    def receive_heartbeat(
        self,
        message,
        mac
    ):

        if not self.verify(message, mac):
            raise ValueError("AUTH_FAIL")

        if message["v"] != BM7_VERSION:
            raise ValueError("VERSION_FAIL")

        if message["dst"] != self.node_id:
            raise ValueError("WRONG_DESTINATION")

        self.peer_last_seen[
            message["src"]
        ] = message["ts"]

        self.epoch = max(
            self.epoch,
            message["epoch"]
        )

        return self.packet(
            "HEARTBEAT_ACK",
            message["src"]
        )

    def register_service(
        self,
        service_id,
        prefix
    ):

        self.services[service_id] = ServiceState(
            service_id=service_id,
            prefix=prefix,
            owner=self.node_id
        )

    def replicate_from(
        self,
        primary,
        peer_id
    ):

        if self.node_id not in primary.peers:
            raise ValueError(
                "UNAUTHORIZED_PEER"
            )

        if peer_id != primary.node_id:
            raise ValueError(
                "INVALID_PRIMARY"
            )

        copied = {}

        for service_id, service in primary.services.items():

            copied[service_id] = ServiceState(
                service_id=service.service_id,
                prefix=service.prefix,
                owner=service.owner,
                sessions=dict(
                    service.sessions
                )
            )

        self.services = copied

        self.epoch = max(
            self.epoch,
            primary.epoch
        )

    def takeover(
        self,
        failed_id,
        now=None
    ):

        now = (
            time.time()
            if now is None
            else now
        )

        if failed_id not in self.peers:
            raise ValueError(
                "UNKNOWN_PRIMARY"
            )

        self.epoch += 1

        self.role = Role.SERVING

        self.lease_until = (
            now + LEASE_SECONDS
        )

        for service in self.services.values():
            service.owner = self.node_id

        return self.epoch

    def renew(
        self,
        now=None
    ):

        now = (
            time.time()
            if now is None
            else now
        )

        if self.role != Role.SERVING:
            raise ValueError(
                "LEASE_INVALID"
            )

        if now > self.lease_until:
            raise ValueError(
                "LEASE_INVALID"
            )

        self.lease_until = (
            now + LEASE_SECONDS
        )

    def prepare_return(
        self,
        primary_id,
        primary,
        now=None
    ):

        now = (
            time.time()
            if now is None
            else now
        )

        if self.role != Role.SERVING:
            raise ValueError(
                "NOT_SERVING"
            )

        if self.lease_until < now:
            raise ValueError(
                "LEASE_EXPIRED"
            )

        if primary_id != primary.node_id:
            raise ValueError(
                "BAD_PRIMARY"
            )

        primary.services = {}

        for service_id, service in self.services.items():

            primary.services[service_id] = ServiceState(
                service_id=service.service_id,
                prefix=service.prefix,
                owner=primary_id,
                sessions=dict(
                    service.sessions
                )
            )

        primary.epoch = max(
            primary.epoch,
            self.epoch
        )

        self.role = Role.RETURNING

        return primary.epoch

    def commit_return(
        self,
        primary_id,
        primary
    ):

        if self.role != Role.RETURNING:
            raise ValueError(
                "NOT_RETURNING"
            )

        if primary.node_id != primary_id:
            raise ValueError(
                "BAD_PRIMARY"
            )

        for service in self.services.values():
            service.owner = primary_id

        self.epoch = max(
            self.epoch,
            primary.epoch
        )

        self.role = Role.STANDBY

        primary.role = Role.PRIMARY

        primary.epoch = self.epoch

        self.lease_until = 0


class Cluster:

    def __init__(self, nodes):

        self.nodes = {
            node.node_id: node
            for node in nodes
        }

    def quorum(self, available):

        return len(
            set(available)
        ) >= 2

    def claim(
        self,
        node_id,
        failed_id,
        available
    ):

        if not self.quorum(available):
            raise ValueError(
                "NO_QUORUM"
            )

        node = self.nodes[node_id]

        return node.takeover(
            failed_id,
            now=100.0
        )


def demo():

    secret = b"bm7-development-secret"

    a = Node(
        node_id="branch-a",
        peers={"branch-b", "branch-c"},
        secret=secret
    )

    b = Node(
        node_id="branch-b",
        peers={"branch-a", "branch-c"},
        secret=secret
    )

    c = Node(
        node_id="branch-c",
        peers={"branch-a", "branch-b"},
        secret=secret
    )

    b.role = Role.PRIMARY

    b.register_service(
        "customer-net-01",
        "10.20.0.0/24"
    )

    c.replicate_from(
        b,
        "branch-b"
    )

    print("=== NORMAL OPERATION ===")
    print("B:", b.role.value)
    print("C:", c.role.value)

    message, mac = c.heartbeat("branch-b")

    b.receive_heartbeat(
        message,
        mac
    )

    print("Heartbeat: OK")

    print("\n=== FAILURE ===")

    cluster = Cluster(
        [a, b, c]
    )

    epoch = cluster.claim(
        "branch-c",
        "branch-b",
        ["branch-a", "branch-c"]
    )

    print("C takeover epoch:", epoch)
    print("C role:", c.role.value)

    print(
        "Service owner:",
        c.services[
            "customer-net-01"
        ].owner
    )

    print("\n=== RECOVERY ===")

    c.prepare_return(
        "branch-b",
        b,
        now=101.0
    )

    c.commit_return(
        "branch-b",
        b
    )

    print("B role:", b.role.value)
    print("C role:", c.role.value)

    print(
        "Recovered owner:",
        b.services[
            "customer-net-01"
        ].owner
    )


if __name__ == "__main__":
    demo()
```
