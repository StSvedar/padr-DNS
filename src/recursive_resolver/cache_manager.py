import time
import copy
from src.core.dns_message import DNSMessage
from src.core.enums import RecordType, Rcode

class CacheManager:
    def __init__(self):
        self.cache_data = {}

    def store(self, query: DNSMessage, response: DNSMessage):
        """Store a response in the cache using the lowest applicable TTL."""
        if not query.questions or not response:
            return

        q = query.questions[0]
        cache_key = (str(q.name).lower(), q.qtype)

        min_ttl = 300
        if response.rcode == Rcode.NOERROR and response.answers:
            min_ttl = min(ans.ttl for ans in response.answers)
        elif response.rcode == Rcode.NXDOMAIN and response.authority:
            for auth in response.authority:
                if auth.type == RecordType.SOA:
                    min_ttl = auth.ttl
                    break

        expires_at = time.time() + min_ttl
        
        self.cache_data[cache_key] = {
            'response': copy.deepcopy(response),
            'expires_at': expires_at
        }
        print(f"[CacheManager] Cached {cache_key} (TTL: {min_ttl}s)")

    def retrieve(self, query: DNSMessage) -> DNSMessage:
        """Return a cached response when present and still valid."""
        if not query.questions:
            return None

        q = query.questions[0]
        cache_key = (str(q.name).lower(), q.qtype)

        if cache_key in self.cache_data:
            entry = self.cache_data[cache_key]
            now = time.time()

            if now > entry['expires_at']:
                print(f"[CacheManager] Cache expired for {cache_key}")
                del self.cache_data[cache_key]
                return None

            print(f"[CacheManager] Cache hit for {cache_key}")
            
            cached_response = copy.deepcopy(entry['response'])
            
            cached_response.id = query.id
            cached_response.aa = 0
            remaining_ttl = max(0, int(entry['expires_at'] - now))

            for section in (cached_response.answers, cached_response.authority, cached_response.additional):
                for rr in section:
                    rr.ttl = remaining_ttl
            
            return cached_response

        return None

    def clear_cache(self):
        """Clear the entire cache."""
        self.cache_data.clear()
        print("[CacheManager] Cache cleared.")