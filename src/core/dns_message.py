import struct

from src.core.dns_question import DNSQuestion
from src.core.resource_record import ResourceRecord

class DNSMessage:
    def __init__(self, id: int = 0, qr: int = 0, opcode: int = 0, aa: int = 0, tc: int = 0, rd: int = 1,
                 ra: int = 0, z: int = 0, rcode: int = 0):
        self.id = id
        self.qr = qr
        self.opcode = opcode
        self.aa = aa
        self.tc = tc
        self.rd = rd
        self.ra = ra
        self.z = z
        self.rcode = rcode

        self.questions: list[DNSQuestion] = []
        self.answers: list[ResourceRecord] = []
        self.authority: list[ResourceRecord] = []
        self.additional: list[ResourceRecord] = []

    @property
    def qdcount(self):
        return len(self.questions)
    
    @property
    def ancount(self):
        return len(self.answers)
    
    @property
    def nscount(self):
        return len(self.authority)
    
    @property
    def arcount(self):
        return len(self.additional)
    
    @property
    def header(self):
        return {
            'id': self.id,

            'qr': self.qr,
            'opcode': self.opcode,
            'aa': self.aa,
            'tc': self.tc,
            'rd': self.rd,
            'ra': self.ra,
            'z': self.z,
            # ad and cd flags are not included in this implementation
            'rcode': self.rcode,

            'qdcount': self.qdcount,
            'ancount': self.ancount,
            'nscount': self.nscount,
            'arcount': self.arcount
        }

    def pack(self) -> bytes:
        flags = (
            (self.header.get('qr', 0) << 15) |
            (self.header.get('opcode', 0) << 11) |
            (self.header.get('aa', 0) << 10) |
            (self.header.get('tc', 0) << 9) |
            (self.header.get('rd', 0) << 8) |
            (self.header.get('ra', 0) << 7) |
            # ad and cd flags are ignored
            (self.header.get('z', 0) << 4) |
            self.header.get('rcode', 0)
        )

        qdcount = len(self.questions)
        ancount = len(self.answers)
        nscount = len(self.authority)
        arcount = len(self.additional)

        packet = bytearray()
        packet.extend(struct.pack('!HHHHHH', self.header.get('id', 0), flags, qdcount, ancount, nscount, arcount))

        domain_offsets = {}

        for q in self.questions:
            packet.extend(q.pack(packet, domain_offsets))

        for section in (self.answers, self.authority, self.additional):
            for rr in section:
                packet.extend(rr.pack(packet, domain_offsets))

        return bytes(packet)

    @classmethod
    def unpack(cls, data: bytes):
        msg = cls()
        header_fields = struct.unpack('!HHHHHH', data[:12])
        msg.id = header_fields[0]

        flags = header_fields[1]
        msg.qr = (flags >> 15) & 0x1
        msg.opcode = (flags >> 11) & 0xF
        msg.aa = (flags >> 10) & 0x1
        msg.tc = (flags >> 9) & 0x1
        msg.rd = (flags >> 8) & 0x1
        msg.ra = (flags >> 7) & 0x1
        # ad and cd flags are ignored
        msg.z = (flags >> 4) & 0x7
        msg.rcode = flags & 0xF

        qdcount = header_fields[2]
        ancount = header_fields[3]
        nscount = header_fields[4]
        arcount = header_fields[5]

        offset = 12

        for _ in range(qdcount):
            q, offset = DNSQuestion.unpack(data, offset)
            msg.questions.append(q)

        for _ in range(ancount):
            rr, offset = ResourceRecord.unpack(data, offset)
            msg.answers.append(rr)

        for _ in range(nscount):
            rr, offset = ResourceRecord.unpack(data, offset)
            msg.authority.append(rr)

        for _ in range(arcount):
            rr, offset = ResourceRecord.unpack(data, offset)
            msg.additional.append(rr)

        return msg