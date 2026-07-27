import threading
from typing import Tuple
from src.core.enums import QR, Rcode
from src.core.dns_listener import DNSListener
from src.core.dns_message import DNSMessage
from src.recursive_resolver.iterative_engine import IterativeEngine

class RecursiveResolver:
    def __init__(self, listen_ip: str, listen_port: int, root_ips: list = None):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        
        self.engine = IterativeEngine(root_ips=root_ips)
        self.listener = DNSListener()

    def start_listening(self):
        """Launch UDP and TCP listeners."""
        print(f"[*] Booting up RecursiveResolver on {self.listen_ip}:{self.listen_port}")
        udp_thread = threading.Thread(target=self.listener.start_udp_listener, args=(self.listen_ip, self.listen_port, self._handle_client_request), daemon=True)
        tcp_thread = threading.Thread(target=self.listener.start_tcp_listener, args=(self.listen_ip, self.listen_port, self._handle_client_request), daemon=True)
        
        udp_thread.start()
        tcp_thread.start()
        return udp_thread, tcp_thread

    def _handle_client_request(self, data: bytes, addr: Tuple[str, int], protocol: str) -> bytes:
        try:
            query = DNSMessage().unpack(data)

            if not query.questions:
                return b""
            
            if query.rd == 1:
                response_msg = self.engine.resolve(query)
                response_msg.ra = 1 # Recursion Available
            else:
                # Reject the request if recursion is not desired
                response_msg = DNSMessage()
                response_msg.id = query.id
                response_msg.qr = QR.RESPONSE
                response_msg.rcode = Rcode.REFUSED

            return response_msg.pack()
        except Exception as e:
            print(f"[!] Error during resolution for client {addr}: {e}")
            return b""


if __name__ == "__main__":
    import os
    import time
    
    host = os.getenv("LISTEN_IP", "0.0.0.0")
    port = int(os.getenv("LISTEN_PORT", 53))
    root_ips = os.getenv("ROOT_IPS", "127.0.0.1").split(",")
    print(f"[*] Booting up RecursiveResolver on {host}:{port} with root IPs: {root_ips}")
    
    server = RecursiveResolver(host, port, root_ips)
    server.start_listening()
    print("[*] RecursiveResolver is listening. Press Ctrl+C to quit.")
    
    try:
        while True: time.sleep(3600)
    except KeyboardInterrupt:
        pass