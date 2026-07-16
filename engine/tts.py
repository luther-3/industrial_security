"""
Text-to-Speech voice announcements using pyttsx3 (offline, Windows built-in).
Each speech cycle creates a fresh engine to avoid broken event loop state.
"""
import threading
import time
import pyttsx3


class TTSManager:
    def __init__(self):
        self._thread: threading.Thread | None = None
        self._running = False
        self._current_text: str = ""

    def start(self, text: str):
        if self._running and self._current_text == text:
            return
        self.stop()
        self._current_text = text
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        time.sleep(0.5)
        while self._running:
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", 180)
                engine.setProperty("volume", 1.0)
                engine.say(self._current_text)
                engine.runAndWait()
                engine.stop()
            except Exception:
                pass
            if self._running:
                time.sleep(2.5)

    def stop(self):
        self._running = False

    def quit(self):
        self.stop()
