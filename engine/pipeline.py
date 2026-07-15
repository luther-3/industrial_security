"""
Main inference pipeline.
Orchestrates: capture -> detect -> pose -> fall-state -> alarm -> draw -> state.
Runs on a background daemon thread.
"""
import time
from datetime import datetime

import cv2

from engine.config import (
    MJPEG_URL,
    JPEG_QUALITY,
    VIOLATION_TRIGGER_FRAMES,
    VIOLATION_CLEAR_FRAMES,
)
from engine.detector import SafetyGearDetector
from engine.pose_estimator import PoseEstimator, FallStateManager
from engine.alarm import create_alarm_manager, AlarmManager
from engine.draw import annotate_frame
from server.state import SharedState


class ViolationStateManager:
    """
    Violation alarm state machine with hysteresis.
    Trigger: >= N consecutive frames with violation.
    Clear: >= M consecutive frames without violation.
    """

    def __init__(self):
        self.is_active = False
        self._counter = 0
        self._clear_counter = 0

    def update(self, has_violation: bool) -> bool:
        if has_violation:
            self._counter += 1
            self._clear_counter = 0
        else:
            self._clear_counter += 1
            self._counter = 0

        if not self.is_active and self._counter >= VIOLATION_TRIGGER_FRAMES:
            self.is_active = True
        elif self.is_active and self._clear_counter >= VIOLATION_CLEAR_FRAMES:
            self.is_active = False

        return self.is_active


class Pipeline:
    """
    Inference pipeline running on a background thread.

    source: "camera" | video file path | camera index (0)
    """

    def __init__(self, state: SharedState, source: str | int = "camera"):
        self.state = state
        self.source = source
        self._running = False

        # Modules (initialized in setup)
        self.detector: SafetyGearDetector | None = None
        self.pose_estimator: PoseEstimator | None = None
        self.fall_manager = FallStateManager()
        self.violation_manager = ViolationStateManager()
        self.alarm: AlarmManager | None = None

    def setup(self):
        """Initialize all modules. Call once before run()."""
        print("[PIPELINE] Initializing...")

        self.detector = SafetyGearDetector()
        self.pose_estimator = PoseEstimator()
        self.alarm = create_alarm_manager()

        print(f"[PIPELINE] Detector model: {self.detector.model_path}")
        print(f"[PIPELINE] Pose model: {self.pose_estimator.model_path}")
        print("[PIPELINE] Ready.")

    def run(self):
        """Main loop. Blocks until stop() is called."""
        if self.detector is None:
            self.setup()

        cap = self._open_source()
        if cap is None:
            print("[PIPELINE] ERROR: cannot open video source")
            self.state.update_stats({"camera_status": "disconnected"})
            return

        self._running = True
        self.state.update_stats({"camera_status": "connected"})
        print("[PIPELINE] Running...")

        frame_count = 0
        fps_timer = time.time()

        while self._running:
            ret, frame = cap.read()
            if not ret:
                print("[PIPELINE] End of video or read error.")
                break

            frame = cv2.resize(frame, (640, 480))
            frame_count += 1

            # ---- detection ----
            detections = self.detector.detect(frame)

            # ---- pose + fall ----
            poses = self.pose_estimator.estimate(frame)
            any_fall_single = any(p.is_fallen for p in poses)
            fall_confirmed = self.fall_manager.update(any_fall_single)

            # ---- stats (pose persons + equipment matching) ----
            if self.detector._is_fallback:
                stats = self.detector.compute_stats(detections)
            else:
                stats = self._compute_gear_stats(poses, detections)

            # ---- alarm evaluation ----
            has_violation = (stats["no_helmet"] > 0 or stats["no_vest"] > 0)
            violation_active = self.violation_manager.update(has_violation)

            if violation_active:
                self.alarm.play("alarm1", loop=True)
            else:
                self.alarm.stop("alarm1")

            if fall_confirmed:
                self.alarm.play("alarm2", loop=True)
            else:
                self.alarm.stop("alarm2")

            # ---- finalize stats ----
            fps = frame_count / max(time.time() - fps_timer, 0.001)
            stats["fall"] = fall_confirmed
            stats["camera_status"] = "connected"
            stats["fps"] = round(fps, 1)
            stats["timestamp"] = datetime.now().isoformat()

            # ---- draw ----
            annotated = annotate_frame(frame, detections, poses, stats)

            # ---- encode JPEG ----
            _, jpeg = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])

            # ---- publish ----
            self.state.update_frame(jpeg.tobytes())
            self.state.update_stats(stats)

        # Cleanup
        cap.release()
        self.alarm.stop_all()
        self.alarm.quit()
        print("[PIPELINE] Stopped.")

    def _compute_gear_stats(self, poses, detections):
        """
        Compute stats: total from pose model, gear violations from
        matching equipment detections (11 PPE classes) to pose person boxes via IoU.
        """
        from engine.config import NO_HELMET_CLASSES, NO_VEST_CLASSES

        total = len(poses)
        no_helmet = 0
        no_vest = 0

        for pose in poses:
            px1, py1, px2, py2 = pose.bbox
            matched_classes = set()

            for det in detections:
                dx1, dy1, dx2, dy2 = det.bbox
                iw = max(0, min(px2, dx2) - max(px1, dx1))
                ih = max(0, min(py2, dy2) - max(py1, dy1))
                inter = iw * ih
                pa = (px2 - px1) * (py2 - py1)
                da = (dx2 - dx1) * (dy2 - dy1)
                iou = inter / max(pa + da - inter, 1)
                if iou > 0.2:
                    matched_classes.add(det.class_name)

            if matched_classes & NO_HELMET_CLASSES:
                no_helmet += 1
            if matched_classes & NO_VEST_CLASSES:
                no_vest += 1

        return {"total_persons": total, "no_helmet": no_helmet, "no_vest": no_vest}

    def stop(self):
        """Signal the main loop to stop."""
        self._running = False

    def _open_source(self):
        """Open video source. Returns cv2.VideoCapture or None."""
        if self.source == "camera":
            src = MJPEG_URL
        else:
            src = self.source

        print(f"[PIPELINE] Opening source: {src}")
        cap = cv2.VideoCapture(src)

        if not cap.isOpened():
            print(f"[PIPELINE] Failed to open: {src}")
            # Retry once after 2s for camera
            if self.source == "camera":
                print("[PIPELINE] Retrying in 2s...")
                time.sleep(2)
                cap = cv2.VideoCapture(src)
        return cap
