"""
图像标注绘制
在视频帧上绘制检测框、标签、姿态关键点、摔倒标记、统计信息。
"""
import cv2
import numpy as np

from engine.detector import Detection
from engine.pose_estimator import PoseResult, SKELETON_PAIRS


# 绘制常量
BOX_THICKNESS = 2
FONT_SCALE = 0.5
FONT_THICKNESS = 1
LABEL_PADDING = 4
STATS_FONT_SCALE = 0.7
STATS_FONT_THICKNESS = 2
STATS_OFFSET_X = 12
STATS_OFFSET_Y = 36
STATS_LINE_HEIGHT = 28

# 姿态绘制
KP_RADIUS = 3
KP_COLOR = (255, 200, 0)          # 关键点颜色（天蓝）
SKELETON_COLOR = (200, 200, 0)    # 骨架颜色（青绿）
FALL_COLOR = (108, 108, 245)      # 红色（摔倒标记）


def annotate_frame(
    frame: np.ndarray,
    detections: list[Detection],
    poses: list[PoseResult] | None = None,
    stats: dict | None = None,
) -> np.ndarray:
    """
    在帧上绘制检测框、姿态关键点、摔倒标记、统计信息。

    Args:
        frame: BGR 格式原始帧 (H, W, 3)
        detections: 检测结果列表
        poses: 姿态估计结果列表（可选）
        stats: 统计数据字典（可选）

    Returns:
        带标注的帧（新拷贝，不修改原帧）
    """
    annotated = frame.copy()

    # 1. 绘制每个检测框 + 类别标签
    for det in detections:
        x1, y1, x2, y2 = det.bbox
        cv2.rectangle(annotated, (x1, y1), (x2, y2), det.color, BOX_THICKNESS)
        _draw_label(annotated, det.label, (x1, y1), det.color)

    # 2. 绘制姿态关键点 + 骨架 + 摔倒标记
    if poses:
        for pose in poses:
            _draw_keypoints(annotated, pose.keypoints)
            _draw_skeleton(annotated, pose.keypoints)
            if pose.is_fallen:
                _draw_fall_marker(annotated, pose.bbox)

    # 3. 绘制左上角统计信息叠加
    if stats is not None:
        _draw_stats_overlay(annotated, stats)

    return annotated


def _draw_keypoints(img: np.ndarray, keypoints: list[tuple[float, float, float]]):
    """绘制 17 个人体关键点（圆点）"""
    for kp in keypoints:
        x, y, conf = kp
        if conf > 0.5:
            cv2.circle(img, (int(x), int(y)), KP_RADIUS, KP_COLOR, -1)


def _draw_skeleton(img: np.ndarray, keypoints: list[tuple[float, float, float]]):
    """绘制骨架连线"""
    for idx_a, idx_b in SKELETON_PAIRS:
        kp_a = keypoints[idx_a]
        kp_b = keypoints[idx_b]
        if kp_a[2] > 0.5 and kp_b[2] > 0.5:
            pt_a = (int(kp_a[0]), int(kp_a[1]))
            pt_b = (int(kp_b[0]), int(kp_b[1]))
            cv2.line(img, pt_a, pt_b, SKELETON_COLOR, 1)


def _draw_fall_marker(img: np.ndarray, bbox: tuple[int, int, int, int]):
    """在摔倒人物框上方绘制红色警告标记"""
    x1, y1, x2, y2 = bbox
    cx = (x1 + x2) // 2
    cy = y1 - 10
    text = "FALL"

    (tw, th), baseline = cv2.getTextSize(
        text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2
    )

    # 半透明红色背景
    bx1 = cx - tw // 2 - 6
    by1 = cy - th - baseline - 6
    bx2 = cx + tw // 2 + 6
    by2 = cy

    overlay = img.copy()
    cv2.rectangle(overlay, (bx1, by1), (bx2, by2), (0, 0, 255), -1)
    cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)

    cv2.putText(
        img, text, (cx - tw // 2, cy - baseline),
        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2,
    )


def _draw_label(
    img: np.ndarray,
    text: str,
    position: tuple[int, int],
    color: tuple[int, int, int],
):
    """在检测框上方绘制标签（带半透明背景）"""
    x, y = position
    (tw, th), baseline = cv2.getTextSize(
        text, cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, FONT_THICKNESS
    )

    # 标签背景（比框稍大）
    bg_y1 = max(0, int(y - th - baseline - LABEL_PADDING * 2))
    bg_y2 = y
    bg_x1 = x
    bg_x2 = int(x + tw + LABEL_PADDING * 2)

    # 半透明背景
    overlay = img.copy()
    cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), color, -1)
    cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)

    # 白色文字
    text_y = int(y - baseline - LABEL_PADDING)
    cv2.putText(
        img, text, (x + LABEL_PADDING, text_y),
        cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, (255, 255, 255), FONT_THICKNESS,
    )


def _draw_stats_overlay(img: np.ndarray, stats: dict):
    """在画面左上角绘制半透明统计信息面板"""
    lines = [
        f"Total: {stats.get('total_persons', 0)}",
        f"No-Helmet: {stats.get('no_helmet', 0)}",
        f"No-Vest: {stats.get('no_vest', 0)}",
        f"Fall: {'YES' if stats.get('fall', False) else 'no'}",
    ]

    # 计算面板尺寸
    max_width = 0
    for line in lines:
        (w, _), _ = cv2.getTextSize(
            line, cv2.FONT_HERSHEY_SIMPLEX, STATS_FONT_SCALE, STATS_FONT_THICKNESS
        )
        max_width = max(max_width, w)

    panel_h = len(lines) * STATS_LINE_HEIGHT + 16
    panel_w = int(max_width + 24)

    # 半透明背景面板
    overlay = img.copy()
    cv2.rectangle(overlay, (8, 8), (8 + panel_w, 8 + panel_h), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.4, img, 0.6, 0, img)

    # 文字
    for i, line in enumerate(lines):
        y = STATS_OFFSET_Y + i * STATS_LINE_HEIGHT
        cv2.putText(
            img, line, (STATS_OFFSET_X, y),
            cv2.FONT_HERSHEY_SIMPLEX, STATS_FONT_SCALE, (255, 255, 255), STATS_FONT_THICKNESS,
        )
