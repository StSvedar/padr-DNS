import json
import os
import tempfile
import time
from unittest.mock import MagicMock, patch

from src.name_server.master.zone_loader import ZoneLoader


def test_zone_loader_reads_config():
    test_data = {"test.com": {"A": [{"ip": "10.0.0.1", "ttl": 60}]}}

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        json.dump(test_data, tmp)
        tmp_path = tmp.name

    try:
        loader = ZoneLoader(tmp_path, MagicMock())
        assert loader.read_config() == test_data
    finally:
        os.remove(tmp_path)


def test_zone_loader_returns_none_for_missing_file():
    loader = ZoneLoader("missing_zone_file.json", MagicMock())

    assert loader.read_config() is None


def test_zone_loader_notifies_callback_for_valid_config():
    test_data = {"test.com": {"A": [{"ip": "10.0.0.1", "ttl": 60}]}}

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        json.dump(test_data, tmp)
        tmp_path = tmp.name

    try:
        callback = MagicMock()
        loader = ZoneLoader(tmp_path, callback)

        assert loader.load_and_notify() is True
        callback.assert_called_once_with(test_data)
    finally:
        os.remove(tmp_path)


def test_zone_loader_starts_watching_thread():
    loader = ZoneLoader("unused.json", MagicMock())

    with patch("threading.Thread") as mock_thread:
        loader.listen_for_sighup()

        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()


def test_zone_loader_detects_file_change():
    initial_data = {"test.com": {"A": [{"ip": "10.0.0.1", "ttl": 60}]}}
    updated_data = {"test.com": {"A": [{"ip": "10.0.0.2", "ttl": 60}]}}

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        json.dump(initial_data, tmp)
        tmp_path = tmp.name

    try:
        callback = MagicMock()
        loader = ZoneLoader(tmp_path, callback, check_interval=0.05)
        
        loader.listen_for_sighup()

        time.sleep(0.1)
        with open(tmp_path, "w") as f:
            json.dump(updated_data, f)
        
        future_mtime = time.time() + 2
        os.utime(tmp_path, (future_mtime, future_mtime))

        time.sleep(0.2)

        callback.assert_called_with(updated_data)
    finally:
        os.remove(tmp_path)