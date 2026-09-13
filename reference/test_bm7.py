import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(ROOT / "reference")
)


from bm7_reference import (
    Node,
    Cluster,
    Role,
    LEASE_SECONDS,
)


SECRET = b"test-secret"


def make_nodes():

    a = Node(
        node_id="branch-a",
        peers={"branch-b", "branch-c"},
        secret=SECRET
    )

    b = Node(
        node_id="branch-b",
        peers={"branch-a", "branch-c"},
        secret=SECRET
    )

    c = Node(
        node_id="branch-c",
        peers={"branch-a", "branch-b"},
        secret=SECRET
    )

    return a, b, c


def test_auth_and_heartbeat():

    _, b, c = make_nodes()

    message, mac = c.heartbeat(
        "branch-b"
    )

    b.receive_heartbeat(
        message,
        mac
    )

    assert (
        b.peer_last_seen[
            "branch-c"
        ] == message["ts"]
    )

    print(
        "test_auth_and_heartbeat PASS"
    )


def test_invalid_authentication():

    _, b, c = make_nodes()

    message, mac = c.heartbeat(
        "branch-b"
    )

    bad_mac = "00" * 32

    try:

        b.receive_heartbeat(
            message,
            bad_mac
        )

        assert False, (
            "Invalid MAC was accepted"
        )

    except ValueError as exc:

        assert str(exc) == "AUTH_FAIL"

    print(
        "test_invalid_authentication PASS"
    )


def test_failover_and_epoch():

    _, b, c = make_nodes()

    b.role = Role.PRIMARY

    b.register_service(
        "customer-net-01",
        "10.20.0.0/24"
    )

    c.replicate_from(
        b,
        "branch-b"
    )

    old_epoch = c.epoch

    cluster = Cluster(
        [b, c]
    )

    new_epoch = cluster.claim(
        "branch-c",
        "branch-b",
        ["branch-b", "branch-c"]
    )

    assert new_epoch > old_epoch

    assert c.role == Role.SERVING

    assert (
        c.services[
            "customer-net-01"
        ].owner == "branch-c"
    )

    print(
        "test_failover_and_epoch PASS"
    )


def test_no_quorum():

    _, b, c = make_nodes()

    b.role = Role.PRIMARY

    b.register_service(
        "customer-net-01",
        "10.20.0.0/24"
    )

    c.replicate_from(
        b,
        "branch-b"
    )

    cluster = Cluster(
        [b, c]
    )

    try:

        cluster.claim(
            "branch-c",
            "branch-b",
            ["branch-c"]
        )

        assert False, (
            "Takeover occurred without quorum"
        )

    except ValueError as exc:

        assert str(exc) == "NO_QUORUM"

    print(
        "test_no_quorum PASS"
    )


def test_return_handback():

    _, b, c = make_nodes()

    b.role = Role.PRIMARY

    b.register_service(
        "customer-net-01",
        "10.20.0.0/24"
    )

    c.replicate_from(
        b,
        "branch-b"
    )

    cluster = Cluster(
        [b, c]
    )

    cluster.claim(
        "branch-c",
        "branch-b",
        ["branch-b", "branch-c"]
    )

    assert c.role == Role.SERVING

    c.prepare_return(
        "branch-b",
        b,
        now=101.0
    )

    assert c.role == Role.RETURNING

    c.commit_return(
        "branch-b",
        b
    )

    assert b.role == Role.PRIMARY
    assert c.role == Role.STANDBY

    assert (
        b.services[
            "customer-net-01"
        ].owner == "branch-b"
    )

    print(
        "test_return_handback PASS"
    )


def test_expired_lease():

    _, b, c = make_nodes()

    b.role = Role.PRIMARY

    b.register_service(
        "customer-net-01",
        "10.20.0.0/24"
    )

    c.replicate_from(
        b,
        "branch-b"
    )

    cluster = Cluster(
        [b, c]
    )

    cluster.claim(
        "branch-c",
        "branch-b",
        ["branch-b", "branch-c"]
    )

    expired_time = (
        c.lease_until + 1
    )

    try:

        c.prepare_return(
            "branch-b",
            b,
            now=expired_time
        )

        assert False, (
            "Expired lease was accepted"
        )

    except ValueError as exc:

        assert str(exc) == "LEASE_EXPIRED"

    print(
        "test_expired_lease PASS"
    )


def test_stale_epoch_protection():

    _, b, c = make_nodes()

    b.role = Role.PRIMARY

    b.epoch = 100

    b.register_service(
        "customer-net-01",
        "10.20.0.0/24"
    )

    c.replicate_from(
        b,
        "branch-b"
    )

    cluster = Cluster(
        [b, c]
    )

    new_epoch = cluster.claim(
        "branch-c",
        "branch-b",
        ["branch-b", "branch-c"]
    )

    assert new_epoch == 101
    assert c.epoch == 101

    # Old primary state must not have a newer epoch.
    assert b.epoch <= c.epoch

    print(
        "test_stale_epoch_protection PASS"
    )


def run_all_tests():

    test_auth_and_heartbeat()
    test_invalid_authentication()
    test_failover_and_epoch()
    test_no_quorum()
    test_return_handback()
    test_expired_lease()
    test_stale_epoch_protection()

    print()
    print(
        "ALL BM7 TESTS PASS"
    )


if __name__ == "__main__":
    run_all_tests()
```
