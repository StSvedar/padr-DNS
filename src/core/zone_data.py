from src.core.resource_record import ResourceRecord
from src.core.enums import RecordType

class ZoneData:
    def __init__(self, name: str = ".", zone_dict: dict[str, dict[str, list[dict]]] = {}):
        self.name = name.lower()
        # Structure interne typée : { "test.be": { RecordType.A: [ResourceRecord, ...] } }
        self._records: dict[str, dict[RecordType, list[ResourceRecord]]] = {}

        if zone_dict:
            self.add_from_dict(zone_dict)

    def add_record(self, record: ResourceRecord):
        """Add a ResourceRecord to the zone data."""
        name = str(record.domain).lower()
        rtype = record.type

        if name not in self._records:
            self._records[name] = {}
        if rtype not in self._records[name]:
            self._records[name][rtype] = []

        self._records[name][rtype].append(record)

    def contains_domain(self, name: str) -> bool:
        """Check if the zone data contains records for the given domain name."""
        return name.lower() in self._records

    def get_names(self) -> list[str]:
        """Return all unique domain names in the zone data."""
        return list(self._records.keys())

    def get_types_for_name(self, name: str) -> list[RecordType]:
        """Return all record types for a given domain name."""
        name = name.lower()
        if name in self._records:
            return list(self._records[name].keys())
        return []

    def get_records(self, name: str, rtype: RecordType) -> list[ResourceRecord]:
        """Retrieve records for a given name and type."""
        name = name.lower()
        return self._records.get(name, {}).get(rtype, [])

    def add_from_dict(self, zone_dict: dict[str, dict[str, list[dict]]]):
        """Add records from a dictionary."""
        for name, types in zone_dict.items():
            for rtype_str, records in types.items():
                for record in records:
                    rr = ResourceRecord.from_dict(name, rtype_str, record)
                    self.add_record(rr)

    def load_from_dict(self, zone_dict: dict[str, dict[str, list[dict]]]):
        """Load/Reload zone data from a dictionary."""
        self._records.clear()
        self.add_from_dict(zone_dict)

    def to_dict(self) -> dict[str, dict[str, list[dict]]]:
        """Convert the ZoneData instance back to a dictionary."""
        zone_dict = {}
        for name, types in self._records.items():
            zone_dict[name] = {}
            for rtype, records in types.items():
                zone_dict[name][rtype.name] = [record.to_dict() for record in records]
        return zone_dict