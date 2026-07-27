from unittest.mock import MagicMock, patch

from src.core.dns_message import DNSMessage
from src.core.dns_question import DNSQuestion
from src.core.enums import RecordType
from src.recursive_resolver.server import RecursiveResolver


@patch("src.recursive_resolver.server.DNSListener")
def test_recursive_resolver_refuses_non_recursive_queries(mock_listener_class):
    server = RecursiveResolver("127.0.0.1", 53)
    server.engine.resolve = MagicMock()

    query = DNSMessage(id=0x9999, rd=0)
    query.questions.append(DNSQuestion("test.com", RecordType.A))

    response_bytes = server._handle_client_request(query.pack(), ("192.168.1.1", 1234), "UDP")
    response_msg = DNSMessage.unpack(response_bytes)

    assert response_msg.rcode == 5
    server.engine.resolve.assert_not_called()