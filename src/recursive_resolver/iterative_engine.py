import socket
from src.core.enums import QR, Rcode, RecordType
from src.core.dns_message import DNSMessage
from src.core.dns_requester import DNSRequester

class IterativeEngine:
    def __init__(self, root_ips: list = None):
        self.root_ips = root_ips
        self.requester = DNSRequester()

    def resolve(self, query: DNSMessage, max_iterations: int=10 ) -> DNSMessage:
        if not query.questions:
            return query

        current_destinations = self.root_ips.copy()

        for _ in range(max_iterations):
            if not current_destinations:
                break

            target_ip = current_destinations[0]
            response = self._query_next_server(target_ip, query)

            if response:
                if response.answers or response.rcode != Rcode.NOERROR or response.aa == 1:
                    return response

                next_ips = self._extract_delegation(response)
                if next_ips:
                    current_destinations = next_ips
                else:
                    break
            else:   # Server did not respond
                current_destinations.pop(0)


        fail_response = DNSMessage()
        fail_response.id = query.id
        fail_response.qr = QR.RESPONSE
        fail_response.rcode = Rcode.SERVFAIL
        fail_response.questions = query.questions
        return fail_response

    def _query_next_server(self, ip: str, query: DNSMessage) -> DNSMessage:
        query.rd = 0
        packed_query = query.pack()

        raw_response = self.requester.send_udp_query(ip, 53, packed_query)
        if raw_response:
            resp_msg = DNSMessage().unpack(raw_response)
            
            if resp_msg.tc == 1:
                print(f"[IterativeEngine] Troncated datagram from {ip}, switching to TCP...")
                raw_response_tcp = self.requester.send_tcp_query(ip, 53, packed_query)
                if raw_response_tcp:
                    resp_msg_tcp = DNSMessage().unpack(raw_response_tcp)
                    return resp_msg_tcp
            return resp_msg
        return None

    def _extract_delegation(self, response: DNSMessage) -> list:
        ips = []
        for record in response.additional:
            if record.type == RecordType.A:
                ip = record.rdata_str
                ips.append(ip)
        return ips