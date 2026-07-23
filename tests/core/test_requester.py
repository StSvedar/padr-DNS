import struct
import pytest
from unittest.mock import patch, MagicMock
import src.core.dns_requester as dns_requester

@patch('src.core.dns_requester.socket.socket')
def test_dns_requester_udp(mock_socket_class):
    mock_socket_instance = MagicMock()
    mock_socket_class.return_value.__enter__.return_value = mock_socket_instance
    mock_socket_instance.recvfrom.return_value = (b"fake_udp_response", ("127.0.0.1", 53))
    
    payload = b"fake_query"
    response = dns_requester.send_udp_query("8.8.8.8", 53, payload)
    
    mock_socket_instance.sendto.assert_called_once_with(payload, ("8.8.8.8", 53))
    mock_socket_instance.recvfrom.assert_called_once()
    assert response == b"fake_udp_response"

@patch('src.core.dns_requester.socket.socket')
def test_dns_requester_tcp_prefix(mock_socket_class):
    mock_socket_instance = MagicMock()
    mock_socket_class.return_value.__enter__.return_value = mock_socket_instance
    
    mock_socket_instance.recv.side_effect = [struct.pack('!H', 12), b"fake_tcp_msg"]
    
    payload = b"1234567890" # 10 bytes
    response = dns_requester.send_tcp_query("8.8.8.8", 53, payload)
    
    expected_sent_data = struct.pack('!H', 10) + payload
    mock_socket_instance.sendall.assert_called_once_with(expected_sent_data)
    assert response == b"fake_tcp_msg"