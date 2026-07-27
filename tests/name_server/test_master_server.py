import json
import os
import tempfile
from unittest.mock import patch

from src.name_server.master.master_server import MasterServer
from src.core.enums import RecordType

@patch("src.name_server.master.zone_loader.ZoneLoader.listen_for_sighup")
def test_master_server_loads_initial_zone_and_reloads(mock_listen_for_sighup):
    initial_data = {"test.com": {"A": [{"ip": "1.1.1.1"}]}}
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        json.dump(initial_data, tmp)
        tmp_path = tmp.name

    try:
        master = MasterServer("127.0.0.1", 10053, tmp_path)
        
        initial_record = master.zone_data.get_records("test.com", RecordType.A)[0]
        assert initial_record.rdata_str == "1.1.1.1"
        assert initial_record.ttl == 300
        
        new_data = {"test.com": {"A": [{"ip": "2.2.2.2"}]}}
        master.on_zone_reload(new_data)

        updated_record = master.zone_data.get_records("test.com", RecordType.A)[0]
        assert updated_record.rdata_str == "2.2.2.2"
        mock_listen_for_sighup.assert_called_once()
        
    finally:
        os.remove(tmp_path)