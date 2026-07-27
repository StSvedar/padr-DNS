import json
import os
import signal
import tempfile
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


def test_zone_loader_registers_sighup_handler():
    loader = ZoneLoader("unused.json", MagicMock())

    with patch.object(signal, "SIGHUP", 1, create=True), patch(
        "src.name_server.master.zone_loader.signal.signal"
    ) as mock_signal:
        loader.listen_for_sighup()

    mock_signal.assert_called_once_with(1, loader._handle_signal)