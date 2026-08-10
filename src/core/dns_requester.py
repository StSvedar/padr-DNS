import socket
import struct

class DNSRequester:
    def __init__(self):
        pass

    def send_udp_query(self, ip: str, port: int, data: bytes, timeout: int = 5) -> bytes:
        """Send a UDP query and wait for the response."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(timeout)
            try:
                s.sendto(data, (ip, port))
                response, _ = s.recvfrom(4096)
                return response
            except (socket.timeout, OSError) as e:
                print(f"[!] UDP error with {ip}:{port} : {e}")
                return b""

    def send_tcp_query(self, ip: str, port: int, data: bytes, timeout: int = 5) -> bytes:
        """Send a TCP query (with length prefix) and wait for the response."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            try:
                s.connect((ip, port))
                
                payload = self._add_tcp_length_prefix(data)
                s.sendall(payload)
                
                length_bytes = s.recv(2)
                if len(length_bytes) < 2:
                    return b""
                msg_length = struct.unpack('!H', length_bytes)[0]
                
                response = b""
                while len(response) < msg_length:
                    size_to_read = msg_length - len(response)
                    chunk = s.recv(size_to_read)
                    if not chunk:
                        break
                    response += chunk
                    
                return response
            except socket.timeout:
                print(f"[!] TCP timeout : No response from {ip}:{port}")
                return b""
            except ConnectionRefusedError:
                print(f"[!] TCP connection refused by {ip}:{port}")
                return b""

    def _add_tcp_length_prefix(self, data: bytes) -> bytes:
        """Adds the 2-byte prefix required by RFC 1035 for DNS over TCP."""
        return struct.pack('!H', len(data)) + data
