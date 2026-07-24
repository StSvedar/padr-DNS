from src.core.dns_message import DNSMessage
from src.core.domain_name import DomainName
from src.core.resource_record import ResourceRecord
from src.core.enums import Rcode, RecordType, QR

class AuthoritativeEngine:
    def __init__(self, initial_zone_data: dict = None):
        self.zone_data = {}
        if initial_zone_data:
            self.update_data(initial_zone_data)

    def update_data(self, new_data: dict):
        """Convert the provided zone data into ResourceRecord objects and store them in RAM."""
        parsed_zone = {}
        for name, types in new_data.items():
            parsed_zone[name] = {}
            for rtype_str, records in types.items():
                parsed_zone[name][rtype_str] = [
                    ResourceRecord.from_dict(name, rtype_str, r) for r in records
                ]
        self.zone_data = parsed_zone
        print("[AuthoritativeEngine] Zone data converted to ResourceRecords and updated in RAM.")
        print(f"[AuthoritativeEngine] Current zone data: {self.zone_data}")

    def build_response(self, query: DNSMessage) -> DNSMessage:
        response = DNSMessage()
        response.id = query.id
        response.qr = QR.RESPONSE
        response.questions = query.questions

        if not query.questions:
            return response

        # DNS does not support multiple questions because of the ambiguity it would create in the response. So we only process the first question.
        q = query.questions[0]
        qname = str(q.name).lower()
        qtype_str = RecordType(q.qtype).name

        if qname in self.zone_data:
            response.aa = 1
            node = self.zone_data[qname]

            if qtype_str in node:
                response.answers.extend(node[qtype_str])
        else:
            delegation_domain = self._find_delegation(qname)
            if delegation_domain:
                response.aa = 0
                self._build_delegation(delegation_domain, response)
            else:
                response.aa = 1
                response.rcode = Rcode.NXDOMAIN

        return response

    def _find_delegation(self, qname: str) -> str:
        parts = qname.split('.')
        for i in range(len(parts)):
            parent = ".".join(parts[i:])
            if parent in self.zone_data and "NS" in self.zone_data[parent]:
                return parent
        return None

    def _build_delegation(self, domain: str, response: DNSMessage):
        if "NS" in self.zone_data[domain]:
            response.authority.extend(self.zone_data[domain]["NS"])

            for ns_rr in self.zone_data[domain]["NS"]:
                ns_host = ns_rr.rdata_str.lower()

                if ns_host in self.zone_data and "A" in self.zone_data[ns_host]:
                    response.additional.extend(self.zone_data[ns_host]["A"])
