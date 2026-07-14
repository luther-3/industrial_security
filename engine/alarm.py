"""
Alarm audio manager using pygame.mixer.
Plays alarm MP3 from PC speakers with loop, idempotent trigger,
and minimum-duration guard to prevent premature stop.
"""
import time
import os
import pygame

from engine.config import ALARM1_PATH, ALARM2_PATH, ALARM_VOLUME

# Minimum play duration before stop() is allowed (seconds)
MIN_PLAY_DURATION = 1.5


class AlarmManager:
    def __init__(self):
        self._initialized = False
        self._sounds: dict[str, pygame.mixer.Sound | None] = {}
        self._playing: dict[str, bool] = {}
        self._start_time: dict[str, float] = {}

    def init(self):
        if self._initialized:
            return
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            print("[ALARM] pygame.mixer init OK")
        except Exception as e:
            print(f"[ALARM] pygame.mixer init failed: {e}")
        self._initialized = True

    def load(self, name: str, filepath: str):
        if not self._initialized:
            self.init()
        if not os.path.exists(filepath):
            print(f"[ALARM] Warning: audio file not found -> {filepath}")
            print(f"         alarm '{name}' disabled, other functions unaffected")
            self._sounds[name] = None
            return
        try:
            self._sounds[name] = pygame.mixer.Sound(filepath)
            self._sounds[name].set_volume(ALARM_VOLUME)
            print(f"[ALARM] loaded: {filepath} -> '{name}'")
        except Exception as e:
            print(f"[ALARM] load failed {filepath}: {e}")
            self._sounds[name] = None

    def play(self, name: str, loop: bool = True):
        """Play alarm. Idempotent for sound start, but always refreshes timer."""
        if not self._initialized:
            self.init()

        sound = self._sounds.get(name)
        if sound is None:
            return

        # Always refresh the timer — keeps alarm alive as long as violation persists
        self._start_time[name] = time.time()

        if self._playing.get(name, False):
            return  # already playing, but timer was refreshed above

        loops = -1 if loop else 0
        try:
            sound.play(loops=loops)
            self._playing[name] = True
        except Exception as e:
            print(f"[ALARM] play failed '{name}': {e}")

    def stop(self, name: str):
        """
        Stop alarm. Refuses to stop within MIN_PLAY_DURATION seconds
        of play() to guarantee a minimum audible alarm length.
        """
        sound = self._sounds.get(name)
        if sound is None:
            return

        if not self._playing.get(name, False):
            return

        elapsed = time.time() - self._start_time.get(name, 0)
        if elapsed < MIN_PLAY_DURATION:
            return  # too soon, keep playing

        try:
            sound.stop()
        except Exception:
            pass
        self._playing[name] = False

    def stop_all(self):
        for name in list(self._playing.keys()):
            # Force-stop ignores minimum duration
            sound = self._sounds.get(name)
            if sound:
                try:
                    sound.stop()
                except Exception:
                    pass
            self._playing[name] = False

    @property
    def is_playing_status(self) -> dict[str, bool]:
        return self._playing.copy()

    def quit(self):
        self.stop_all()
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        self._initialized = False


def create_alarm_manager() -> AlarmManager:
    mgr = AlarmManager()
    mgr.init()
    mgr.load("alarm1", ALARM1_PATH)
    mgr.load("alarm2", ALARM2_PATH)
    return mgr
