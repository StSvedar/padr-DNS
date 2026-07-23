import struct
import ipaddress

from src.core.domain_name import DomainName
from src.core.enums import RecordType, RecordClass

class ResourceRecord:
    def __init__(self, name: str | DomainName, type_: RecordType, rclass: RecordClass, ttl: int, rdata: bytes):
        self.name = name if isinstance(name, DomainName) else DomainName(name)
        self.type = type_
        self.rclass = rclass
        self.ttl = ttl
        self.rdata = rdata

    @property
    def rdlength(self) -> int:
        return len(self.rdata)

    @classmethod
    def create_A(cls, name: str, ip: str, ttl: int = 300) -> 'ResourceRecord':
        rdata = ipaddress.IPv4Address(ip).packed
        return cls(name, RecordType.A, RecordClass.IN, ttl, rdata)

    @classmethod
    def create_AAAA(cls, name: str, ip: str, ttl: int = 300) -> 'ResourceRecord':
        rdata = ipaddress.IPv6Address(ip).packed
        return cls(name, RecordType.AAAA, RecordClass.IN, ttl, rdata)

    @classmethod
    def create_NS(cls, name: str, target_host: str, ttl: int = 86400) -> 'ResourceRecord':
        rdata = DomainName(target_host).pack(bytearray(), {})
        return cls(name, RecordType.NS, RecordClass.IN, ttl, rdata)

    @classmethod
    def create_CNAME(cls, name: str, target_host: str, ttl: int = 300) -> 'ResourceRecord':
        rdata = DomainName(target_host).pack(bytearray(), {})
        return cls(name, RecordType.CNAME, RecordClass.IN, ttl, rdata)

    def pack(self, packet: bytearray, domain_offsets: dict) -> bytes:
        data = bytearray()
        data.extend(self.name.pack(packet, domain_offsets))
        data.extend(struct.pack('!HHIH', self.type, self.rclass, self.ttl, self.rdlength))
        data.extend(self.rdata)
        return bytes(data)

    @classmethod
    def unpack(cls, data: bytes, offset: int) -> tuple['ResourceRecord', int]:
        name, offset = DomainName.unpack(data, offset)
        rtype, rclass, ttl, rdlength = struct.unpack('!HHIH', data[offset:offset+10])
        offset += 10
        rdata = data[offset:offset+rdlength]
        offset += rdlength
        return cls(name, RecordType(rtype), RecordClass(rclass), ttl, rdata), offset
