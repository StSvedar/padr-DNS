from unittest.mock import MagicMock, patch

from src.core.dns_message import DNSMessage
from src.core.dns_question import DNSQuestion
from src.core.enums import RecordType, Rcode
from src.core.resource_record import ResourceRecord
from src.recursive_resolver.server import RecursiveResolver


@patch("src.recursive_resolver.server.DNSListener")
def test_recursive_resolver_refuses_non_recursive_queries(mock_listener_class):
    server = RecursiveResolver("127.0.0.1", 53)
    server.engine.resolve = MagicMock()

    query = DNSMessage(id=0x9999, rd=0)
    query.questions.append(DNSQuestion("test.com", RecordType.A))

    response_bytes = server._route_request(query.pack(), ("192.168.1.1", 1234), "UDP")
    response_msg = DNSMessage.unpack(response_bytes)

    assert response_msg.rcode == Rcode.REFUSED
    server.engine.resolve.assert_not_called()


@patch("src.recursive_resolver.server.DNSListener")
def test_recursive_resolver_cache_hit(mock_listener_class):
    server = RecursiveResolver("127.0.0.1", 53)
    server.engine.resolve = MagicMock()

    cached_response = DNSMessage(id=0x1234)
    cached_response.answers.append(ResourceRecord.create_A("cached.com", "1.1.1.1", 300))
    server.cache.retrieve = MagicMock(return_value=cached_response)

    query = DNSMessage(id=0x1234, rd=1)
    query.questions.append(DNSQuestion("cached.com", RecordType.A))

    response_bytes = server._route_request(query.pack(), ("192.168.1.1", 1234), "UDP")
    response_msg = DNSMessage.unpack(response_bytes)

    assert response_msg.ra == 1
    assert len(response_msg.answers) == 1
    assert response_msg.answers[0].rdata_str == "1.1.1.1"
    server.engine.resolve.assert_not_called()


@patch("src.recursive_resolver.server.DNSListener")
def test_recursive_resolver_cache_miss_queries_engine(mock_listener_class):
    server = RecursiveResolver("127.0.0.1", 53)

    resolved_response = DNSMessage(id=0x5555)
    resolved_response.answers.append(ResourceRecord.create_A("upstream.com", "9.9.9.9", 120))
    server.engine.resolve = MagicMock(return_value=resolved_response)
    server.cache.retrieve = MagicMock(return_value=None)
    server.cache.store = MagicMock()

    query = DNSMessage(id=0x5555, rd=1)
    query.questions.append(DNSQuestion("upstream.com", RecordType.A))

    response_bytes = server._route_request(query.pack(), ("192.168.1.1", 1234), "UDP")
    response_msg = DNSMessage.unpack(response_bytes)

    assert response_msg.ra == 1
    server.engine.resolve.assert_called_once()
    server.cache.store.assert_called_once()


@patch("src.recursive_resolver.server.DNSListener")
def test_recursive_resolver_flush_cache_command(mock_listener_class):
    server = RecursiveResolver("127.0.0.1", 53)
    server.cache.clear_cache = MagicMock()

    query = DNSMessage(id=0x7777, rd=1)
    query.questions.append(DNSQuestion("flush.cache.local", RecordType.TXT))

    response_bytes = server._route_request(query.pack(), ("192.168.1.1", 1234), "UDP")
    response_msg = DNSMessage.unpack(response_bytes)

    server.cache.clear_cache.assert_called_once()
    assert response_msg.id == 0x7777


@patch("src.recursive_resolver.server.DNSListener")
def test_recursive_resolver_empty_questions(mock_listener_class):
    server = RecursiveResolver("127.0.0.1", 53)
    query = DNSMessage(id=0x1111, rd=1)

    response_bytes = server._route_request(query.pack(), ("192.168.1.1", 1234), "UDP")
    assert response_bytes == b""


@patch("src.recursive_resolver.server.DNSListener")
def test_recursive_resolver_handles_exception_gracefully(mock_listener_class):
    server = RecursiveResolver("127.0.0.1", 53)
    corrupted_data = b"\x00\x00\xff\xff\xff"

    response_bytes = server._route_request(corrupted_data, ("192.168.1.1", 1234), "UDP")
    assert response_bytes == b""