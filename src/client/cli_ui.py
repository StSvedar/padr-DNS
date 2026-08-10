import argparse
import socket
from src.core.enums import RecordType
from src.core.resource_record import ResourceRecord
from src.core.dns_message import DNSMessage
from src.client.dns_client import DNSClient

class CLI_UI:
    def __init__(self):
        self.client = DNSClient()

    def parse_arguments(self, args_list=None):
        """Configure and parse arguments passed from the command line."""
        parser = argparse.ArgumentParser(description="DNS Client tool")
        
        parser.add_argument("domain", help="Domain name to resolve (e.g. google.com or flush.cache.local)")
        parser.add_argument("-s", "--server", default="127.0.0.1", help="DNS server IP to query (default: 127.0.0.1)")
        parser.add_argument("-p", "--port", type=int, default=53, help="DNS server port (default: 53)")
        parser.add_argument("-t", "--type", default="A", choices=["A", "AAAA", "NS", "TXT"], help="Record type")
        parser.add_argument("--no-recurse", action="store_true", help="Disable recursion (RD=0)")
        parser.add_argument("--tcp", action="store_true", help="Force TCP usage")
        
        return parser.parse_args(args_list)

    def display_results(self, response: DNSMessage):
        """Display the result in a readable format."""
        print(f"\n;; ->>HEADER<<- opcode: {response.header.get('opcode', 0)}, "
              f"status: {response.header.get('rcode', 0)}, "
              f"id: {response.header.get('id', 0)}")
        
        flags = []
        if response.header.get('qr'): flags.append("qr")
        if response.header.get('aa'): flags.append("aa")
        if response.header.get('tc'): flags.append("tc")
        if response.header.get('rd'): flags.append("rd")
        if response.header.get('ra'): flags.append("ra")
        print(f";; flags: {' '.join(flags)}; "
              f"QUERY: {response.header.get('qdcount', 0)}, "
              f"ANSWER: {response.header.get('ancount', 0)}, "
              f"AUTHORITY: {response.header.get('nscount', 0)}, "
              f"ADDITIONAL: {response.header.get('arcount', 0)}\n")

        self._print_section("ANSWER SECTION:", response.answers)
        self._print_section("AUTHORITY SECTION:", response.authority)
        self._print_section("ADDITIONAL SECTION:", response.additional)
        print(";; End of resolution.\n")

    def display_error(self, msg: str):
        print(f"[ERROR] {msg}")

    def _print_section(self, title: str, section_data: list[ResourceRecord]):
        if not section_data:
            return
        print(f";; {title}")
        for record in section_data:
            qtype_str = self._get_type_str(record.type)
            rdata_str = self._format_rdata(record.type, record.rdata)
            print(f"{record.domain}\t{record.ttl}\tIN\t{qtype_str}\t{rdata_str}")
        print()

    def _get_type_str(self, qtype: int) -> str:
        return {RecordType.A: 'A', RecordType.NS: 'NS', RecordType.CNAME: 'CNAME', RecordType.TXT: 'TXT', RecordType.AAAA: 'AAAA'}.get(qtype, str(qtype))

    def _format_rdata(self, qtype: int, rdata: bytes) -> str:
        try:
            if qtype == RecordType.A:
                return socket.inet_ntoa(rdata)
            elif qtype == RecordType.AAAA:
                return socket.inet_ntop(socket.AF_INET6, rdata)
            elif qtype == RecordType.TXT:
                return rdata[1:].decode('utf-8') if len(rdata) > 0 else ""
            else:
                return f"<binary: {rdata.hex()}>"
        except Exception:
            return f"<parse error: {rdata.hex()}>"

    def start(self, args_list=None):
        args = self.parse_arguments(args_list)
        rd_flag = 0 if args.no_recurse else 1
        print(f"Querying {args.server}:{args.port} for {args.domain} (type {args.type}, RD={rd_flag}, TCP={args.tcp})...")

        try:
            response = self.client.execute_query(args.domain, args.type, rd_flag, args.tcp, args.server, args.port)
        except ValueError as e:
            self.display_error(e)
            return

        if response:
            self.display_results(response)

if __name__ == "__main__":
    cli_ui = CLI_UI()
    cli_ui.start()