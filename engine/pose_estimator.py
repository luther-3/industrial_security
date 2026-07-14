"""
人体姿态估计 + 摔倒判断
使用 YOLOv8n-pose 官方预训练模型检测 17 个关键点，
基于几何特征 + 时序确认判断摔倒。
"""
from dataclasses import dataclass, field

import numpy as np
from ultralytics import YOLO

from engine.config import (
    POSE_MODEL_PATH,
    POSE_CONFIDENCE,
    FALL_TORSO_RATIO,
    FALL_BBOX_RATIO,
    POSE_REQUIRED_KEYPOINT_CONF,
    FALL_TRIGGER_FRAMES,
    FALL_CLEAR_FRAMES,
)

# COCO 17 关键点索引
KP = {
    "nose": 0, "left_eye": 1, "right_eye": 2,
    "left_ear": 3, "right_ear": 4,
    "left_shoulder": 5, "right_shoulder": 6,
    "left_elbow": 7, "right_elbow": 8,
    "left_wrist": 9, "right_wrist": 10,
    "left_hip": 11, "right_hip": 12,
    "left_knee": 13, "right_knee": 14,
    "left_ankle": 15, "right_ankle": 16,
}

# 骨架连线对（用于绘制）
SKELETON_PAIRS = [
    (5, 6),   # 肩-肩
    (5, 7), (7, 9),    # 左臂
    (6, 8), (8, 10),   # 右臂
    (5, 11), (6, 12),  # 肩-髋
    (11, 12),  # 髋-髋
    (11, 13), (13, 15),  # 左腿
    (12, 14), (14, 16),  # 右腿
]

# 摔倒判断需要的 6 个关键点索引
CRITICAL_KP = [
    KP["left_shoulder"], KP["right_shoulder"],
    KP["left_hip"], KP["right_hip"],
    KP["left_ankle"], KP["right_ankle"],
]


@dataclass
class PoseResult:
    """单个姿态估计结果"""
    bbox: tuple[int, int, int, int]              # (x1, y1, x2, y2)
    keypoints: list[tuple[float, float, float]]  # 17 个 (x, y, conf)
    is_fallen: bool = False                        # 单帧判断结果（未考虑时序）


class FallStateManager:
    """
    摔倒状态机（帧级迟滞）

    触发: 连续 FALL_TRIGGER_FRAMES 帧判定为摔倒 → 触发
    解除: 连续 FALL_CLEAR_FRAMES 帧判定为正常 → 解除
    """

    def __init__(self):
        self.is_active = False
        self._fall_counter = 0
        self._clear_counter = 0

    def update(self, single_frame_fall: bool) -> bool:
        """
        输入单帧判断结果，返回状态机确认后的最终结果。
        """
        if single_frame_fall:
            self._fall_counter += 1
            self._clear_counter = 0
        else:
            self._clear_counter += 1
            self._fall_counter = 0

        if not self.is_active and self._fall_counter >= FALL_TRIGGER_FRAMES:
            self.is_active = True
        elif self.is_active and self._clear_counter >= FALL_CLEAR_FRAMES:
            self.is_active = False

        return self.is_active

    def reset(self):
        """重置状态"""
        self.is_active = False
        self._fall_counter = 0
        self._clear_counter = 0


def is_fallen(
    keypoints: list[tuple[float, float, float]],
    bbox: tuple[int, int, int, int],
) -> bool:
    """
    单帧摔倒判断（多条件 AND）。

    Args:
        keypoints: 17 个关键点 [(x, y, conf), ...]
        bbox: 人体边界框 (x1, y1, x2, y2)

    Returns:
        True 如果满足所有摔倒条件
    """
    # 条件 1: 关键点置信度过滤（6 个关键点）
    for idx in CRITICAL_KP:
        kp = keypoints[idx]
        if len(kp) < 3 or kp[2] < POSE_REQUIRED_KEYPOINT_CONF:
            return False

    # 提取坐标
    l_sh = keypoints[KP["left_shoulder"]]
    r_sh = keypoints[KP["right_shoulder"]]
    l_hi = keypoints[KP["left_hip"]]
    r_hi = keypoints[KP["right_hip"]]
    l_an = keypoints[KP["left_ankle"]]
    r_an = keypoints[KP["right_ankle"]]

    shoulder_y = (l_sh[1] + r_sh[1]) / 2
    hip_y = (l_hi[1] + r_hi[1]) / 2
    ankle_y = (l_an[1] + r_an[1]) / 2

    torso_h = abs(hip_y - shoulder_y)     # 躯干高度
    body_h = abs(shoulder_y - ankle_y)     # 身体总高度

    # 条件 2: 躯干高度比
    if body_h <= 0 or (torso_h / body_h) >= FALL_TORSO_RATIO:
        return False

    # 条件 3: bbox 宽高比（摔倒时宽 > 高）
    x1, y1, x2, y2 = bbox
    bw = abs(x2 - x1)
    bh = abs(y2 - y1)
    if bh <= 0 or (bw / bh) <= FALL_BBOX_RATIO:
        return False

    return True


class PoseEstimator:
    """
    人体姿态估计器

    封装 YOLOv8-pose 模型，提供姿态估计 + 批量摔倒判断。
    """

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or POSE_MODEL_PATH
        self._model: YOLO | None = None

    @property
    def model(self) -> YOLO:
        if self._model is None:
            self._model = YOLO(self.model_path)
        return self._model

    def estimate(self, frame: np.ndarray) -> list[PoseResult]:
        """
        对单帧图像进行姿态估计。

        Args:
            frame: BGR 格式 (H, W, 3)

        Returns:
            每个人的姿态结果列表
        """
        results = self.model(frame, verbose=False)

        poses: list[PoseResult] = []
        for result in results:
            if result.keypoints is None:
                continue

            kpts_tensor = result.keypoints.data.cpu().numpy()  # (N, 17, 3)
            if result.boxes is not None:
                boxes = result.boxes.xyxy.cpu().numpy()
            else:
                continue

            for kpts, box in zip(kpts_tensor, boxes):
                x1, y1, x2, y2 = map(int, box)
                keypoints = [(float(k[0]), float(k[1]), float(k[2])) for k in kpts]
                fallen = is_fallen(keypoints, (x1, y1, x2, y2))
                poses.append(PoseResult(
                    bbox=(x1, y1, x2, y2),
                    keypoints=keypoints,
                    is_fallen=fallen,
                ))

        return poses
