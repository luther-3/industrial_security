"""
Shared state between inference thread and web thread.
Thread-safe: all writes protected by a single lock.
"""
import threading
from datetime import datetime
from typing import Optional


class SharedState:
    def __init__(self):
        self._lock = threading.Lock()

        # Latest annotated JPEG frame
        self._jpeg: Optional[bytes] = None

        # Latest stats
        self._stats: dict = {
            "total_persons": 0,
            "no_helmet": 0,
            "no_vest": 0,
            "fall": False,
            "camera_status": "connecting",
            "fps": 0.0,
            "timestamp": None,
        }

    # ---- frame ----

    def update_frame(self, jpeg: bytes):
        with self._lock:
            self._jpeg = jpeg

    def get_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self._jpeg

    # ---- stats ----

    def update_stats(self, stats: dict):
        with self._lock:
            self._stats = {**stats, "timestamp": datetime.now().isoformat()}

    def get_stats(self) -> dict:
        with self._lock:
            return self._stats.copy()
