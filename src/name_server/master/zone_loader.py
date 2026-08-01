import json
import os
import threading
import time
from typing import Callable, Optional

class ZoneLoader:
    """Handles reading the raw JSON file and watching for file changes to notify updates."""

    def __init__(self, filepath: str, on_config_change: Callable[[dict], None], check_interval: float = 1.0):
        self.filepath = filepath
        self.on_config_change = on_config_change
        self.check_interval = check_interval
        self._last_mtime: Optional[float] = None

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
        """Enable background file modification checking for hot reload (Cross-platform)."""
        try:
            self._last_mtime = os.path.getmtime(self.filepath)
        except OSError:
            self._last_mtime = None

        thread = threading.Thread(target=self._watch_loop, daemon=True)
        thread.start()
        print(f"[*] ZoneLoader is watching {self.filepath} for changes (Windows/Linux compatible).")

    def _watch_loop(self):
        """Background loop checking file mtime."""
        while True:
            time.sleep(self.check_interval)
            try:
                current_mtime = os.path.getmtime(self.filepath)
            except OSError:
                continue

            if self._last_mtime is not None and current_mtime > self._last_mtime:
                print(f"\n[*] File change detected in {self.filepath}! Sending update notification...")
                self._last_mtime = current_mtime
                self.load_and_notify()
            elif self._last_mtime is None:
                self._last_mtime = current_mtime
