
from enum import IntEnum

class RecordType(IntEnum):
    UNKNOWN = 0
    A = 1
    NS = 2
    CNAME = 5
    SOA = 6
    PTR = 12
    MX = 15
    TXT = 16
    AAAA = 28
    AXFR = 252
    ANY = 255

class RecordClass(IntEnum):
    IN = 1
    CH = 3
    HS = 4

class Opcode(IntEnum):
    QUERY = 0
    IQUERY = 1
    STATUS = 2
    NOTIFY = 4
    UPDATE = 5

class Rcode(IntEnum):
    NOERROR = 0
    FORMERR = 1
    SERVFAIL = 2
    NXDOMAIN = 3
    NOTIMP = 4
    REFUSED = 5

class QR(IntEnum):
    QUERY = 0
    RESPONSE = 1