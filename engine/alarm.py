"""
告警音频管理器
使用 pygame.mixer 播放 MP3 告警音，从 PC 扬声器输出。
支持循环播放、幂等触发、文件中性处理。
"""
import os
import pygame

from engine.config import ALARM1_PATH, ALARM2_PATH, ALARM_VOLUME


class AlarmManager:
    """
    告警音频管理器

    管理两个独立告警通道：
    - alarm1: 安全装备违规（未戴安全帽 / 未穿反光衣）
    - alarm2: 摔倒检测

    特性：
    - 循环播放直到显式停止
    - play() 幂等（已在播放则跳过，避免声音叠加）
    - 音频文件缺失时可正常运行（跳过播放 + 打印警告）
    """

    def __init__(self):
        self._initialized = False
        self._sounds: dict[str, pygame.mixer.Sound | None] = {}
        self._playing: dict[str, bool] = {}

    def init(self):
        """初始化 pygame 音频系统。仅调用一次。"""
        if self._initialized:
            return

        try:
            pygame.mixer.init()
            print("[ALARM] pygame.mixer init OK")
        except Exception as e:
            print(f"[ALARM] pygame.mixer init failed: {e}")

        self._initialized = True

    def load(self, name: str, filepath: str):
        """
        加载音频文件。

        Args:
            name: 告警标识（"alarm1" 或 "alarm2"）
            filepath: MP3 文件路径
        """
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
        """
        播放告警音（幂等：已在播放则跳过）。

        Args:
            name: 告警标识
            loop: 是否循环播放（默认 True）
        """
        if not self._initialized:
            self.init()

        sound = self._sounds.get(name)
        if sound is None:
            return  # 文件不存在，静默跳过

        if self._playing.get(name, False):
            return  # 已在播放，幂等跳过

        loops = -1 if loop else 0
        try:
            sound.play(loops=loops)
            self._playing[name] = True
        except Exception as e:
            print(f"[ALARM] play failed '{name}': {e}")

    def stop(self, name: str):
        """
        停止指定告警音。

        Args:
            name: 告警标识
        """
        sound = self._sounds.get(name)
        if sound is None:
            return
        try:
            sound.stop()
        except Exception:
            pass
        self._playing[name] = False

    def stop_all(self):
        """停止所有告警音。"""
        for name in list(self._playing.keys()):
            self.stop(name)

    @property
    def is_playing_status(self) -> dict[str, bool]:
        """返回各告警的播放状态"""
        return self._playing.copy()

    def quit(self):
        """释放 pygame 资源。"""
        self.stop_all()
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        self._initialized = False


def create_alarm_manager() -> AlarmManager:
    """
    工厂函数：创建 AlarmManager 并加载默认告警文件。
    文件缺失时不报错，告警功能降级运行。
    """
    mgr = AlarmManager()
    mgr.init()
    mgr.load("alarm1", ALARM1_PATH)
    mgr.load("alarm2", ALARM2_PATH)
    return mgr
