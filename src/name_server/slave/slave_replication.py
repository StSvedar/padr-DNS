import json
from typing import Callable
from src.core.dns_message import DNSMessage
from src.core.dns_requester import DNSRequester
from src.core.dns_question import DNSQuestion
from src.core.enums import QR, RecordClass, RecordType

class SlaveReplicationManager:
    def __init__(self, master_ip: str, master_port: int, on_sync_callback: Callable[[dict], None]):
        self.master_ip = master_ip
        self.master_port = master_port
        self.on_sync_callback = on_sync_callback
        self.requester = DNSRequester()
        self.current_serial = 0

    def request_axfr(self):
        """Request the full zone from the master over TCP."""
        query = DNSMessage(id=9999)
        query.questions.append(DNSQuestion(name='.', qtype=RecordType.AXFR, qclass=RecordClass.IN))
        
        print(f"[*] Requesting AXFR transfer from {self.master_ip}:{self.master_port} (TCP)...")
        raw_response = self.requester.send_tcp_query(self.master_ip, self.master_port, query.pack())
        
        if raw_response:
            try:
                response = DNSMessage.unpack(raw_response)

                if response.answers and response.answers[0].type == RecordType.AXFR:
                    json_payload = response.answers[0].rdata.decode('utf-8')
                    new_zone_data = json.loads(json_payload)
                    
                    print("[*] AXFR succeeded. Updating local zone data.")
                    self.on_sync_callback(new_zone_data)
                    self.current_serial += 1
            except Exception as e:
                print(f"[!] Error while decoding AXFR: {e}")

    def handle_notify(self, query: DNSMessage) -> DNSMessage:
        """Acknowledge a master NOTIFY and trigger synchronization."""
        print("[SlaveReplication] NOTIFY received from master.")
        
        response = DNSMessage(id=query.id, qr=QR.RESPONSE, opcode=4)
        response.questions = query.questions
        
        self.request_axfr()
        
        return response