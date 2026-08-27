from src.core.dns_message import DNSMessage
from src.core.dns_question import DNSQuestion
from src.core.enums import RecordType, Opcode, QR
from src.core.dns_requester import DNSRequester

class DNSClient:
    def __init__(self):
        self.__current_request_number = 0
        self.requester = DNSRequester()

    def _get_new_query_id(self):
        self.__current_request_number += 1
        query_id = self.__current_request_number % 65536
        return query_id

    def execute_query(self, domain: str, qtype: str, rd_flag: int, use_tcp: bool = False, target_ip: str = "127.0.0.1", port: int = 53) -> DNSMessage:
        query = DNSMessage(id = self._get_new_query_id(),
                           opcode=Opcode.QUERY,
                           rd=rd_flag,
                           qr=QR.QUERY)
        
        qtype_int = {'A': RecordType.A, 'NS': RecordType.NS, 'CNAME': RecordType.CNAME, 'TXT': RecordType.TXT, 'AAAA': RecordType.AAAA}.get(qtype.upper())
        if qtype_int is None:
            raise ValueError(f"Unknown record type: {qtype}")
        
        query.questions.append(DNSQuestion(domain, qtype_int))
        
        packed_query = query.pack()

        if use_tcp:
            raw_response = self.requester.send_tcp_query(target_ip, port, packed_query, timeout=15)
        else:
            raw_response = self.requester.send_udp_query(target_ip, port, packed_query, timeout=15)

        if not raw_response:
            raise ValueError(f"No response from server {target_ip}:{port} (Timeout or Refused).")

        try:
            response = DNSMessage.unpack(raw_response)
            return response
        except Exception as e:
            raise ValueError(f"Unable to decode received frame: {e}")
