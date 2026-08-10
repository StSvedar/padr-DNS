import struct
import ipaddress

from src.core.domain_name import DomainName
from src.core.enums import RecordType, RecordClass

class ResourceRecord:
    def __init__(self, domain: str | DomainName, type_: RecordType, rclass: RecordClass, ttl: int, rdata: bytes):
        self.domain = domain if isinstance(domain, DomainName) else DomainName(domain)
        self.type = type_
        self.rclass = rclass
        self.ttl = ttl
        self.rdata = rdata

    @property
    def rdata_str(self) -> str:
        if self.type == RecordType.A:
            return str(ipaddress.IPv4Address(self.rdata))
        if self.type == RecordType.AAAA:
            return str(ipaddress.IPv6Address(self.rdata))
        if self.type in (RecordType.NS, RecordType.CNAME):
            domain_obj, _ = DomainName.unpack(self.rdata, 0)
            return str(domain_obj)
        if self.type == RecordType.TXT:
            return self.rdata[1:].decode('utf-8', errors='ignore') if len(self.rdata) > 0 else ""
        
        return self.rdata.hex() if isinstance(self.rdata, bytes) else str(self.rdata)

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

    @classmethod
    def create_TXT(cls, name: str, text: str | bytes, ttl: int = 300) -> 'ResourceRecord':
        encoded_text = text.encode('utf-8') if isinstance(text, str) else text
        
        if len(encoded_text) > 255:
            raise ValueError("A single TXT string cannot exceed 255 bytes (RFC 1035)")
            
        rdata = bytes([len(encoded_text)]) + encoded_text
        return cls(name, RecordType.TXT, RecordClass.IN, ttl, rdata)

    @classmethod
    def create_UNKNOWN(cls, name: str, rdata: bytes, ttl: int) -> 'ResourceRecord':
        return cls(name, RecordType.UNKNOWN, RecordClass.IN, ttl, rdata)

    def pack(self, packet: bytearray, domain_offsets: dict) -> bytes:
        data = bytearray()
        data.extend(self.domain.pack(packet, domain_offsets))
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

        if not rtype in RecordType._value2member_map_:
            print(f"[!] Warning: Unknown record type {rtype} encountered while unpacking ResourceRecord.")
            rtype = RecordType.UNKNOWN

        if not rclass in RecordClass._value2member_map_:
            print(f"[!] Warning: Unknown record class {rclass} encountered while unpacking ResourceRecord.")
            rclass = RecordClass.IN # Default to IN if unknown to match from_dict behavior

        return cls(name, RecordType(rtype), RecordClass(rclass), ttl, rdata), offset

    def to_dict(self) -> dict:
        record_dict = {
            'class': self.rclass.name,
            'ttl': self.ttl,
            'rdata': self.rdata_str
        }
        return record_dict

    @classmethod
    def from_dict(cls, name: str, rtype_str: str, record_dict: dict) -> 'ResourceRecord':
        ttl = record_dict.get('ttl', 300)
        
        if rtype_str == 'A':
            return cls.create_A(name, record_dict.get('ip', record_dict.get('rdata')), ttl)
        if rtype_str == 'AAAA':
            return cls.create_AAAA(name, record_dict.get('ip', record_dict.get('rdata')), ttl)
        if rtype_str == 'NS':
            return cls.create_NS(name, record_dict.get('host', record_dict.get('rdata')), ttl)
        if rtype_str == 'CNAME':
            return cls.create_CNAME(name, record_dict.get('host', record_dict.get('rdata')), ttl)
        if rtype_str == 'TXT':
            return cls.create_TXT(name, record_dict.get('text', record_dict.get('rdata', '')), ttl)

        return cls.create_UNKNOWN(name, record_dict.get('rdata', b''), ttl)
        