import json
from src.core.enums import QR, RecordType, RecordClass, Opcode
from src.core.dns_message import DNSMessage
from src.core.dns_question import DNSQuestion
from src.core.resource_record import ResourceRecord
from src.core.dns_requester import DNSRequester
from src.core.zone_data import ZoneData

class MasterReplicationManager:
    def __init__(self, zone_data_ref: ZoneData, slave_ips: list):
        self.zone_data_ref = zone_data_ref
        self.slave_ips = slave_ips
        self.requester = DNSRequester()

    def handle_axfr(self, query: DNSMessage) -> DNSMessage:
        response = DNSMessage(id=query.id, qr=QR.RESPONSE, aa=1)
        response.questions = query.questions
        
        zone_dict = self.zone_data_ref.to_dict() if hasattr(self.zone_data_ref, "to_dict") else self.zone_data_ref
        zone_bytes = json.dumps(zone_dict).encode('utf-8')
        
        qname = str(query.questions[0].name) if query.questions else '.'
        response.answers.append(ResourceRecord(qname, RecordType.AXFR, RecordClass.IN, 0, zone_bytes))
        
        print(f"[MasterReplication] AXFR transfer generated ({len(zone_bytes)} bytes).")
        return response

    def send_notify_to_slaves(self, domain: str = "."):
        notify_msg = DNSMessage(opcode=Opcode.NOTIFY)
        
        notify_msg.questions.append(DNSQuestion(domain, RecordType.SOA, RecordClass.IN))
        
        packed_notify = notify_msg.pack()
        
        for slave_ip in self.slave_ips:
            print(f"[MasterReplication] Sending NOTIFY to {slave_ip}")
            self.requester.send_udp_query(slave_ip, 53, packed_notify, timeout=2)