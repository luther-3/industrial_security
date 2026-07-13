"""
图像标注绘制
在视频帧上绘制检测框、标签、统计信息叠加。
"""
import cv2
import numpy as np

from engine.detector import Detection


# 绘制常量
BOX_THICKNESS = 2
FONT_SCALE = 0.6
FONT_THICKNESS = 2
LABEL_PADDING = 4
STATS_FONT_SCALE = 0.7
STATS_FONT_THICKNESS = 2
STATS_OFFSET_X = 12
STATS_OFFSET_Y = 36
STATS_LINE_HEIGHT = 28


def annotate_frame(
    frame: np.ndarray,
    detections: list[Detection],
    stats: dict | None = None,
) -> np.ndarray:
    """
    在帧上绘制检测框、标签、统计信息。

    Args:
        frame: BGR 格式原始帧 (H, W, 3)
        detections: 检测结果列表
        stats: 统计数据字典（可选），叠加到画面左上角

    Returns:
        带标注的帧（新拷贝，不修改原帧）
    """
    annotated = frame.copy()

    # 1. 绘制每个检测框 + 类别标签
    for det in detections:
        x1, y1, x2, y2 = det.bbox
        color = det.color
        label = det.label

        # 边框
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, BOX_THICKNESS)

        # 标签背景 + 文字
        _draw_label(annotated, label, (x1, y1), color)

    # 2. 绘制左上角统计信息叠加
    if stats is not None:
        _draw_stats_overlay(annotated, stats)

    return annotated


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
