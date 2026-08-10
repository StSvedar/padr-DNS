from unittest.mock import MagicMock

from src.core.dns_message import DNSMessage
from src.core.dns_question import DNSQuestion
from src.core.enums import RecordType
from src.core.resource_record import ResourceRecord
from src.recursive_resolver.iterative_engine import IterativeEngine


def test_iterative_engine_follows_delegation_chain():
    engine = IterativeEngine(root_ips=["10.0.0.1"])

    query = DNSMessage(id=0x1111)
    query.questions.append(DNSQuestion("test.com", RecordType.A))

    root_response = DNSMessage()
    root_response.additional.append(ResourceRecord.create_A("ns1.test.com", "10.0.0.2", 86400))

    authoritative_response = DNSMessage()
    authoritative_response.aa = 1
    authoritative_response.answers.append(ResourceRecord.create_A("test.com", "192.168.1.100", 300))

    engine.requester = MagicMock()
    engine.requester.send_udp_query.side_effect = [root_response.pack(), authoritative_response.pack()]

    final_response = engine.resolve(query)

    assert engine.requester.send_udp_query.call_count == 2
    assert final_response.aa == 1
    assert len(final_response.answers) == 1
    assert final_response.answers[0].rdata_str == "192.168.1.100"