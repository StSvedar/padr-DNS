from typing import Tuple
from src.core.enums import Opcode
from src.core.dns_message import DNSMessage
from src.name_server.base.base_name_server import BaseNameServer
from src.name_server.slave.slave_replication import SlaveReplicationManager

class SlaveServer(BaseNameServer):
    def __init__(self, listen_ip: str, listen_port: int, master_ip: str, master_port: int = 53):
        super().__init__(listen_ip, listen_port, initial_zone_data={})
        
        self.replication_manager = SlaveReplicationManager(
            master_ip, master_port, 
            on_sync_callback=self.zone_data.load_from_dict
        )

    def sync_from_master(self):
        """Fetch the zone from the master during startup or on demand."""
        self.replication_manager.request_axfr()

    def _route_request(self, data: bytes, addr: Tuple[str, int], protocol: str) -> bytes:
        """Override the router to intercept NOTIFY messages."""
        try:
            query = DNSMessage.unpack(data)
            
            if query.opcode == Opcode.NOTIFY:
                response_msg = self.replication_manager.handle_notify(query)
                return response_msg.pack()

            return super()._route_request(data, addr, protocol)
        except Exception as e:
            print(f"[!] SlaveServer error ({addr}): {e}")
            return b""
        

if __name__ == "__main__":
    import os
    import time
    
    host = os.getenv("LISTEN_IP", "0.0.0.0")
    port = int(os.getenv("LISTEN_PORT", 53))
    master_ip = os.getenv("MASTER_IP", "127.0.0.1")
    master_port = int(os.getenv("MASTER_PORT", 53))
    
    print(f"[*] Starting SlaveServer on {host}:{port} (target master: {master_ip}:{master_port})")
    
    server = SlaveServer(host, port, master_ip, master_port)
    server.start_listening()
    
    server.sync_from_master()
    
    print("[*] SlaveServer is listening. Press Ctrl+C to quit.")
    
    try:
        while True: time.sleep(3600)
    except KeyboardInterrupt:
        pass