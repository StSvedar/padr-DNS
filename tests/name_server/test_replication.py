import json
from unittest.mock import MagicMock

from src.core.dns_message import DNSMessage
from src.core.dns_question import DNSQuestion
from src.core.resource_record import ResourceRecord
from src.core.zone_data import ZoneData
from src.name_server.master.master_replication import MasterReplicationManager
from src.name_server.slave.slave_replication import SlaveReplicationManager
from src.core.enums import RecordType, RecordClass

MOCK_ZONE = {"test.com": {"A": [{"ip": "1.2.3.4", "ttl": 300}]}}

def test_master_handle_axfr_serialization():
    zone_data = ZoneData(zone_dict=MOCK_ZONE)
    master_repl = MasterReplicationManager(zone_data, slave_ips=[])
    
    query = DNSMessage(id=42)
    query.questions.append(DNSQuestion('.', RecordType.AXFR, RecordClass.IN))
    
    response = master_repl.handle_axfr(query)
    
    assert response.qr == 1
    assert response.aa == 1
    assert len(response.answers) == 1
    assert response.answers[0].type == RecordType.AXFR
    
    payload_str = response.answers[0].rdata.decode('utf-8')
    recovered_zone = json.loads(payload_str)
    assert recovered_zone == zone_data.to_dict()

def test_slave_request_axfr_deserialization():
    mock_callback = MagicMock()
    slave_repl = SlaveReplicationManager("10.0.0.1", 53, mock_callback)
    
    fake_master_response = DNSMessage()
    payload = json.dumps(MOCK_ZONE).encode('utf-8')
    fake_master_response.answers.append(ResourceRecord('.', RecordType.AXFR, RecordClass.IN, 0, payload))
    
    slave_repl.requester = MagicMock()
    slave_repl.requester.send_tcp_query.return_value = fake_master_response.pack()
    
    slave_repl.request_axfr()
    
    mock_callback.assert_called_once_with(MOCK_ZONE)
    assert slave_repl.current_serial == 1

def test_slave_handle_notify():
    mock_callback = MagicMock()
    slave_repl = SlaveReplicationManager("10.0.0.1", 53, mock_callback)
    slave_repl.request_axfr = MagicMock()
    
    query = DNSMessage(id=777, opcode=4)
    
    response = slave_repl.handle_notify(query)
    
    assert response.id == 777
    assert response.qr == 1
    assert response.opcode == 4
    slave_repl.request_axfr.assert_called_once()