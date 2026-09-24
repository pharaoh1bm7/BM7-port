from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import hmac
import ipaddress
import json
import time
from typing import Dict, Optional


# ============================================================
# BM7 Protocol Constants
# ============================================================

BM7_VERSION = 1
BM7_PORT = 4707

LEASE_SECONDS = 15
TIMESTAMP_WINDOW_SECONDS = 30


# ============================================================
# BM7 Node Roles
# ============================================================

class Role(str, Enum):
    PRIMARY = "PRIMARY"
    STANDBY = "STANDBY"
    SERVING = "SERVING"
    RETURNING = "RETURNING"
    ISOLATED = "ISOLATED"


# ============================================================
# BM7 Message Types
# ============================================================

class MessageType(str, Enum):
    HELLO = "HELLO"
    HELLO_ACK = "HELLO_ACK"

    HEARTBEAT = "HEARTBEAT"
    HEARTBEAT_ACK = "HEARTBEAT_ACK"

    STATE_DIGEST = "STATE_DIGEST"
    STATE_REQUEST = "STATE_REQUEST"
    STATE_RESPONSE = "STATE_RESPONSE"

    FAILURE_CLAIM = "FAILURE_CLAIM"
    FAILURE_CLAIM_ACK = "FAILURE_CLAIM_ACK"

    ROUTE_CLAIM = "ROUTE_CLAIM"
    ROUTE_CLAIM_ACK = "ROUTE_CLAIM_ACK"

    SESSION_CLAIM = "SESSION_CLAIM"
    SESSION_CLAIM_ACK = "SESSION_CLAIM_ACK"

    LEASE_RENEW = "LEASE_RENEW"
    LEASE_ACK = "LEASE_ACK"

    RETURN_PREPARE = "RETURN_PREPARE"
    RETURN_READY = "RETURN_READY"
    RETURN_COMMIT = "RETURN_COMMIT"
    RETURN_ACK = "RETURN_ACK"

    ERROR = "ERROR"


# ============================================================
# BM7 Error Codes
# ============================================================

class ErrorCode(str, Enum):
    AUTH_FAIL = "AUTH_FAIL"
    VERSION_FAIL = "VERSION_FAIL"
    WRONG_DESTINATION = "WRONG_DESTINATION"
    UNKNOWN_PEER = "UNKNOWN_PEER"
    REPLAY = "REPLAY"
    TIMESTAMP_EXPIRED = "TIMESTAMP_EXPIRED"
    STALE_EPOCH = "STALE_EPOCH"
    EXPIRED_LEASE = "EXPIRED_LEASE"
    UNAUTHORIZED = "UNAUTHORIZED"
    NO_QUORUM = "NO_QUORUM"
    UNKNOWN_SERVICE = "UNKNOWN_SERVICE"
    INVALID_CLAIM = "INVALID_CLAIM"
    INVALID_STATE = "INVALID_STATE"
    BAD_MESSAGE = "BAD_MESSAGE"


# ============================================================
# Service State
# ============================================================

@dataclass
class ServiceState:
    service_id: str
    prefix: str
    owner: str
    sessions: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "service_id": self.service_id,
            "prefix": self.prefix,
            "owner": self.owner,
            "sessions": dict(self.sessions),
        }


# ============================================================
# BM7 Node
# ============================================================

