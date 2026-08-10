import socket
import time

import pytest

from src.client.dns_client import DNSClient
from src.core.dns_message import DNSMessage
from src.core.dns_question import DNSQuestion
from src.core.dns_requester import DNSRequester
from src.core.enums import RecordType
from src.name_server.base.base_name_server import BaseNameServer
from src.recursive_resolver.server import RecursiveResolver


ROOT_FAKE_IP = "127.0.0.10"
TLD_FAKE_IP = "127.0.0.11"
AUTH_FAKE_IP = "127.0.0.12"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _probe_server(port: int, timeout: float = 5.0) -> None:
    requester = DNSRequester()
    probe = DNSMessage(id=1)
    probe.questions.append(DNSQuestion("probe.local", RecordType.A))

    deadline = time.time() + timeout
    while time.time() < deadline:
        if requester.send_udp_query("127.0.0.1", port, probe.pack(), timeout=0.2):
            return
        time.sleep(0.05)

    raise RuntimeError(f"DNS server on port {port} did not become ready in time")


@pytest.fixture()
def recursive_stack():
    root_port = _free_port()
    tld_port = _free_port()
    auth_port = _free_port()
    recursive_port = _free_port()

    root_zone = {
        "be": {
            "NS": [{"host": "ns1.tld.be", "ttl": 86400}],
        },
        "ns1.tld.be": {
            "A": [{"ip": TLD_FAKE_IP, "ttl": 300}],
        },
    }
    tld_zone = {
        "test.be": {
            "NS": [{"host": "ns1.test.be", "ttl": 86400}],
        },
        "ns1.test.be": {
            "A": [{"ip": AUTH_FAKE_IP, "ttl": 300}],
        },
    }
    auth_zone = {
        "www.test.be": {
            "A": [{"ip": "192.168.99.99", "ttl": 300}],
            "AAAA": [{"ip": "2001:db8::99", "ttl": 300}],
        },
        "api.test.be": {
            "A": [{"ip": "192.168.99.100", "ttl": 300}],
        },
    }

    root_server = BaseNameServer("127.0.0.1", root_port, initial_zone_data=root_zone)
    tld_server = BaseNameServer("127.0.0.1", tld_port, initial_zone_data=tld_zone)
    auth_server = BaseNameServer("127.0.0.1", auth_port, initial_zone_data=auth_zone)
    recursive_server = RecursiveResolver("127.0.0.1", recursive_port, root_ips=[ROOT_FAKE_IP])

    counts = {"root": 0, "tld": 0, "auth": 0}

    def wrap_route(server, key):
        original = server._route_request

        def wrapped(data, addr, protocol):
            counts[key] += 1
            return original(data, addr, protocol)

        return wrapped

    root_server._route_request = wrap_route(root_server, "root")
    tld_server._route_request = wrap_route(tld_server, "tld")
    auth_server._route_request = wrap_route(auth_server, "auth")

    original_send_udp_query = DNSRequester.send_udp_query
    original_send_tcp_query = DNSRequester.send_tcp_query
    endpoint_map = {
        ROOT_FAKE_IP: root_port,
        TLD_FAKE_IP: tld_port,
        AUTH_FAKE_IP: auth_port,
    }

    def routed_send_udp_query(self, ip, port, data, timeout=5):
        return original_send_udp_query(self, "127.0.0.1", endpoint_map.get(ip, port), data, timeout)

    def routed_send_tcp_query(self, ip, port, data, timeout=5):
        return original_send_tcp_query(self, "127.0.0.1", endpoint_map.get(ip, port), data, timeout)

    DNSRequester.send_udp_query = routed_send_udp_query
    DNSRequester.send_tcp_query = routed_send_tcp_query

    root_server.start_listening()
    tld_server.start_listening()
    auth_server.start_listening()
    recursive_server.start_listening()

    _probe_server(root_port)
    _probe_server(tld_port)
    _probe_server(auth_port)
    _probe_server(recursive_port)

    yield {
        "root_port": root_port,
        "tld_port": tld_port,
        "auth_port": auth_port,
        "recursive_port": recursive_port,
        "root_server": root_server,
        "tld_server": tld_server,
        "auth_server": auth_server,
        "recursive_server": recursive_server,
        "counts": counts,
    }

    DNSRequester.send_udp_query = original_send_udp_query
    DNSRequester.send_tcp_query = original_send_tcp_query


