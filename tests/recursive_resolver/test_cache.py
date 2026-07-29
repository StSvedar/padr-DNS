import time
from unittest.mock import patch

from src.core.dns_message import DNSMessage
from src.core.dns_question import DNSQuestion
from src.core.enums import RecordType
from src.core.resource_record import ResourceRecord
from src.recursive_resolver.cache_manager import CacheManager


def test_cache_store_and_retrieve():
    cache = CacheManager()

    query = DNSMessage(id=100)
    query.questions.append(DNSQuestion("test.com", RecordType.A))

    response = DNSMessage(id=100)
    response.answers.append(ResourceRecord.create_A("test.com", "127.0.0.1", 60))

    cache.store(query, response)

    new_query = DNSMessage(id=200)
    new_query.questions.append(DNSQuestion("test.com", RecordType.A))

    cached_response = cache.retrieve(new_query)

    assert cached_response is not None
    assert cached_response.id == 200
    assert len(cached_response.answers) == 1
    assert cached_response.answers[0].rdata_str == "127.0.0.1"


def test_cache_lazy_expiration():
    cache = CacheManager()

    query = DNSMessage(id=100)
    query.questions.append(DNSQuestion("test.com", RecordType.A))

    response = DNSMessage(id=100)
    response.answers.append(ResourceRecord.create_A("test.com", "127.0.0.1", 1))

    cache.store(query, response)

    with patch("time.time", return_value=time.time() + 2):
        cached_response = cache.retrieve(query)

    assert cached_response is None
    assert len(cache.cache_data) == 0


def test_cache_clear_cache():
    cache = CacheManager()

    query = DNSMessage(id=100)
    query.questions.append(DNSQuestion("test.com", RecordType.A))

    response = DNSMessage(id=100)
    response.answers.append(ResourceRecord.create_A("test.com", "127.0.0.1", 60))

    cache.store(query, response)
    cache.clear_cache()

    assert len(cache.cache_data) == 0


def test_cache_retrieve_forces_aa_flag_to_zero():
    cache = CacheManager()

    query = DNSMessage(id=100)
    query.questions.append(DNSQuestion("auth.com", RecordType.A))

    response = DNSMessage(id=100)
    response.aa = 1
    response.answers.append(ResourceRecord.create_A("auth.com", "10.0.0.1", 300))

    cache.store(query, response)
    cached_response = cache.retrieve(query)

    assert cached_response.aa == 0


def test_cache_retrieve_decrements_ttl():
    cache = CacheManager()
    start_time = time.time()

    query = DNSMessage(id=100)
    query.questions.append(DNSQuestion("ttl.com", RecordType.A))

    response = DNSMessage(id=100)
    response.answers.append(ResourceRecord.create_A("ttl.com", "10.0.0.1", 100))

    with patch("time.time", return_value=start_time):
        cache.store(query, response)

    with patch("time.time", return_value=start_time + 40):
        cached_response = cache.retrieve(query)

    assert cached_response is not None
    assert cached_response.answers[0].ttl == 60


def test_cache_case_insensitive_matching():
    cache = CacheManager()

    query = DNSMessage(id=100)
    query.questions.append(DNSQuestion("MiXeD-CaSe.CoM", RecordType.A))

    response = DNSMessage(id=100)
    response.answers.append(ResourceRecord.create_A("mixed-case.com", "10.0.0.1", 300))

    cache.store(query, response)

    lookup_query = DNSMessage(id=200)
    lookup_query.questions.append(DNSQuestion("MIXED-CASE.COM", RecordType.A))

    cached_response = cache.retrieve(lookup_query)

    assert cached_response is not None
    assert cached_response.id == 200


def test_cache_retrieve_empty_questions():
    cache = CacheManager()
    query = DNSMessage(id=100)
    assert cache.retrieve(query) is None


def test_cache_retrieve_miss():
    cache = CacheManager()

    query = DNSMessage(id=100)
    query.questions.append(DNSQuestion("missing.com", RecordType.A))

    assert cache.retrieve(query) is None