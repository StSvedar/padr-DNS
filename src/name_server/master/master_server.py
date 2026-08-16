from typing import Tuple
from src.core.enums import RecordType
from src.name_server.base.base_name_server import BaseNameServer
from src.name_server.master.master_replication import MasterReplicationManager
from src.name_server.master.zone_loader import ZoneLoader
from src.core.dns_message import DNSMessage

class MasterServer(BaseNameServer):
    def __init__(self, listen_ip: str, listen_port: int, zone_filepath: str, slave_ips: list = None):
        super().__init__(listen_ip, listen_port, initial_zone_data=None)
        
        self.zone_loader = ZoneLoader(zone_filepath, self.on_zone_reload)
        self.replication_manager = MasterReplicationManager(self.zone_data, slave_ips or [])

        initial_data = self.zone_loader.read_config()
        if initial_data is not None:
            self.zone_data.load_from_dict(initial_data)
        else:
            print(f"[!] Failed to load initial zone data from {zone_filepath}. Starting with empty zone data.")

        self.zone_loader.listen_for_sighup()

    def on_zone_reload(self, new_data: dict):
        """Callback for hot reloading zone data."""
        print("[MasterServer] Hot reloading zone data...")
        self.zone_data.load_from_dict(new_data)
        
        self.replication_manager.send_notify_to_slaves()

    def _route_request(self, data: bytes, addr: Tuple[str, int], protocol: str) -> bytes:
        """Override the parent router to intercept AXFR transfer requests."""
        try:
            query = DNSMessage.unpack(data)
            
            if query.questions and query.questions[0].qtype == RecordType.AXFR:
                if protocol != "TCP":
                    print(f"[!] AXFR request refused by {addr}. TCP required.")
                    return b""
                response_msg = self.replication_manager.handle_axfr(query)
                return response_msg.pack()

            return super()._route_request(data, addr, protocol)
        except Exception as e:
            print(f"[!] MasterServer error ({addr}): {e}")
            return b""
        

if __name__ == "__main__":
    import os
    import time
    
    host = os.getenv("LISTEN_IP", "0.0.0.0")
    port = int(os.getenv("LISTEN_PORT", 53))
    zone_file = os.getenv("ZONE_FILE", "/app/zones/default.json")
    
    slave_ips_raw = os.getenv("SLAVE_IPS", "")
    slave_ips = slave_ips_raw.split(",") if slave_ips_raw else []
    
    print(f"[*] Bootstrapping master server on {host}:{port} with zone {zone_file} (Slaves: {slave_ips})")
    
    server = MasterServer(host, port, zone_file, slave_ips)
    server.start_listening()
    
    try:
        while True: time.sleep(3600)
    except KeyboardInterrupt:
        pass