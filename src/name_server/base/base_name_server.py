from typing import Tuple
from src.core.enums import QR, Rcode, RecordType
from src.core.zone_data import ZoneData
from src.core.dns_message import DNSMessage
from src.recursive_resolver.server import RecursiveResolver # Import du parent

class BaseNameServer(RecursiveResolver): # <-- HÉRITAGE ICI
    def __init__(self, listen_ip: str, listen_port: int, initial_zone_data: dict = None, root_ips: list = None):
        super().__init__(listen_ip, listen_port, root_ips)
        
        self.zone_data = ZoneData(zone_dict=initial_zone_data or {})

    def _route_request(self, data: bytes, addr: Tuple[str, int], protocol: str) -> bytes:
        """Override parent method: Handle locally if authoritative, otherwise delegate to resolver."""
        try:
            query = DNSMessage.unpack(data)
            
            if not query.questions:
                return b""

            qname = str(query.questions[0].name).lower()
            
            is_authoritative = False
            if self.zone_data.contains_domain(qname) or self._find_delegation(qname):
                is_authoritative = True

            if is_authoritative:
                print(f"[*] Parsed DNS query (Authoritative): {query}")
                response_msg = self._build_response(query)
                print(f"[*] Built DNS response: {response_msg}")
                return response_msg.pack()
            else:
                return super()._route_request(data, addr, protocol)
                
        except Exception as e:
            print(f"[!] Error routing request from {addr} over {protocol}: {e}")
            return b""

    def _build_response(self, query: DNSMessage) -> DNSMessage:
        response = DNSMessage()
        response.id = query.id
        response.qr = QR.RESPONSE
        response.questions = query.questions

        if not query.questions:
            return response

        q = query.questions[0]
        qname = str(q.name).lower()
        qtype = q.qtype

        if self.zone_data.contains_domain(qname):
            response.aa = 1
            records = self.zone_data.get_records(qname, qtype)
            if records:
                response.answers.extend(records)
            else:
                response.rcode = Rcode.NOERROR

        else:
            delegation_domain = self._find_delegation(qname)
            
            is_our_zone_apex = False
            if delegation_domain:
                if (self.zone_data.get_records(delegation_domain, RecordType.A) or 
                    self.zone_data.get_records(delegation_domain, RecordType.AAAA)):
                    is_our_zone_apex = True

            if delegation_domain and not is_our_zone_apex:
                response.aa = 0
                self._build_delegation(delegation_domain, response)
            else:
                response.aa = 1
                response.rcode = Rcode.NXDOMAIN

                if delegation_domain:
                    soa_records = self.zone_data.get_records(delegation_domain, RecordType.SOA)
                        
                    if soa_records:
                        response.authority.extend(soa_records)
                    else:
                        ns_records = self.zone_data.get_records(delegation_domain, RecordType.NS)
                        if ns_records:
                            response.authority.extend(ns_records)

        return response

    def _find_delegation(self, qname: str) -> str:
        parts = qname.split('.')
        for i in range(len(parts)):
            parent = ".".join(parts[i:])
            if RecordType.NS in self.zone_data.get_types_for_name(parent):
                return parent
        return None

    def _build_delegation(self, domain: str, response: DNSMessage):
        ns_records = self.zone_data.get_records(domain, RecordType.NS)
        if ns_records:
            response.authority.extend(ns_records)

            for ns_rr in ns_records:
                ns_host = ns_rr.rdata_str.lower()
                glue_records = self.zone_data.get_records(ns_host, RecordType.A)
                if glue_records:
                    response.additional.extend(glue_records)
