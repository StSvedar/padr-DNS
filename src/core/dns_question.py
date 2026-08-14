import struct

from src.core.domain_name import DomainName
from src.core.enums import RecordType, RecordClass

class DNSQuestion:
    def __init__(self, name: str | DomainName, qtype: RecordType, qclass: RecordClass = RecordClass.IN):
        self.name = name if isinstance(name, DomainName) else DomainName(name)
        self.qtype = qtype
        self.qclass = qclass

    def __str__(self):
        return f"DNSQuestion(name={self.name}, qtype={self.qtype}, qclass={self.qclass})"

    def pack(self, packet: bytearray, domain_offsets: dict) -> bytes:
        data = bytearray()
        data.extend(self.name.pack(packet, domain_offsets))
        data.extend(struct.pack('!HH', self.qtype, self.qclass))
        return bytes(data)

    @classmethod
    def unpack(cls, data: bytes, offset: int) -> tuple['DNSQuestion', int]:
        name, offset = DomainName.unpack(data, offset)
        qtype, qclass = struct.unpack('!HH', data[offset:offset+4])
        return cls(name, RecordType(qtype), RecordClass(qclass)), offset + 4