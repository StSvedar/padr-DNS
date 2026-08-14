from unittest.mock import MagicMock
from src.core.dns_message import DNSMessage
from src.core.dns_question import DNSQuestion
from src.core.enums import RecordType, Rcode
from src.core.resource_record import ResourceRecord
from src.name_server.base.base_name_server import BaseNameServer

def test_name_server_handles_recursive_query():
    server = BaseNameServer("127.0.0.1", 53, initial_zone_data={"example.com": {}})

    fake_resolved_msg = DNSMessage(id=0x1234, qr=1, rcode=Rcode.NOERROR)
    fake_resolved_msg.answers.append(ResourceRecord.create_A("google.com", "8.8.8.8", 300))
    server.engine.resolve = MagicMock(return_value=fake_resolved_msg)

    query = DNSMessage(id=0x1234, rd=1)
    query.questions.append(DNSQuestion("google.com", RecordType.A))
    
    response_bytes = server._route_request(query.pack(), ("192.168.1.1", 12345), "UDP")
    response = DNSMessage.unpack(response_bytes)

    server.engine.resolve.assert_called_once()
    
    assert response.ra == 1

    assert response.rcode == Rcode.NOERROR
    assert len(response.answers) == 1
    assert response.answers[0].rdata_str == "8.8.8.8"

def test_name_server_refuses_external_query_without_recursion():
    server = BaseNameServer("127.0.0.1", 53, initial_zone_data={"example.com": {}})
    
    query = DNSMessage(id=0x5678, rd=0)
    query.questions.append(DNSQuestion("google.com", RecordType.A))
    
    response_bytes = server._route_request(query.pack(), ("192.168.1.1", 12345), "UDP")
    response = DNSMessage.unpack(response_bytes)
    
    assert response.rcode == Rcode.REFUSED