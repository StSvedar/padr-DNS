import struct
import pytest
from unittest.mock import patch, MagicMock
from src.core.dns_listener import DNSListener


@patch('src.core.dns_listener.socket.socket')
def test_dns_listener_udp_callback(mock_socket_class):
    mock_socket_instance = MagicMock()
    mock_socket_class.return_value.__enter__.return_value = mock_socket_instance
    
    mock_socket_instance.recvfrom.side_effect = [
        (b"incoming_data", ("192.168.1.10", 12345)), 
        Exception("Stop Loop")
    ]
    
    mock_callback = MagicMock(return_value=b"response_data")
    
    with pytest.raises(Exception, match="Stop Loop"):
        dns_listener = DNSListener()
        dns_listener.start_udp_listener("127.0.0.1", 53, on_message_received=mock_callback)
    
    mock_socket_instance.bind.assert_called_once_with(("127.0.0.1", 53))
    mock_callback.assert_called_once_with(b"incoming_data", ("192.168.1.10", 12345), "UDP")
    mock_socket_instance.sendto.assert_called_once_with(b"response_data", ("192.168.1.10", 12345))


@patch('src.core.dns_listener.threading.Thread')
@patch('src.core.dns_listener.socket.socket')
def test_dns_listener_tcp_callback(mock_socket_class, mock_thread_class):
    mock_socket_instance = MagicMock()
    mock_socket_class.return_value.__enter__.return_value = mock_socket_instance

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    
    mock_conn.recv.side_effect = [
        struct.pack('!H', 13), 
        b"incoming_data"
    ]
    
    mock_socket_instance.accept.side_effect = [
        (mock_conn, ("192.168.1.10", 12345)),
        Exception("Stop Loop")
    ]

    def run_thread_inline(*args, **kwargs):
        thread_mock = MagicMock()
        target = kwargs.get('target')
        thread_args = kwargs.get('args', ())
        thread_mock.start.side_effect = lambda: target(*thread_args)
        return thread_mock

    mock_thread_class.side_effect = run_thread_inline

    mock_callback = MagicMock(return_value=b"response_data")

    with pytest.raises(Exception, match="Stop Loop"):
        dns_listener = DNSListener()
        dns_listener.start_tcp_listener("127.0.0.1", 53, on_message_received=mock_callback)

    mock_socket_instance.bind.assert_called_once_with(("127.0.0.1", 53))
    mock_callback.assert_called_once_with(b"incoming_data", ("192.168.1.10", 12345), "TCP")
    
    expected_payload = struct.pack('!H', len(b"response_data")) + b"response_data"
    mock_conn.sendall.assert_called_once_with(expected_payload)