@dataclass
class Node:

    node_id: str
    peers: set
    secret: bytes

    epoch: int = 0
    role: Role = Role.STANDBY
    lease_until: float = 0
    seq: int = 0

    services: Dict[str, ServiceState] = field(
        default_factory=dict
    )

    # Last accepted sequence number from every peer.
    peer_last_seq: Dict[str, int] = field(
        default_factory=dict
    )

    # Last heartbeat received from every peer.
    peer_last_seen: Dict[str, float] = field(
        default_factory=dict
    )

    # Peers that approved a failure claim.
    claim_votes: Dict[str, set] = field(
        default_factory=dict
    )

    # ========================================================
    # Authentication
    # ========================================================

    def _canonical(self, message: dict) -> bytes:

        return json.dumps(
            message,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def sign(self, message: dict) -> str:

        return hmac.new(
            self.secret,
            self._canonical(message),
            hashlib.sha256,
        ).hexdigest()

    def verify(
        self,
        message: dict,
        mac: str,
    ) -> bool:

        expected = self.sign(message)

        return hmac.compare_digest(
            expected,
            mac,
        )

    # ========================================================
    # Message Creation
    # ========================================================

    def packet(
        self,
        message_type: MessageType,
        peer: str,
        **payload,
    ):

        if peer not in self.peers:
            raise ValueError(
                ErrorCode.UNKNOWN_PEER.value
            )

        self.seq += 1

        message = {
            "v": BM7_VERSION,
            "type": message_type.value,
            "src": self.node_id,
            "dst": peer,
            "epoch": self.epoch,
            "seq": self.seq,
            "ts": int(time.time()),
            "payload": payload,
        }

        mac = self.sign(message)

        return message, mac

    # ========================================================
    # Message Validation
    # ========================================================

    def validate_message(
        self,
        message: dict,
        mac: str,
        now: Optional[float] = None,
    ):

        if now is None:
            now = time.time()

        required = {
            "v",
            "type",
            "src",
            "dst",
            "epoch",
            "seq",
            "ts",
            "payload",
        }

        if not required.issubset(message):
            raise ValueError(
                ErrorCode.BAD_MESSAGE.value
            )

        if message["v"] != BM7_VERSION:
            raise ValueError(
                ErrorCode.VERSION_FAIL.value
            )

        source = message["src"]

        if source not in self.peers:
            raise ValueError(
                ErrorCode.UNKNOWN_PEER.value
            )

        if message["dst"] != self.node_id:
            raise ValueError(
                ErrorCode.WRONG_DESTINATION.value
            )

        if not self.verify(message, mac):
            raise ValueError(
                ErrorCode.AUTH_FAIL.value
            )

        timestamp = int(message["ts"])

        if abs(now - timestamp) > TIMESTAMP_WINDOW_SECONDS:
            raise ValueError(
                ErrorCode.TIMESTAMP_EXPIRED.value
            )

        sequence = int(message["seq"])

        previous = self.peer_last_seq.get(
            source,
            0,
        )

        if sequence <= previous:
            raise ValueError(
                ErrorCode.REPLAY.value
            )

        message_epoch = int(
            message["epoch"]
        )

        if message_epoch < self.epoch:
            raise ValueError(
                ErrorCode.STALE_EPOCH.value
            )

        self.peer_last_seq[
            source
        ] = sequence

        self.peer_last_seen[
            source
        ] = timestamp

        self.epoch = max(
            self.epoch,
            message_epoch,
        )

    # ========================================================
    # HELLO
    # ========================================================

    def hello(self, peer: str):

        return self.packet(
            MessageType.HELLO,
            peer,
            capabilities=[
                "HEARTBEAT",
                "STATE_SYNC",
                "FAILOVER",
                "ROUTE_CLAIM",
                "SESSION_CLAIM",
                "LEASE",
                "HANDOVER",
            ],
        )

    def receive_hello(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        return self.packet(
            MessageType.HELLO_ACK,
            message["src"],
        )

    # ========================================================
    # HEARTBEAT
    # ========================================================

    def heartbeat(self, peer: str):

        return self.packet(
            MessageType.HEARTBEAT,
            peer,
        )

    def receive_heartbeat(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        self.peer_last_seen[
            message["src"]
        ] = time.time()

        return self.packet(
            MessageType.HEARTBEAT_ACK,
            message["src"],
        )

    def receive_heartbeat_ack(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        self.peer_last_seen[
            message["src"]
        ] = time.time()

    # ========================================================
    # Failure Detection
    # ========================================================

    def primary_alive(
        self,
        primary_id: str,
        now: Optional[float] = None,
    ):

        if now is None:
            now = time.time()

        last_seen = self.peer_last_seen.get(
            primary_id
        )

        if last_seen is None:
            return False

        return (
            now - last_seen
            <= TIMESTAMP_WINDOW_SECONDS
        )

    # ========================================================
    # Service Registration
    # ========================================================

    def register_service(
        self,
        service_id: str,
        prefix: str,
    ):

        network = ipaddress.ip_network(
            prefix,
            strict=False,
        )

        self.services[
            service_id
        ] = ServiceState(
            service_id=service_id,
            prefix=str(network),
            owner=self.node_id,
        )

    # ========================================================
    # STATE DIGEST
    # ========================================================

    def state_digest(self):

        state = {
            "epoch": self.epoch,
            "role": self.role.value,
            "services": {
                service_id: service.to_dict()
                for service_id, service
                in sorted(
                    self.services.items()
                )
            },
        }

        encoded = json.dumps(
            state,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()

        return hashlib.sha256(
            encoded
        ).hexdigest()

    def state_digest_message(
        self,
        peer: str,
    ):

        return self.packet(
            MessageType.STATE_DIGEST,
            peer,
            digest=self.state_digest(),
        )

    # ========================================================
    # STATE REQUEST
    # ========================================================

    def state_request(
        self,
        peer: str,
    ):

        return self.packet(
            MessageType.STATE_REQUEST,
            peer,
        )

    def receive_state_request(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        return self.packet(
            MessageType.STATE_RESPONSE,
            message["src"],
            state=self.export_state(),
        )

    # ========================================================
    # STATE RESPONSE
    # ========================================================

    def export_state(self):

        return {
            "epoch": self.epoch,
            "role": self.role.value,
            "services": {
                service_id: service.to_dict()
                for service_id, service
                in self.services.items()
            },
        }

    def receive_state_response(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        state = message[
            "payload"
        ].get("state")

        if not state:
            raise ValueError(
                ErrorCode.BAD_MESSAGE.value
            )

        incoming_epoch = int(
            state["epoch"]
        )

        if incoming_epoch < self.epoch:
            raise ValueError(
                ErrorCode.STALE_EPOCH.value
            )

        new_services = {}

        for service_id, raw in state[
            "services"
        ].items():

            new_services[
                service_id
            ] = ServiceState(
                service_id=raw[
                    "service_id"
                ],
                prefix=raw["prefix"],
                owner=raw["owner"],
                sessions=dict(
                    raw.get(
                        "sessions",
                        {}
                    )
                ),
            )

        self.services = new_services

        self.epoch = incoming_epoch

    # ========================================================
    # FAILURE CLAIM
    # ========================================================

    def failure_claim(
        self,
        peer: str,
        failed_primary: str,
    ):

        if failed_primary not in self.peers:
            raise ValueError(
                ErrorCode.UNKNOWN_PEER.value
            )

        return self.packet(
            MessageType.FAILURE_CLAIM,
            peer,
            failed_primary=failed_primary,
            candidate=self.node_id,
            proposed_epoch=self.epoch + 1,
        )

    def receive_failure_claim(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        payload = message[
            "payload"
        ]

        failed_primary = payload[
            "failed_primary"
        ]

        candidate = payload[
            "candidate"
        ]

        proposed_epoch = int(
            payload[
                "proposed_epoch"
            ]
        )

        if candidate != message["src"]:
            raise ValueError(
                ErrorCode.INVALID_CLAIM.value
            )

        if failed_primary == self.node_id:
            raise ValueError(
                ErrorCode.INVALID_CLAIM.value
            )

        if self.primary_alive(
            failed_primary
        ):
            return self.packet(
                MessageType.FAILURE_CLAIM_ACK,
                message["src"],
                status="REJECTED",
                reason="PRIMARY_ALIVE",
            )

        if proposed_epoch <= self.epoch:
            return self.packet(
                MessageType.FAILURE_CLAIM_ACK,
                message["src"],
                status="REJECTED",
                reason="STALE_EPOCH",
            )

        return self.packet(
            MessageType.FAILURE_CLAIM_ACK,
            message["src"],
            status="ACCEPTED",
            failed_primary=failed_primary,
            candidate=candidate,
            epoch=proposed_epoch,
        )

    # ========================================================
    # ROUTE CLAIM
    # ========================================================

    def route_claim(
        self,
        peer: str,
        service_id: str,
    ):

        service = self.services.get(
            service_id
        )

        if service is None:
            raise ValueError(
                ErrorCode.UNKNOWN_SERVICE.value
            )

        return self.packet(
            MessageType.ROUTE_CLAIM,
            peer,
            service_id=service_id,
            prefix=service.prefix,
            owner=self.node_id,
        )

    def receive_route_claim(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        payload = message[
            "payload"
        ]

        service_id = payload[
            "service_id"
        ]

        service = self.services.get(
            service_id
        )

        if service is None:
            raise ValueError(
                ErrorCode.UNKNOWN_SERVICE.value
            )

        if payload["prefix"] != service.prefix:
            raise ValueError(
                ErrorCode.INVALID_CLAIM.value
            )

        return self.packet(
            MessageType.ROUTE_CLAIM_ACK,
            message["src"],
            service_id=service_id,
            owner=payload["owner"],
            status="ACCEPTED",
        )

    # ========================================================
    # SESSION CLAIM
    # ========================================================

    def session_claim(
        self,
        peer: str,
        service_id: str,
    ):

        service = self.services.get(
            service_id
        )

        if service is None:
            raise ValueError(
                ErrorCode.UNKNOWN_SERVICE.value
            )

        return self.packet(
            MessageType.SESSION_CLAIM,
            peer,
            service_id=service_id,
            sessions=service.sessions,
            owner=self.node_id,
        )

    def receive_session_claim(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        payload = message[
            "payload"
        ]

        service_id = payload[
            "service_id"
        ]

        service = self.services.get(
            service_id
        )

        if service is None:
            raise ValueError(
                ErrorCode.UNKNOWN_SERVICE.value
            )

        service.sessions.update(
            payload.get(
                "sessions",
                {}
            )
        )

        return self.packet(
            MessageType.SESSION_CLAIM_ACK,
            message["src"],
            service_id=service_id,
            status="ACCEPTED",
        )

    # ========================================================
    # TAKEOVER
    # ========================================================

    def takeover(
        self,
        failed_primary: str,
        available_nodes: set,
        now: Optional[float] = None,
    ):

        if now is None:
            now = time.time()

        # Reference quorum policy:
        # at least two trusted nodes are required.
        trusted_available = {
            node
            for node in available_nodes
            if node in self.peers
            or node == self.node_id
        }

        if len(trusted_available) < 2:
            raise ValueError(
                ErrorCode.NO_QUORUM.value
            )

        if failed_primary not in self.peers:
            raise ValueError(
                ErrorCode.UNKNOWN_PEER.value
            )

        if self.primary_alive(
            failed_primary,
            now,
        ):
            raise ValueError(
                ErrorCode.INVALID_CLAIM.value
            )

        # Ownership generation changes.
        self.epoch += 1

        self.role = Role.SERVING

        self.lease_until = (
            now + LEASE_SECONDS
        )

        for service in self.services.values():
            service.owner = self.node_id

        return self.epoch

    # ========================================================
    # LEASE
    # ========================================================

    def lease_renew(
        self,
        peer: str,
    ):

        if self.role != Role.SERVING:
            raise ValueError(
                ErrorCode.INVALID_STATE.value
            )

        if time.time() >= self.lease_until:
            raise ValueError(
                ErrorCode.EXPIRED_LEASE.value
            )

        return self.packet(
            MessageType.LEASE_RENEW,
            peer,
            lease_until=int(
                time.time()
                + LEASE_SECONDS
            ),
        )

    def receive_lease_renew(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        if self.role != Role.SERVING:
            return self.packet(
                MessageType.ERROR,
                message["src"],
                code=ErrorCode.INVALID_STATE.value,
            )

        if time.time() >= self.lease_until:
            return self.packet(
                MessageType.ERROR,
                message["src"],
                code=ErrorCode.EXPIRED_LEASE.value,
            )

        self.lease_until = (
            time.time()
            + LEASE_SECONDS
        )

        return self.packet(
            MessageType.LEASE_ACK,
            message["src"],
            lease_until=int(
                self.lease_until
            ),
        )

    def renew(
        self,
        now: Optional[float] = None,
    ):

        if now is None:
            now = time.time()

        if self.role != Role.SERVING:
            raise ValueError(
                ErrorCode.INVALID_STATE.value
            )

        if now >= self.lease_until:
            self.role = Role.ISOLATED

            raise ValueError(
                ErrorCode.EXPIRED_LEASE.value
            )

        self.lease_until = (
            now + LEASE_SECONDS
        )

    # ========================================================
    # CONTROLLED RETURN
    # ========================================================

    def return_prepare(
        self,
        primary_id: str,
    ):

        if self.role != Role.SERVING:
            raise ValueError(
                ErrorCode.INVALID_STATE.value
            )

        if time.time() >= self.lease_until:
            raise ValueError(
                ErrorCode.EXPIRED_LEASE.value
            )

        return self.packet(
            MessageType.RETURN_PREPARE,
            primary_id,
            primary_id=primary_id,
            serving_id=self.node_id,
        )

    def receive_return_prepare(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        if self.role not in {
            Role.STANDBY,
            Role.PRIMARY,
        }:
            raise ValueError(
                ErrorCode.INVALID_STATE.value
            )

        # The returning original primary has
        # already synchronized its state.
        return self.packet(
            MessageType.RETURN_READY,
            message["src"],
            primary_id=self.node_id,
        )

    def return_commit(
        self,
        primary_id: str,
    ):

        return self.packet(
            MessageType.RETURN_COMMIT,
            primary_id,
            primary_id=primary_id,
            serving_id=self.node_id,
        )

    def receive_return_commit(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        primary_id = message[
            "payload"
        ]["primary_id"]

        for service in self.services.values():
            service.owner = primary_id

        self.role = Role.STANDBY
        self.lease_until = 0

        return self.packet(
            MessageType.RETURN_ACK,
            primary_id,
            status="COMMITTED",
        )

    # ========================================================
    # Message Dispatcher
    # ========================================================

    def receive(
        self,
        message: dict,
        mac: str,
    ):

        message_type = message.get(
            "type"
        )

        handlers = {
            MessageType.HELLO.value:
                self.receive_hello,

            MessageType.HEARTBEAT.value:
                self.receive_heartbeat,

            MessageType.HEARTBEAT_ACK.value:
                self.receive_heartbeat_ack,

            MessageType.STATE_REQUEST.value:
                self.receive_state_request,

            MessageType.STATE_RESPONSE.value:
                self.receive_state_response,

            MessageType.FAILURE_CLAIM.value:
                self.receive_failure_claim,

            MessageType.ROUTE_CLAIM.value:
                self.receive_route_claim,

            MessageType.SESSION_CLAIM.value:
                self.receive_session_claim,

            MessageType.LEASE_RENEW.value:
                self.receive_lease_renew,

            MessageType.RETURN_PREPARE.value:
                self.receive_return_prepare,

            MessageType.RETURN_COMMIT.value:
                self.receive_return_commit,
        }

        handler = handlers.get(
            message_type
        )

        if handler is None:

            self.validate_message(
                message,
                mac,
            )

            return self.packet(
                MessageType.ERROR,
                message["src"],
                code="UNSUPPORTED_MESSAGE",
            )

        return handler(
            message,
            mac,
        )


# ============================================================
# BM7 Cluster / Quorum
# ============================================================

class Cluster:

    def __init__(
        self,
        nodes,
    ):

        self.nodes = {
            node.node_id: node
            for node in nodes
        }

    def quorum(
        self,
        available,
    ):

        trusted = {
            node_id
            for node_id in available
            if node_id in self.nodes
        }

        return len(trusted) >= 2

    def authorize_takeover(
        self,
        candidate_id: str,
        failed_id: str,
        available,
    ):

        if not self.quorum(
            available
        ):
            raise ValueError(
                ErrorCode.NO_QUORUM.value
            )

        if candidate_id not in self.nodes:
            raise ValueError(
                ErrorCode.UNKNOWN_PEER.value
            )

        if failed_id not in self.nodes:
            raise ValueError(
                ErrorCode.UNKNOWN_PEER.value
            )

        candidate = self.nodes[
            candidate_id
        ]

        return candidate.takeover(
            failed_id,
            set(available),
        )


# ============================================================
# Reference Demonstration
# ============================================================

def demo():

    secret = b"bm7-development-secret"

    a = Node(
        node_id="branch-a",
        peers={
            "branch-b",
            "branch-c",
        },
        secret=secret,
    )

    b = Node(
        node_id="branch-b",
        peers={
            "branch-a",
            "branch-c",
        },
        secret=secret,
    )

    c = Node(
        node_id="branch-c",
        peers={
            "branch-a",
            "branch-b",
        },
        secret=secret,
    )

    # --------------------------------------------------------
    # NORMAL OPERATION
    # --------------------------------------------------------

    b.role = Role.PRIMARY

    b.register_service(
        "customer-net-01",
        "10.20.0.0/24",
    )

    print(
        "=== NORMAL OPERATION ==="
    )

    print(
        "Primary:",
        b.node_id,
    )

    print(
        "Service owner:",
        b.services[
            "customer-net-01"
        ].owner,
    )

    # --------------------------------------------------------
    # HEARTBEAT
    # --------------------------------------------------------

    heartbeat, heartbeat_mac = (
        b.heartbeat(
            "branch-c"
        )
    )

    c.receive_heartbeat(
        heartbeat,
        heartbeat_mac,
    )

    print(
        "Heartbeat: OK"
    )

    # --------------------------------------------------------
    # STATE SYNCHRONIZATION
    # --------------------------------------------------------

    # For the reference simulation we use
    # BM7 messages rather than direct copying.

    state_request, state_request_mac = (
        c.state_request(
            "branch-b"
        )
    )

    state_response = (
        b.receive_state_request(
            state_request,
            state_request_mac,
        )
    )

    c.receive_state_response(
        state_response[0],
        state_response[1],
    )

    print(
        "State synchronization: OK"
    )

    # --------------------------------------------------------
    # FAILURE
    # --------------------------------------------------------

    print(
        "\n=== FAILURE ==="
    )

    # Simulate loss of B heartbeat.
    c.peer_last_seen[
        "branch-b"
    ] = (
        time.time()
        - TIMESTAMP_WINDOW_SECONDS
        - 1
    )

    # A is the second trusted node.
    cluster = Cluster(
        [a, b, c]
    )

    epoch = cluster.authorize_takeover(
        candidate_id="branch-c",
        failed_id="branch-b",
        available={
            "branch-a",
            "branch-c",
        },
    )

    print(
        "Takeover epoch:",
        epoch,
    )

    print(
        "Serving node:",
        c.node_id,
    )

    print(
        "Service owner:",
        c.services[
            "customer-net-01"
        ].owner,
    )

    # --------------------------------------------------------
    # LEASE RENEWAL
    # --------------------------------------------------------

    c.renew()

    print(
        "Temporary lease: ACTIVE"
    )

    # --------------------------------------------------------
    # RECOVERY
    # --------------------------------------------------------

    print(
        "\n=== RECOVERY ==="
    )

    # B returns and receives synchronized state.
    state_request, state_request_mac = (
        b.state_request(
            "branch-c"
        )
    )

    state_response = (
        c.receive_state_request(
            state_request,
            state_request_mac,
        )
    )

    b.receive_state_response(
        state_response[0],
        state_response[1],
    )

    # C begins controlled handback.
    return_prepare, return_prepare_mac = (
        c.return_prepare(
            "branch-b"
        )
    )

    return_ready = (
        b.receive_return_prepare(
            return_prepare,
            return_prepare_mac,
        )
    )

    # B is now synchronized and ready.
    if (
        return_ready[0]["type"]
        != MessageType.RETURN_READY.value
    ):
        raise RuntimeError(
            "RETURN_READY was not received"
        )

    # C commits handback.
    return_commit, return_commit_mac = (
        c.return_commit(
            "branch-b"
        )
    )

    return_ack = (
        b.receive_return_commit(
            return_commit,
            return_commit_mac,
        )
    )

    # Final role state.
    b.role = Role.PRIMARY
    c.role = Role.STANDBY

    print(
        "Return:",
        return_ack[0]["type"],
    )

    print(
        "Primary:",
        b.node_id,
    )

    print(
        "Standby:",
        c.node_id,
    )

    print(
        "Recovered owner:",
        b.services[
            "customer-net-01"
        ].owner,
    )


if __name__ == "__main__":
    demo()
