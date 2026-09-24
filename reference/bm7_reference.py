"""
BM7 Protocol Reference Implementation
=====================================

BM7 is a control-plane protocol for coordinated service ownership,
failover, and controlled handback between network branches.

Reference transport:
    UDP/4707

This implementation intentionally does NOT manipulate routing tables,
BGP, OSPF, NAT, conntrack, or customer traffic directly.

BM7 owns the control-plane decision:
    Who owns the service?
    Who may take ownership?
    When does a lease expire?
    How is ownership handed back?

The data plane may consume BM7 ownership decisions separately.

This implementation uses JSON as the reference wire encoding.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import hmac
import ipaddress
import json
import socket
import threading
import time
from typing import Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# Protocol constants
# ---------------------------------------------------------------------------

BM7_VERSION = 1
BM7_PORT = 4707

LEASE_SECONDS = 15
CLOCK_SKEW_SECONDS = 30

MAX_MESSAGE_SIZE = 65535


# ---------------------------------------------------------------------------
# Protocol message types
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Node roles
# ---------------------------------------------------------------------------

class Role(str, Enum):
    PRIMARY = "PRIMARY"
    STANDBY = "STANDBY"
    SERVING = "SERVING"
    RETURNING = "RETURNING"
    ISOLATED = "ISOLATED"


# ---------------------------------------------------------------------------
# Error codes
# ---------------------------------------------------------------------------

class ErrorCode(str, Enum):
    AUTH_FAIL = "AUTH_FAIL"
    VERSION_FAIL = "VERSION_FAIL"
    WRONG_DESTINATION = "WRONG_DESTINATION"
    UNKNOWN_PEER = "UNKNOWN_PEER"
    REPLAY = "REPLAY"
    TIMESTAMP_EXPIRED = "TIMESTAMP_EXPIRED"
    STALE_EPOCH = "STALE_EPOCH"
    LEASE_EXPIRED = "LEASE_EXPIRED"
    LEASE_INVALID = "LEASE_INVALID"
    NO_QUORUM = "NO_QUORUM"
    UNAUTHORIZED = "UNAUTHORIZED"
    UNKNOWN_SERVICE = "UNKNOWN_SERVICE"
    BAD_MESSAGE = "BAD_MESSAGE"
    BAD_STATE = "BAD_STATE"
    INVALID_CLAIM = "INVALID_CLAIM"


# ---------------------------------------------------------------------------
# Service state
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# BM7 Node
# ---------------------------------------------------------------------------

@dataclass
class Node:

    node_id: str
    peers: set
    secret: bytes

    epoch: int = 0
    role: Role = Role.STANDBY
    lease_until: float = 0
    seq: int = 0

    services: Dict[str, ServiceState] = field(default_factory=dict)

    # Last accepted sequence number from each peer.
    peer_last_seq: Dict[str, int] = field(default_factory=dict)

    # Last accepted timestamp from each peer.
    peer_last_seen: Dict[str, float] = field(default_factory=dict)

    # Last heartbeat received from each peer.
    peer_heartbeat: Dict[str, float] = field(default_factory=dict)

    # Peers that explicitly authorized a claim.
    claim_votes: Dict[str, set] = field(default_factory=dict)

    # Returning primary synchronization state.
    synchronized_peers: set = field(default_factory=set)

    # ------------------------------------------------------------------
    # Basic protocol helpers
    # ------------------------------------------------------------------

    def _canonical(self, message: dict) -> bytes:
        """
        Canonical serialization used for authentication.

        The MAC is calculated over the complete message excluding the MAC
        itself.
        """
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

    def verify(self, message: dict, mac: str) -> bool:
        expected = self.sign(message)

        return hmac.compare_digest(
            expected,
            mac,
        )

    # ------------------------------------------------------------------
    # Message creation
    # ------------------------------------------------------------------

    def packet(
        self,
        message_type: str | MessageType,
        peer: str,
        **payload,
    ) -> Tuple[dict, str]:

        if isinstance(message_type, MessageType):
            message_type = message_type.value

        if peer not in self.peers:
            raise ValueError(ErrorCode.UNKNOWN_PEER.value)

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

    # ------------------------------------------------------------------
    # Message validation
    # ------------------------------------------------------------------

    def validate_message(
        self,
        message: dict,
        mac: str,
        now: Optional[float] = None,
    ):

        now = time.time() if now is None else now

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

        if not required.issubset(message.keys()):
            raise ValueError(ErrorCode.BAD_MESSAGE.value)

        if message["v"] != BM7_VERSION:
            raise ValueError(ErrorCode.VERSION_FAIL.value)

        if message["dst"] != self.node_id:
            raise ValueError(ErrorCode.WRONG_DESTINATION.value)

        source = message["src"]

        if source not in self.peers:
            raise ValueError(ErrorCode.UNKNOWN_PEER.value)

        if not self.verify(message, mac):
            raise ValueError(ErrorCode.AUTH_FAIL.value)

        timestamp = float(message["ts"])

        if abs(now - timestamp) > CLOCK_SKEW_SECONDS:
            raise ValueError(
                ErrorCode.TIMESTAMP_EXPIRED.value
            )

        sequence = int(message["seq"])

        last_sequence = self.peer_last_seq.get(
            source,
            0,
        )

        if sequence <= last_sequence:
            raise ValueError(ErrorCode.REPLAY.value)

        message_epoch = int(message["epoch"])

        if message_epoch < self.epoch:
            raise ValueError(ErrorCode.STALE_EPOCH.value)

        self.peer_last_seq[source] = sequence
        self.peer_last_seen[source] = timestamp

        if message_epoch > self.epoch:
            self.epoch = message_epoch

    # ------------------------------------------------------------------
    # HELLO
    # ------------------------------------------------------------------

    def hello(self, peer: str):

        return self.packet(
            MessageType.HELLO,
            peer,
            capabilities=[
                "FAILOVER",
                "STATE_SYNC",
                "LEASE",
                "ROUTE_OWNERSHIP",
                "SESSION_OWNERSHIP",
            ],
            message_types=[
                item.value
                for item in MessageType
            ],
        )

    def handle_hello(
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
            capabilities=[
                "FAILOVER",
                "STATE_SYNC",
                "LEASE",
                "ROUTE_OWNERSHIP",
                "SESSION_OWNERSHIP",
            ],
        )

    # ------------------------------------------------------------------
    # HEARTBEAT
    # ------------------------------------------------------------------

    def heartbeat(self, peer: str):

        return self.packet(
            MessageType.HEARTBEAT,
            peer,
        )

    def handle_heartbeat(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        source = message["src"]

        self.peer_heartbeat[source] = time.time()

        return self.packet(
            MessageType.HEARTBEAT_ACK,
            source,
            received_seq=message["seq"],
        )

    def handle_heartbeat_ack(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        self.peer_heartbeat[message["src"]] = time.time()

    # ------------------------------------------------------------------
    # Failure detection
    # ------------------------------------------------------------------

    def peer_is_alive(
        self,
        peer_id: str,
        now: Optional[float] = None,
    ) -> bool:

        now = time.time() if now is None else now

        last = self.peer_heartbeat.get(peer_id)

        if last is None:
            return False

        return (
            now - last
        ) <= CLOCK_SKEW_SECONDS

    # ------------------------------------------------------------------
    # STATE DIGEST
    # ------------------------------------------------------------------

    def state_digest(self) -> str:

        state = {
            "epoch": self.epoch,
            "role": self.role.value,
            "services": {
                service_id: service.to_dict()
                for service_id, service
                in sorted(self.services.items())
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

    def send_state_digest(self, peer: str):

        return self.packet(
            MessageType.STATE_DIGEST,
            peer,
            digest=self.state_digest(),
        )

    def handle_state_digest(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        local_digest = self.state_digest()

        remote_digest = message[
            "payload"
        ].get("digest")

        if remote_digest == local_digest:

            return self.packet(
                MessageType.STATE_RESPONSE,
                message["src"],
                status="MATCH",
                epoch=self.epoch,
                state=self.export_state(),
            )

        return self.packet(
            MessageType.STATE_REQUEST,
            message["src"],
            reason="STATE_MISMATCH",
            epoch=self.epoch,
        )

    # ------------------------------------------------------------------
    # STATE REQUEST / RESPONSE
    # ------------------------------------------------------------------

    def request_state(self, peer: str):

        return self.packet(
            MessageType.STATE_REQUEST,
            peer,
            epoch=self.epoch,
        )

    def handle_state_request(
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
            epoch=self.epoch,
            state=self.export_state(),
        )

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

    def import_state(self, state: dict):

        incoming_epoch = int(
            state["epoch"]
        )

        if incoming_epoch < self.epoch:
            raise ValueError(
                ErrorCode.STALE_EPOCH.value
            )

        services = {}

        for service_id, raw in state.get(
            "services",
            {},
        ).items():

            services[service_id] = ServiceState(
                service_id=raw["service_id"],
                prefix=raw["prefix"],
                owner=raw["owner"],
                sessions=dict(
                    raw.get("sessions", {})
                ),
            )

        self.services = services
        self.epoch = incoming_epoch

    def handle_state_response(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        payload = message["payload"]

        if payload.get("status") == "MATCH":
            self.synchronized_peers.add(
                message["src"]
            )
            return

        self.import_state(
            payload["state"]
        )

        self.synchronized_peers.add(
            message["src"]
        )

    # ------------------------------------------------------------------
    # Service registration
    # ------------------------------------------------------------------

    def register_service(
        self,
        service_id: str,
        prefix: str,
    ):

        # Validate that the prefix is actually a network.
        ipaddress.ip_network(
            prefix,
            strict=False,
        )

        self.services[service_id] = ServiceState(
            service_id=service_id,
            prefix=prefix,
            owner=self.node_id,
        )

    # ------------------------------------------------------------------
    # ROUTE CLAIM
    # ------------------------------------------------------------------

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

    def handle_route_claim(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        payload = message["payload"]

        service_id = payload.get(
            "service_id"
        )

        if service_id not in self.services:
            raise ValueError(
                ErrorCode.UNKNOWN_SERVICE.value
            )

        service = self.services[
            service_id
        ]

        if payload.get("prefix") != service.prefix:
            raise ValueError(
                ErrorCode.INVALID_CLAIM.value
            )

        return self.packet(
            MessageType.ROUTE_CLAIM_ACK,
            message["src"],
            service_id=service_id,
            owner=payload["owner"],
            epoch=self.epoch,
            status="ACCEPTED",
        )

    # ------------------------------------------------------------------
    # SESSION CLAIM
    # ------------------------------------------------------------------

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

    def handle_session_claim(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        service_id = message[
            "payload"
        ].get("service_id")

        service = self.services.get(
            service_id
        )

        if service is None:
            raise ValueError(
                ErrorCode.UNKNOWN_SERVICE.value
            )

        service.sessions.update(
            message["payload"].get(
                "sessions",
                {},
            )
        )

        return self.packet(
            MessageType.SESSION_CLAIM_ACK,
            message["src"],
            service_id=service_id,
            status="ACCEPTED",
        )

    # ------------------------------------------------------------------
    # FAILURE CLAIM
    # ------------------------------------------------------------------

    def failure_claim(
        self,
        peer: str,
        failed_id: str,
    ):

        if failed_id not in self.peers:
            raise ValueError(
                ErrorCode.UNKNOWN_PEER.value
            )

        if self.peer_is_alive(
            failed_id
        ):
            raise ValueError(
                ErrorCode.INVALID_CLAIM.value
            )

        return self.packet(
            MessageType.FAILURE_CLAIM,
            peer,
            failed_id=failed_id,
            candidate=self.node_id,
            proposed_epoch=self.epoch + 1,
        )

    def handle_failure_claim(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        payload = message["payload"]

        failed_id = payload[
            "failed_id"
        ]

        candidate = payload[
            "candidate"
        ]

        proposed_epoch = int(
            payload["proposed_epoch"]
        )

        if candidate != message["src"]:
            raise ValueError(
                ErrorCode.INVALID_CLAIM.value
            )

        if failed_id == self.node_id:
            raise ValueError(
                ErrorCode.INVALID_CLAIM.value
            )

        if self.peer_is_alive(
            failed_id
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
            failed_id=failed_id,
            candidate=candidate,
            epoch=proposed_epoch,
        )

    # ------------------------------------------------------------------
    # Takeover
    # ------------------------------------------------------------------

    def takeover(
        self,
        failed_id: str,
        now: Optional[float] = None,
    ):

        now = (
            time.time()
            if now is None
            else now
        )

        if failed_id not in self.peers:
            raise ValueError(
                ErrorCode.UNKNOWN_PEER.value
            )

        if self.peer_is_alive(
            failed_id,
            now=now,
        ):
            raise ValueError(
                ErrorCode.INVALID_CLAIM.value
            )

        self.epoch += 1

        self.role = Role.SERVING

        self.lease_until = (
            now + LEASE_SECONDS
        )

        for service in self.services.values():
            service.owner = self.node_id

        return self.epoch

    # ------------------------------------------------------------------
    # LEASE RENEW
    # ------------------------------------------------------------------

    def lease_renew(self, peer: str):

        if self.role != Role.SERVING:
            raise ValueError(
                ErrorCode.LEASE_INVALID.value
            )

        if time.time() > self.lease_until:
            raise ValueError(
                ErrorCode.LEASE_EXPIRED.value
            )

        return self.packet(
            MessageType.LEASE_RENEW,
            peer,
            lease_seconds=LEASE_SECONDS,
        )

    def handle_lease_renew(
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
                code=ErrorCode.LEASE_INVALID.value,
            )

        if time.time() > self.lease_until:
            return self.packet(
                MessageType.ERROR,
                message["src"],
                code=ErrorCode.LEASE_EXPIRED.value,
            )

        self.lease_until = (
            time.time()
            + LEASE_SECONDS
        )

        return self.packet(
            MessageType.LEASE_ACK,
            message["src"],
            lease_until=self.lease_until,
        )

    def renew(
        self,
        now: Optional[float] = None,
    ):

        now = (
            time.time()
            if now is None
            else now
        )

        if self.role != Role.SERVING:
            raise ValueError(
                ErrorCode.LEASE_INVALID.value
            )

        if now > self.lease_until:
            raise ValueError(
                ErrorCode.LEASE_EXPIRED.value
            )

        self.lease_until = (
            now + LEASE_SECONDS
        )

    # ------------------------------------------------------------------
    # RETURN / HAND-BACK
    # ------------------------------------------------------------------

    def return_prepare(
        self,
        primary_id: str,
    ):

        if self.role != Role.SERVING:
            raise ValueError(
                ErrorCode.BAD_STATE.value
            )

        if time.time() > self.lease_until:
            raise ValueError(
                ErrorCode.LEASE_EXPIRED.value
            )

        return self.packet(
            MessageType.RETURN_PREPARE,
            primary_id,
            returning_primary=primary_id,
            current_serving=self.node_id,
            epoch=self.epoch,
        )

    def handle_return_prepare(
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
            return self.packet(
                MessageType.ERROR,
                message["src"],
                code=ErrorCode.BAD_STATE.value,
            )

        self.role = Role.PRIMARY

        return self.packet(
            MessageType.RETURN_READY,
            message["src"],
            synchronized=True,
            epoch=self.epoch,
        )

    def prepare_return(
        self,
        primary_id: str,
        primary: "Node",
        now: Optional[float] = None,
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

            primary.services[
                service_id
            ] = ServiceState(
                service_id=service.service_id,
                prefix=service.prefix,
                owner=primary_id,
                sessions=dict(
                    service.sessions
                ),
            )

        primary.epoch = max(
            primary.epoch,
            self.epoch,
        )

        self.role = Role.RETURNING

        return primary.epoch

    def return_ready(
        self,
        peer: str,
    ):

        return self.packet(
            MessageType.RETURN_READY,
            peer,
            synchronized=True,
            epoch=self.epoch,
        )

    def return_commit(
        self,
        peer: str,
    ):

        return self.packet(
            MessageType.RETURN_COMMIT,
            peer,
            owner=peer,
            epoch=self.epoch,
        )

    def handle_return_commit(
        self,
        message: dict,
        mac: str,
    ):

        self.validate_message(
            message,
            mac,
        )

        primary_id = message[
            "src"
        ]

        for service in self.services.values():
            service.owner = primary_id

        self.role = Role.STANDBY
        self.lease_until = 0

        return self.packet(
            MessageType.RETURN_ACK,
            primary_id,
            status="COMMITTED",
            epoch=self.epoch,
        )

    def commit_return(
        self,
        primary_id: str,
        primary: "Node",
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
            primary.epoch,
        )

        self.role = Role.STANDBY
        primary.role = Role.PRIMARY
        primary.epoch = self.epoch
        self.lease_until = 0

    # ------------------------------------------------------------------
    # Generic protocol dispatcher
    # ------------------------------------------------------------------

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
                self.handle_hello,

            MessageType.HEARTBEAT.value:
                self.handle_heartbeat,

            MessageType.HEARTBEAT_ACK.value:
                self.handle_heartbeat_ack,

            MessageType.STATE_DIGEST.value:
                self.handle_state_digest,

            MessageType.STATE_REQUEST.value:
                self.handle_state_request,

            MessageType.STATE_RESPONSE.value:
                self.handle_state_response,

            MessageType.FAILURE_CLAIM.value:
                self.handle_failure_claim,

            MessageType.ROUTE_CLAIM.value:
                self.handle_route_claim,

            MessageType.SESSION_CLAIM.value:
                self.handle_session_claim,

            MessageType.LEASE_RENEW.value:
                self.handle_lease_renew,

            MessageType.RETURN_PREPARE.value:
                self.handle_return_prepare,

            MessageType.RETURN_COMMIT.value:
                self.handle_return_commit,
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
                code="UNKNOWN_MESSAGE_TYPE",
            )

        try:
            return handler(
                message,
                mac,
            )

        except ValueError as exc:

            try:
                source = message["src"]

                if source in self.peers:
                    return self.packet(
                        MessageType.ERROR,
                        source,
                        code=str(exc),
                    )

            except Exception:
                pass

            raise


# ---------------------------------------------------------------------------
# UDP BM7 Transport
# ---------------------------------------------------------------------------

class BM7UDPTransport:

    """
    Minimal UDP transport for BM7.

    This is the point where BM7 becomes an actual network protocol:
        UDP datagram
            ->
        BM7 JSON message
            ->
        BM7 authentication
            ->
        BM7 dispatcher
            ->
        BM7 response
    """

    def __init__(
        self,
        node: Node,
        bind_host: str = "0.0.0.0",
        port: int = BM7_PORT,
    ):

        self.node = node
        self.bind_host = bind_host
        self.port = port

        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        self.socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        self.socket.bind(
            (
                bind_host,
                port,
            )
        )

        self.running = False

    # ------------------------------------------------------------------
    # Encoding
    # ------------------------------------------------------------------

    @staticmethod
    def encode(
        message: dict,
        mac: str,
    ) -> bytes:

        envelope = {
            "message": message,
            "mac": mac,
        }

        encoded = json.dumps(
            envelope,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        if len(encoded) > MAX_MESSAGE_SIZE:
            raise ValueError(
                "BM7_MESSAGE_TOO_LARGE"
            )

        return encoded

    # ------------------------------------------------------------------
    # Decoding
    # ------------------------------------------------------------------

    @staticmethod
    def decode(
        data: bytes,
    ) -> Tuple[dict, str]:

        if len(data) > MAX_MESSAGE_SIZE:
            raise ValueError(
                "BM7_MESSAGE_TOO_LARGE"
            )

        envelope = json.loads(
            data.decode("utf-8")
        )

        if (
            "message" not in envelope
            or "mac" not in envelope
        ):
            raise ValueError(
                ErrorCode.BAD_MESSAGE.value
            )

        return (
            envelope["message"],
            envelope["mac"],
        )

    # ------------------------------------------------------------------
    # Send
    # ------------------------------------------------------------------

    def send(
        self,
        message: dict,
        mac: str,
        address: Tuple[str, int],
    ):

        data = self.encode(
            message,
            mac,
        )

        self.socket.sendto(
            data,
            address,
        )

    # ------------------------------------------------------------------
    # Receive one datagram
    # ------------------------------------------------------------------

    def receive_once(self):

        data, address = self.socket.recvfrom(
            MAX_MESSAGE_SIZE
        )

        try:

            message, mac = self.decode(
                data
            )

            response = self.node.receive(
                message,
                mac,
            )

            if response is not None:

                response_message, response_mac = response

                self.send(
                    response_message,
                    response_mac,
                    address,
                )

        except Exception as exc:

            # If possible, return a protocol ERROR.
            try:

                message = json.loads(
                    data.decode("utf-8")
                ).get(
                    "message",
                    {}
                )

                source = message.get(
                    "src"
                )

                if source in self.node.peers:

                    error_message, error_mac = (
                        self.node.packet(
                            MessageType.ERROR,
                            source,
                            code=str(exc),
                        )
                    )

                    self.send(
                        error_message,
                        error_mac,
                        address,
                    )

            except Exception:
                pass

    # ------------------------------------------------------------------
    # Server loop
    # ------------------------------------------------------------------

    def serve_forever(self):

        self.running = True

        print(
            f"BM7 node '{self.node.node_id}' "
            f"listening on UDP/{self.port}"
        )

        while self.running:

            self.receive_once()

    def stop(self):

        self.running = False

        try:
            self.socket.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Cluster authority
# ---------------------------------------------------------------------------

class Cluster:

    def __init__(self, nodes):

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

        # Reference policy:
        # at least two trusted nodes must be available.
        return len(trusted) >= 2

    def claim(
        self,
        node_id: str,
        failed_id: str,
        available,
    ):

        if not self.quorum(
            available
        ):
            raise ValueError(
                ErrorCode.NO_QUORUM.value
            )

        if node_id not in self.nodes:
            raise ValueError(
                ErrorCode.UNKNOWN_PEER.value
            )

        if failed_id not in self.nodes:
            raise ValueError(
                ErrorCode.UNKNOWN_PEER.value
            )

        node = self.nodes[
            node_id
        ]

        return node.takeover(
            failed_id,
            now=time.time(),
        )


# ---------------------------------------------------------------------------
# Protocol demonstration
# ---------------------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # Normal operation
    # ---------------------------------------------------------------

    b.role = Role.PRIMARY

    b.register_service(
        "customer-net-01",
        "10.20.0.0/24",
    )

    print(
        "=== NORMAL OPERATION ==="
    )

    print(
        "B:",
        b.role.value,
    )

    print(
        "C:",
        c.role.value,
    )

    # ---------------------------------------------------------------
    # HELLO
    # ---------------------------------------------------------------

    hello, hello_mac = c.hello(
        "branch-b"
    )

    hello_ack = b.handle_hello(
        hello,
        hello_mac,
    )

    print(
        "HELLO:",
        hello_ack[0]["type"],
    )

    # ---------------------------------------------------------------
    # HEARTBEAT
    # ---------------------------------------------------------------

    heartbeat, heartbeat_mac = (
        c.heartbeat(
            "branch-b"
        )
    )

    heartbeat_ack = b.handle_heartbeat(
        heartbeat,
        heartbeat_mac,
    )

    print(
        "Heartbeat:",
        heartbeat_ack[0]["type"],
    )

    # ---------------------------------------------------------------
    # State synchronization
    # ---------------------------------------------------------------

    state_request, state_request_mac = (
        c.request_state(
            "branch-b"
        )
    )

    state_response = b.handle_state_request(
        state_request,
        state_request_mac,
    )

    c.handle_state_response(
        state_response[0],
        state_response[1],
    )

    print(
        "State synchronization: OK"
    )

    # ---------------------------------------------------------------
    # FAILURE
    # ---------------------------------------------------------------

    print(
        "\n=== FAILURE ==="
    )

    # Simulate B becoming unavailable.
    c.peer_heartbeat[
        "branch-b"
    ] = time.time() - (
        CLOCK_SKEW_SECONDS + 1
    )

    failure_claim, failure_mac = (
        c.failure_claim(
            "branch-a",
            "branch-b",
        )
    )

    failure_ack = a.handle_failure_claim(
        failure_claim,
        failure_mac,
    )

    print(
        "Failure claim:",
        failure_ack[0]["payload"]["status"],
    )

    # Local reference authority approves
    # the takeover after quorum.
    cluster = Cluster(
        [a, b, c]
    )

    epoch = cluster.claim(
        "branch-c",
        "branch-b",
        [
            "branch-a",
            "branch-c",
        ],
    )

    print(
        "C takeover epoch:",
        epoch,
    )

    print(
        "C role:",
        c.role.value,
    )

    print(
        "Service owner:",
        c.services[
            "customer-net-01"
        ].owner,
    )

    # ---------------------------------------------------------------
    # LEASE
    # ---------------------------------------------------------------

    print(
        "Lease valid:",
        c.lease_until > time.time(),
    )

    # ---------------------------------------------------------------
    # RETURN
    # ---------------------------------------------------------------

    print(
        "\n=== RECOVERY ==="
    )

    # B establishes communication again.
    b.role = Role.STANDBY

    state_request, state_request_mac = (
        b.request_state(
            "branch-c"
        )
    )

    state_response = c.handle_state_request(
        state_request,
        state_request_mac,
    )

    b.handle_state_response(
        state_response[0],
        state_response[1],
    )

    # C prepares the return.
    c.prepare_return(
        "branch-b",
        b,
    )

    # B becomes the primary again.
    b.role = Role.PRIMARY

    c.commit_return(
        "branch-b",
        b,
    )

    print(
        "B role:",
        b.role.value,
    )

    print(
        "C role:",
        c.role.value,
    )

    print(
        "Recovered owner:",
        b.services[
            "customer-net-01"
        ].owner,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo()
