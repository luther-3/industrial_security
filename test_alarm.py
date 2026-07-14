"""
Test script: Alarm Manager
Usage: python test_alarm.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.alarm import AlarmManager
from engine.config import ALARM1_PATH, ALARM2_PATH


def check_files():
    a1 = os.path.exists(ALARM1_PATH)
    a2 = os.path.exists(ALARM2_PATH)
    print(f"[TEST] alarm1.mp3: {'[OK] ready' if a1 else '[MISS] skipped'}")
    print(f"[TEST] alarm2.mp3: {'[OK] ready' if a2 else '[MISS] skipped'}")
    return a1, a2


def test_play1():
    print("\n--- Test 1: play alarm1 2s ---")
    mgr = AlarmManager()
    mgr.init()
    mgr.load("alarm1", ALARM1_PATH)
    mgr.load("alarm2", ALARM2_PATH)
    if mgr._sounds.get("alarm1"):
        mgr.play("alarm1", loop=True)
        print("[TEST] alarm1 playing... (2s)")
        time.sleep(2)
        mgr.stop("alarm1")
        print("[TEST] alarm1 stopped")
    else:
        print("[TEST] skipped (alarm1.mp3 not found)")
    mgr.quit()


def test_play2():
    print("\n--- Test 2: play alarm2 2s ---")
    mgr = AlarmManager()
    mgr.init()
    mgr.load("alarm1", ALARM1_PATH)
    mgr.load("alarm2", ALARM2_PATH)
    if mgr._sounds.get("alarm2"):
        mgr.play("alarm2", loop=True)
        print("[TEST] alarm2 playing... (2s)")
        time.sleep(2)
        mgr.stop("alarm2")
        print("[TEST] alarm2 stopped")
    else:
        print("[TEST] skipped (alarm2.mp3 not found)")
    mgr.quit()


def test_both():
    print("\n--- Test 3: both alarms 3s ---")
    mgr = AlarmManager()
    mgr.init()
    mgr.load("alarm1", ALARM1_PATH)
    mgr.load("alarm2", ALARM2_PATH)
    a1 = mgr._sounds.get("alarm1")
    a2 = mgr._sounds.get("alarm2")
    if a1 and a2:
        mgr.play("alarm1", loop=True)
        mgr.play("alarm2", loop=True)
        print("[TEST] alarm1 + alarm2 playing... (3s)")
        time.sleep(3)
        mgr.stop_all()
        print("[TEST] all stopped")
    else:
        print("[TEST] skipped (missing files)")
    mgr.quit()


def test_idempotent():
    print("\n--- Test 4: idempotent play ---")
    mgr = AlarmManager()
    mgr.init()
    mgr.load("alarm1", ALARM1_PATH)
    if mgr._sounds.get("alarm1"):
        mgr.play("alarm1", loop=True)
        mgr.play("alarm1", loop=True)   # should be ignored
        mgr.play("alarm1", loop=True)   # should be ignored
        print("[TEST] 3x play('alarm1'), should hear only one (check ears)")
        time.sleep(1.5)
        mgr.stop("alarm1")
    else:
        print("[TEST] skipped (alarm1.mp3 not found)")
    mgr.quit()


def test_missing():
    print("\n--- Test 5: missing file tolerance ---")
    mgr = AlarmManager()
    mgr.init()
    mgr.load("alarm1", "nonexistent_file.mp3")
    mgr.play("alarm1")    # should not crash
    mgr.stop("alarm1")    # should not crash
    mgr.play("alarm2")    # not loaded, should not crash
    print("[TEST] no crash with missing files [OK]")
    mgr.quit()


def main():
    print("=" * 50)
    print("  Alarm Manager Test")
    print("=" * 50)
    check_files()
    test_play1()
    test_play2()
    test_both()
    test_idempotent()
    test_missing()
    print("\n" + "=" * 50)
    print("  Test Complete")
    print("=" * 50)


if __name__ == "__main__":
    main()
