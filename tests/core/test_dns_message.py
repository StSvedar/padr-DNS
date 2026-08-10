import ipaddress
import pytest

from src.core.dns_message import DNSMessage
from src.core.dns_question import DNSQuestion
from src.core.resource_record import ResourceRecord
from src.core.enums import RecordType, RecordClass


def test_dns_message_header_pack_unpack():
    msg = DNSMessage()
    msg.id = 0xABCD
    msg.qr = 1
    msg.rd = 1

    packed = msg.pack()
    assert len(packed) >= 12
    
    new_msg = DNSMessage.unpack(packed)
    
    assert new_msg.id == 0xABCD
    assert new_msg.qr == 1
    assert new_msg.rd == 1


def test_dns_message_header_flags():
    msg = DNSMessage(
        id=0x1234,
        qr=1,
        opcode=2,
        aa=1,
        tc=0,
        rd=1,
        ra=1,
        z=0,
        rcode=3
    )

    packed = msg.pack()
    unpacked = DNSMessage.unpack(packed)

    assert unpacked.id == 0x1234
    assert unpacked.qr == 1
    assert unpacked.opcode == 2
    assert unpacked.aa == 1
    assert unpacked.tc == 0
    assert unpacked.rd == 1
    assert unpacked.ra == 1
    assert unpacked.z == 0
    assert unpacked.rcode == 3


def test_dns_message_question_serialization():
    msg = DNSMessage()
    msg.questions.append(DNSQuestion('www.henallux.be', RecordType.A, RecordClass.IN))
    
    packed = msg.pack()
    new_msg = DNSMessage.unpack(packed)
    
    assert len(new_msg.questions) == 1
    assert str(new_msg.questions[0].name) == 'www.henallux.be'
    assert new_msg.questions[0].qtype == RecordType.A
    assert new_msg.questions[0].qclass == RecordClass.IN


def test_dns_message_with_answers_roundtrip():
    msg = DNSMessage(id=42, qr=1, aa=1, rcode=0)
    msg.questions.append(DNSQuestion('example.com', RecordType.A, RecordClass.IN))
    
    msg.answers.append(ResourceRecord.create_A('example.com', '192.168.1.10', ttl=300))
    msg.answers.append(ResourceRecord.create_AAAA('example.com', '2001:db8::1', ttl=600))
    
    packed = msg.pack()
    unpacked = DNSMessage.unpack(packed)
    
    assert unpacked.qdcount == 1
    assert unpacked.ancount == 2
    
    ans_a = unpacked.answers[0]
    assert str(ans_a.domain) == 'example.com'
    assert ans_a.type == RecordType.A
    assert ans_a.ttl == 300
    assert ipaddress.IPv4Address(ans_a.rdata) == ipaddress.IPv4Address('192.168.1.10')
    
    ans_aaaa = unpacked.answers[1]
    assert str(ans_aaaa.domain) == 'example.com'
    assert ans_aaaa.type == RecordType.AAAA
    assert ans_aaaa.ttl == 600
    assert ipaddress.IPv6Address(ans_aaaa.rdata) == ipaddress.IPv6Address('2001:db8::1')


def test_dns_message_full_sections_authority_additional():
    msg = DNSMessage(id=100, qr=1)
    msg.questions.append(DNSQuestion('domain.be', RecordType.A, RecordClass.IN))
    
    msg.authority.append(ResourceRecord.create_NS('domain.be', 'ns1.domain.be', ttl=86400))
    
    msg.additional.append(ResourceRecord.create_A('ns1.domain.be', '10.0.0.1', ttl=3600))
    
    packed = msg.pack()
    unpacked = DNSMessage.unpack(packed)
    
    assert unpacked.qdcount == 1
    assert unpacked.ancount == 0
    assert unpacked.nscount == 1
    assert unpacked.arcount == 1
    
    ns_rr = unpacked.authority[0]
    assert str(ns_rr.domain) == 'domain.be'
    assert ns_rr.type == RecordType.NS
    assert ns_rr.ttl == 86400
    
    glue_rr = unpacked.additional[0]
    assert str(glue_rr.domain) == 'ns1.domain.be'
    assert glue_rr.type == RecordType.A
    assert ipaddress.IPv4Address(glue_rr.rdata) == ipaddress.IPv4Address('10.0.0.1')


def test_dns_message_cname_record():
    msg = DNSMessage(id=77, qr=1)
    msg.questions.append(DNSQuestion('alias.com', RecordType.A, RecordClass.IN))
    msg.answers.append(ResourceRecord.create_CNAME('alias.com', 'target.com', ttl=120))
    
    packed = msg.pack()
    unpacked = DNSMessage.unpack(packed)
    
    cname_rr = unpacked.answers[0]
    assert cname_rr.type == RecordType.CNAME
    assert str(cname_rr.domain) == 'alias.com'
    assert cname_rr.ttl == 120


def test_dns_name_compression():
    msg = DNSMessage()
    msg.questions.append(DNSQuestion('test.com', RecordType.A, RecordClass.IN))
    msg.questions.append(DNSQuestion('test.com', RecordType.AAAA, RecordClass.IN))
    
    packed = msg.pack()
    assert len(packed) == 32
    
    new_msg = DNSMessage.unpack(packed)
    
    assert str(new_msg.questions[0].name) == 'test.com'
    assert str(new_msg.questions[1].name) == 'test.com'


def test_dns_name_compression_across_all_sections():
    msg = DNSMessage(id=123, qr=1)
    msg.questions.append(DNSQuestion('sub.example.com', RecordType.A, RecordClass.IN))
    
    msg.answers.append(ResourceRecord.create_A('sub.example.com', '1.2.3.4'))
    
    msg.authority.append(ResourceRecord.create_NS('example.com', 'ns1.example.com'))
    
    packed = msg.pack()
    unpacked = DNSMessage.unpack(packed)
    
    assert str(unpacked.questions[0].name) == 'sub.example.com'
    assert str(unpacked.answers[0].domain) == 'sub.example.com'
    assert str(unpacked.authority[0].domain) == 'example.com'