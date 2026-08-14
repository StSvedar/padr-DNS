import socket
from unittest.mock import MagicMock

from src.name_server.base.base_name_server import BaseNameServer
from src.core.dns_message import DNSMessage
from src.core.dns_question import DNSQuestion
from src.core.enums import RecordType, Rcode


MOCK_ZONE = {
    "be": {"NS": [{"host": "ns1.be", "ttl": 86400}, {"host": "ns2.be", "ttl": 86400}]},
    "ns1.be": {"A": [{"ip": "1.2.3.4", "ttl": 300}]},
    "test.be": {"A": [{"ip": "192.168.1.50", "ttl": 120}]},
}

def test_base_server_routing():
    server = BaseNameServer("127.0.0.1", 53, initial_zone_data=MOCK_ZONE)

    fake_response = DNSMessage(id=0x9999, qr=1)
    server._build_response = MagicMock(return_value=fake_response)

    fake_query = DNSMessage(id=0x1111)    
    domain_in_mock = list(MOCK_ZONE.keys())[0] if MOCK_ZONE else "example.com"
    fake_query.questions.append(DNSQuestion(name=domain_in_mock, qtype=RecordType.A))
    
    fake_query_bytes = fake_query.pack()

    result_bytes = server._route_request(fake_query_bytes, ("192.168.1.1", 12345), "UDP")

    server._build_response.assert_called_once()

def test_base_server_exact_match_response():
    server = BaseNameServer("127.0.0.1", 53, initial_zone_data=MOCK_ZONE)
    query = DNSMessage()
    query.questions.append(DNSQuestion("test.be", RecordType.A))

    response = server._build_response(query)

    assert response.aa == 1
    assert response.rcode == Rcode.NOERROR
    assert response.ancount == 1
    assert response.answers[0].rdata == socket.inet_aton("192.168.1.50")


def test_base_server_nxdomain_response():
    server = BaseNameServer("127.0.0.1", 53, initial_zone_data=MOCK_ZONE)
    query = DNSMessage()
    query.questions.append(DNSQuestion("inconnu.com", RecordType.A))

    response = server._build_response(query)

    assert response.aa == 1
    assert response.rcode == Rcode.NXDOMAIN
    assert response.ancount == 0


def test_base_server_delegation_and_glue_response():
    server = BaseNameServer("127.0.0.1", 53, initial_zone_data=MOCK_ZONE)
    query = DNSMessage()
    query.questions.append(DNSQuestion("sous-domaine.be", RecordType.A))

    response = server._build_response(query)

    assert response.aa == 0
    assert response.rcode == Rcode.NOERROR
    assert response.ancount == 0
    assert len(response.authority) == 2
    assert response.authority[0].type == RecordType.NS
    assert len(response.additional) == 1
    assert response.additional[0].type == RecordType.A
    assert response.additional[0].rdata == socket.inet_aton("1.2.3.4")