def test_recursive_stack_resolves_a_and_aaaa_and_hits_cache(recursive_stack):
    client = DNSClient()

    baseline_counts = dict(recursive_stack["counts"])

    response_a = client.execute_query(
        "www.test.be",
        "A",
        rd_flag=1,
        use_tcp=False,
        target_ip="127.0.0.1",
        port=recursive_stack["recursive_port"],
    )

    assert response_a.ra == 1
    assert response_a.aa == 1
    assert len(response_a.answers) == 1
    assert response_a.answers[0].type == RecordType.A
    assert response_a.answers[0].rdata_str == "192.168.99.99"
    assert recursive_stack["counts"]["root"] == baseline_counts["root"] + 1
    assert recursive_stack["counts"]["tld"] == baseline_counts["tld"] + 1
    assert recursive_stack["counts"]["auth"] == baseline_counts["auth"] + 1

    counts_after_first_lookup = dict(recursive_stack["counts"])

    cached_response = client.execute_query(
        "www.test.be",
        "A",
        rd_flag=1,
        use_tcp=False,
        target_ip="127.0.0.1",
        port=recursive_stack["recursive_port"],
    )

    assert cached_response.ra == 1
    assert cached_response.aa == 0
    assert len(cached_response.answers) == 1
    assert cached_response.answers[0].rdata_str == "192.168.99.99"
    assert recursive_stack["counts"] == counts_after_first_lookup

    response_aaaa = client.execute_query(
        "www.test.be",
        "AAAA",
        rd_flag=1,
        use_tcp=False,
        target_ip="127.0.0.1",
        port=recursive_stack["recursive_port"],
    )

    assert response_aaaa.ra == 1
    assert response_aaaa.aa == 1
    assert len(response_aaaa.answers) == 1
    assert response_aaaa.answers[0].type == RecordType.AAAA
    assert response_aaaa.answers[0].rdata_str == "2001:db8::99"
    assert recursive_stack["counts"]["root"] == counts_after_first_lookup["root"] + 1
    assert recursive_stack["counts"]["tld"] == counts_after_first_lookup["tld"] + 1
    assert recursive_stack["counts"]["auth"] == counts_after_first_lookup["auth"] + 1


def test_recursive_stack_flushes_cache_via_txt_command(recursive_stack):
    client = DNSClient()

    warm_response = client.execute_query(
        "www.test.be",
        "A",
        rd_flag=1,
        use_tcp=False,
        target_ip="127.0.0.1",
        port=recursive_stack["recursive_port"],
    )

    assert warm_response.aa == 1
    counts_after_warm = dict(recursive_stack["counts"])

    flush_response = client.execute_query(
        "flush.cache.local",
        "TXT",
        rd_flag=1,
        use_tcp=False,
        target_ip="127.0.0.1",
        port=recursive_stack["recursive_port"],
    )

    assert flush_response.answers[0].type == RecordType.TXT
    assert flush_response.answers[0].rdata_str == "Cache flushed successfully"

    post_flush_response = client.execute_query(
        "www.test.be",
        "A",
        rd_flag=1,
        use_tcp=False,
        target_ip="127.0.0.1",
        port=recursive_stack["recursive_port"],
    )

    assert post_flush_response.aa == 1
    assert post_flush_response.answers[0].rdata_str == "192.168.99.99"
    assert recursive_stack["counts"]["root"] == counts_after_warm["root"] + 1
    assert recursive_stack["counts"]["tld"] == counts_after_warm["tld"] + 1
    assert recursive_stack["counts"]["auth"] == counts_after_warm["auth"] + 1