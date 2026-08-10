import json
import socket
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from src.client.dns_client import DNSClient
from src.core.dns_message import DNSMessage
from src.core.dns_question import DNSQuestion
from src.core.dns_requester import DNSRequester
from src.core.enums import RecordClass, RecordType
from src.name_server.master.master_server import MasterServer
from src.name_server.slave.slave_server import SlaveServer


SLAVE_FAKE_IP = "127.0.0.21"


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
def replication_stack(tmp_path: Path):
    master_port = _free_port()
    slave_port = _free_port()

    initial_zone = {
        "test.be": {
            "NS": [{"host": "ns1.test.be", "ttl": 86400}],
        },
        "ns1.test.be": {
            "A": [{"ip": SLAVE_FAKE_IP, "ttl": 300}],
        },
        "www.test.be": {
            "A": [{"ip": "192.168.50.10", "ttl": 120}],
            "AAAA": [{"ip": "2001:db8::10", "ttl": 120}],
        },
    }
    updated_zone = {
        "test.be": {
            "NS": [{"host": "ns1.test.be", "ttl": 86400}],
        },
        "ns1.test.be": {
            "A": [{"ip": SLAVE_FAKE_IP, "ttl": 300}],
        },
        "www.test.be": {
            "A": [{"ip": "192.168.50.11", "ttl": 120}],
            "AAAA": [{"ip": "2001:db8::11", "ttl": 120}],
        },
    }

    zone_file = tmp_path / "master-zone.json"
    zone_file.write_text(json.dumps(initial_zone), encoding="utf-8")

    with patch("src.name_server.master.zone_loader.ZoneLoader.listen_for_sighup", return_value=None):
        master_server = MasterServer("127.0.0.1", master_port, str(zone_file), slave_ips=[SLAVE_FAKE_IP])
    slave_server = SlaveServer("127.0.0.1", slave_port, master_ip="127.0.0.1", master_port=master_port)

    original_send_udp_query = DNSRequester.send_udp_query
    original_send_tcp_query = DNSRequester.send_tcp_query
    endpoint_map = {
        SLAVE_FAKE_IP: slave_port,
    }

    def routed_send_udp_query(self, ip, port, data, timeout=5):
        return original_send_udp_query(self, "127.0.0.1", endpoint_map.get(ip, port), data, timeout)

    def routed_send_tcp_query(self, ip, port, data, timeout=5):
        return original_send_tcp_query(self, "127.0.0.1", endpoint_map.get(ip, port), data, timeout)

    DNSRequester.send_udp_query = routed_send_udp_query
    DNSRequester.send_tcp_query = routed_send_tcp_query

    master_server.start_listening()
    slave_server.start_listening()

    _probe_server(master_port)
    _probe_server(slave_port)

    slave_server.sync_from_master()

    yield {
        "master": master_server,
        "slave": slave_server,
        "master_port": master_port,
        "slave_port": slave_port,
        "initial_zone": initial_zone,
        "updated_zone": updated_zone,
    }

    DNSRequester.send_udp_query = original_send_udp_query
    DNSRequester.send_tcp_query = original_send_tcp_query


def test_master_serves_axfr_and_slave_resynchronizes_on_notify(replication_stack):
    requester = DNSRequester()

    axfr_query = DNSMessage(id=42)
    axfr_query.questions.append(DNSQuestion(".", RecordType.AXFR, RecordClass.IN))

    initial_axfr_raw = requester.send_tcp_query("127.0.0.1", replication_stack["master_port"], axfr_query.pack())
    initial_axfr = DNSMessage.unpack(initial_axfr_raw)
    assert initial_axfr.answers[0].type == RecordType.AXFR
    assert json.loads(initial_axfr.answers[0].rdata.decode("utf-8")) == replication_stack["master"].zone_data.to_dict()

    client = DNSClient()

    initial_a = client.execute_query(
        "www.test.be",
        "A",
        rd_flag=1,
        use_tcp=False,
        target_ip="127.0.0.1",
        port=replication_stack["slave_port"],
    )
    initial_aaaa = client.execute_query(
        "www.test.be",
        "AAAA",
        rd_flag=1,
        use_tcp=False,
        target_ip="127.0.0.1",
        port=replication_stack["slave_port"],
    )

    assert initial_a.answers[0].rdata_str == "192.168.50.10"
    assert initial_aaaa.answers[0].rdata_str == "2001:db8::10"
    assert replication_stack["slave"].replication_manager.current_serial == 1

    replication_stack["master"].on_zone_reload(replication_stack["updated_zone"])
    replication_stack["master"].replication_manager.send_notify_to_slaves()

    updated_axfr_raw = requester.send_tcp_query("127.0.0.1", replication_stack["master_port"], axfr_query.pack())
    updated_axfr = DNSMessage.unpack(updated_axfr_raw)
    assert json.loads(updated_axfr.answers[0].rdata.decode("utf-8")) == replication_stack["master"].zone_data.to_dict()

    updated_a = client.execute_query(
        "www.test.be",
        "A",
        rd_flag=1,
        use_tcp=False,
        target_ip="127.0.0.1",
        port=replication_stack["slave_port"],
    )
    updated_aaaa = client.execute_query(
        "www.test.be",
        "AAAA",
        rd_flag=1,
        use_tcp=False,
        target_ip="127.0.0.1",
        port=replication_stack["slave_port"],
    )

    assert updated_a.answers[0].rdata_str == "192.168.50.11"
    assert updated_aaaa.answers[0].rdata_str == "2001:db8::11"
    assert replication_stack["slave"].replication_manager.current_serial == 2