import socket
import struct
import threading
from typing import Callable, Tuple

class DNSListener:
    def __init__(self):
        pass

    def start_udp_listener(self, ip: str, port: int, on_message_received: Callable[[bytes, Tuple[str, int], str], bytes]):
        """
        Starts the UDP listening loop.
        Callback 3 parameters: (received_data, client_address, protocol) and must return the response to send in bytes.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind((ip, port))
            print(f"[*] DNS server (UDP) listening on {ip}:{port}")
            while True:
                data, addr = s.recvfrom(4096)
                response_data = on_message_received(data, addr, "UDP")
                if response_data:
                    s.sendto(response_data, addr)

    def start_tcp_listener(self, ip: str, port: int, on_message_received: Callable[[bytes, Tuple[str, int], str], bytes]):
        """
        Starts the TCP listening loop.
        Callback 3 parameters: (received_data, client_address, protocol) and must return the response to send in bytes.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((ip, port))
            s.listen(5)
            print(f"[*] DNS server (TCP) listening on {ip}:{port}")
            while True:
                conn, addr = s.accept()
                client_thread = threading.Thread(target=self._handle_tcp_client, args=(conn, addr, on_message_received))
                client_thread.start()

    def _handle_tcp_client(self, conn: socket.socket, addr: Tuple[str, int], on_message_received: Callable[[bytes, Tuple[str, int], str], bytes]):
        with conn:
            try:
                length_bytes = conn.recv(2)
                if len(length_bytes) < 2:
                    return
                msg_length = struct.unpack('!H', length_bytes)[0]
                
                data = b""
                while len(data) < msg_length:
                    size_to_read = msg_length - len(data)
                    chunk = conn.recv(size_to_read)
                    if not chunk:
                        break
                    data += chunk
                    
                response_data = on_message_received(data, addr, "TCP")
                
                if response_data:
                    payload = struct.pack('!H', len(response_data)) + response_data
                    conn.sendall(payload)
            except Exception as e:
                print(f"[!] TCP error with client {addr} : {e}")
