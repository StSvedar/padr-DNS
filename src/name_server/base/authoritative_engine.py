from src.core.dns_message import DNSMessage
from src.core.zone_data import ZoneData
from src.core.enums import Rcode, RecordType, QR

class AuthoritativeEngine:
    def __init__(self, initial_zone_data: dict = {}):
        self.zone_data = ZoneData(zone_dict=initial_zone_data)

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
