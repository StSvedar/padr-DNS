import socket
from src.core.dns_message import DNSMessage
from src.core.dns_question import DNSQuestion
from src.core.enums import RecordType, Rcode
from src.name_server.base.authoritative_engine import AuthoritativeEngine

MOCK_ZONE = {
    "be": {"NS": [{"host": "ns1.be", "ttl": 86400}, {"host": "ns2.be", "ttl": 86400}]},
    "ns1.be": {"A": [{"ip": "1.2.3.4", "ttl": 300}]},
    "test.be": {"A": [{"ip": "192.168.1.50", "ttl": 120}]}
}

def test_engine_exact_match():
    engine = AuthoritativeEngine(MOCK_ZONE)
    query = DNSMessage()
    query.questions.append(DNSQuestion('test.be', RecordType.A))
    
    response = engine.build_response(query)
    
    assert response.aa == 1
    assert response.rcode == Rcode.NOERROR
    assert response.ancount == 1
    assert response.answers[0].rdata == socket.inet_aton("192.168.1.50")

def test_engine_nxdomain():
    engine = AuthoritativeEngine(MOCK_ZONE)
    query = DNSMessage()
    query.questions.append(DNSQuestion('inconnu.com', RecordType.A))
    
    response = engine.build_response(query)
    
    assert response.aa == 1
    assert response.rcode == Rcode.NXDOMAIN
    assert response.ancount == 0

def test_engine_delegation_and_glue():
    engine = AuthoritativeEngine(MOCK_ZONE)
    query = DNSMessage()
    query.questions.append(DNSQuestion('sous-domaine.be', RecordType.A))
    
    response = engine.build_response(query)
    
    assert response.aa == 0
    assert response.rcode == Rcode.NOERROR
    assert response.ancount == 0

    assert len(response.authority) == 2
    assert response.authority[0].type == RecordType.NS

    assert len(response.additional) == 1
    assert response.additional[0].type == RecordType.A
    assert response.additional[0].rdata == socket.inet_aton("1.2.3.4")