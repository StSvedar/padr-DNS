import json
import signal
from typing import Callable, Optional

class ZoneLoader:
    """Handles reading the raw JSON file and listening for SIGHUP to notify changes."""

    def __init__(self, filepath: str, on_config_change: Callable[[dict], None]):
        self.filepath = filepath
        self.on_config_change = on_config_change

    def read_config(self) -> Optional[dict]:
        """Read and return the raw JSON dictionary without transformation."""
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
            print(f"[ZoneLoader] Configuration loaded from {self.filepath}")
            return data
        except Exception as e:
            print(f"[!] Error reading {self.filepath}: {e}")
            return None

    def load_and_notify(self) -> bool:
        """Read the configuration and notify the callback only when the data is valid."""
        data = self.read_config()
        if data is not None:
            self.on_config_change(data)
            return True
        return False

    def listen_for_sighup(self):
        """Enable SIGHUP handling for hot reload."""
        try:
            signal.signal(signal.SIGHUP, self._handle_signal)
            print("[*] ZoneLoader is listening for SIGHUP.")
        except AttributeError:
            print("[!] SIGHUP is not supported on this system (Windows).")

    def _handle_signal(self, signum, frame):
        print("\n[*] SIGHUP signal received! Sending update notification...")
        self.load_and_notify()
