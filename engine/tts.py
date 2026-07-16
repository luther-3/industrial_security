"""
Text-to-Speech voice announcements using pyttsx3 (offline, Windows built-in).
"""
import threading
import time
import pyttsx3


class TTSManager:
    """
    Voice announcement manager.

    Usage:
        tts = TTSManager()
        tts.start("请注意，检测到有人员未佩戴安全帽")
        ...
        tts.stop()
    """

    def __init__(self):
        self._engine: pyttsx3.Engine | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._current_text: str = ""

    @property
    def engine(self):
        if self._engine is None:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 180)   # 语速
            self._engine.setProperty("volume", 1.0)
        return self._engine

    def start(self, text: str):
        """Start looping voice announcement (non-blocking)."""
        if self._running and self._current_text == text:
            return  # already speaking same message

        self.stop()  # stop any previous speech
        self._current_text = text
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        """Loop: speak → wait → speak → ... until stopped."""
        # Short delay before voice
        time.sleep(0.5)

        while self._running:
            try:
                self.engine.say(self._current_text)
                self.engine.runAndWait()
            except Exception:
                pass
            # Gap between repetitions
            if self._running:
                time.sleep(2.5)

    def stop(self):
        """Stop current voice announcement."""
        self._running = False
        if self._engine:
            try:
                self.engine.stop()
            except Exception:
                pass

    def quit(self):
        """Release resources."""
        self.stop()
        try:
            if self._engine:
                self.engine.stop()
        except Exception:
            pass
