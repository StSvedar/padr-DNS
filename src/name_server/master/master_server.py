from src.name_server.base.base_name_server import BaseNameServer
from src.name_server.master.zone_loader import ZoneLoader

class MasterServer(BaseNameServer):
    def __init__(self, listen_ip: str, listen_port: int, zone_filepath: str):
        super().__init__(listen_ip, listen_port, initial_zone_data=None)
        
        self.zone_loader = ZoneLoader(zone_filepath, self.on_zone_reload)

        initial_data = self.zone_loader.read_config()
        if initial_data is not None:
            self.zone_data.load_from_dict(initial_data)
        else:
            print(f"[!] Failed to load initial zone data from {zone_filepath}. Starting with empty zone data.")

        self.zone_loader.listen_for_sighup()

    def on_zone_reload(self, new_data: dict):
        """Callback for hot-reloading zone data."""
        print("[MasterServer] Hot-reloading zone data...")
        self.zone_data.load_from_dict(new_data)
        

if __name__ == "__main__":
    import os
    import time
    
    host = os.getenv("LISTEN_IP", "0.0.0.0")
    port = int(os.getenv("LISTEN_PORT", 53))
    zone_file = os.getenv("ZONE_FILE", "/app/zones/default.json")
    
    print(f"[*] Bootstrapping master server on {host}:{port} with zone {zone_file}")
    
    server = MasterServer(host, port, zone_file)
    server.start_listening()
    
    try:
        while True: time.sleep(3600)
    except KeyboardInterrupt:
        pass