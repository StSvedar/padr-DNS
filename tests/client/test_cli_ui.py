import pytest
from src.client.cli_ui import CLI_UI

def test_cli_ui_arguments_parsing_default():
    ui = CLI_UI()
    args = ui.parse_arguments(["google.com"])
    
    assert args.domain == "google.com"
    assert args.server == "127.0.0.1"
    assert args.port == 53
    assert args.type == "A"
    assert args.no_recurse is False

def test_cli_ui_arguments_parsing_custom():
    ui = CLI_UI()
    args = ui.parse_arguments(["flush.cache.local", "-s", "8.8.8.8", "-p", "10053", "-t", "TXT", "--no-recurse"])
    
    assert args.domain == "flush.cache.local"
    assert args.server == "8.8.8.8"
    assert args.port == 10053
    assert args.type == "TXT"
    assert args.no_recurse is True