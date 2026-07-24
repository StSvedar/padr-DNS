from unittest.mock import MagicMock
from src.core.dns_message import DNSMessage
from src.client.dns_client import DNSClient
from src.core.enums import QR

def test_dns_client_execute_query():
    client = DNSClient()
    
    fake_response = DNSMessage()
    fake_response.id = 1234
    fake_response.qr = QR.RESPONSE
    fake_response_bytes = fake_response.pack()
    
    client.requester = MagicMock()
    client.requester.send_udp_query.return_value = fake_response_bytes

    response = client.execute_query("test.com", "A", rd_flag=1, use_tcp=False, target_ip="10.0.0.1", port=53)

    client.requester.send_udp_query.assert_called_once()
    assert response is not None
    assert response.qr == QR.RESPONSE
    assert response.id == 1234