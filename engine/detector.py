"""
安全装备检测器
加载 YOLO 模型，对单帧图像进行推理，返回检测结果列表。
"""
import os
from dataclasses import dataclass

import numpy as np
from ultralytics import YOLO

from engine.config import (
    CLASS_NAMES,
    CLASS_COLORS,
    CLASS_LABELS,
    DETECTION_CONFIDENCE,
    DETECTION_MODEL_PATH,
    FALLBACK_MODEL_PATH,
)


@dataclass
class Detection:
    """单个检测结果"""
    bbox: tuple[int, int, int, int]  # (x1, y1, x2, y2)
    class_name: str                   # 类别名，如 "person_helmet_vest"
    confidence: float                 # 置信度

    @property
    def color(self) -> tuple[int, int, int]:
        """OpenCV BGR 框颜色"""
        return CLASS_COLORS.get(self.class_name, (128, 128, 128))

    @property
    def label(self) -> str:
        """显示标签"""
        return CLASS_LABELS.get(self.class_name, self.class_name)


class SafetyGearDetector:
    """
    安全装备检测器

    加载队友训练的 helmet_vest.pt，如果文件不存在则自动回退到
    YOLOv8n COCO 预训练模型（仅检测 person 类）。
    """

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or self._resolve_model_path()
        self._model: YOLO | None = None
        self._is_fallback = self.model_path == FALLBACK_MODEL_PATH

    def _resolve_model_path(self) -> str:
        """解析模型路径：优先队友模型，不存在则回退占位模型"""
        if os.path.exists(DETECTION_MODEL_PATH):
            print(f"[DETECTOR] 加载队友模型: {DETECTION_MODEL_PATH}")
            return DETECTION_MODEL_PATH
        print(f"[DETECTOR] 队友模型未找到，回退占位模型: {FALLBACK_MODEL_PATH}")
        print(f"           占位模型仅检测 COCO 'person' 类，不区分安全装备状态")
        return FALLBACK_MODEL_PATH

    @property
    def model(self) -> YOLO:
        """延迟加载模型（首次调用时才加载）"""
        if self._model is None:
            self._model = YOLO(self.model_path)
        return self._model

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """
        对单帧图像进行推理。

        Args:
            frame: BGR 格式的 numpy 数组 (H, W, 3)

        Returns:
            检测结果列表（按置信度过滤后）
        """
        results = self.model(frame, verbose=False)

        detections: list[Detection] = []
        for result in results:
            if result.boxes is None:
                continue

            boxes = result.boxes.xyxy.cpu().numpy()       # (N, 4)
            confs = result.boxes.conf.cpu().numpy()        # (N,)
            clss = result.boxes.cls.cpu().numpy().astype(int)  # (N,)

            for box, conf, cls_id in zip(boxes, confs, clss):
                if conf < DETECTION_CONFIDENCE:
                    continue

                x1, y1, x2, y2 = map(int, box)
                class_name = self._resolve_class(cls_id)

                detections.append(Detection(
                    bbox=(x1, y1, x2, y2),
                    class_name=class_name,
                    confidence=float(conf),
                ))

        return detections

    def _resolve_class(self, cls_id: int) -> str:
        """
        将模型输出的类别 ID 映射为类别名。

        队友模型: 使用 CLASS_NAMES 映射（4 个组合类）
        占位模型: 从 YOLO 模型的 names 属性获取 COCO 类别名
        """
        if not self._is_fallback:
            return CLASS_NAMES.get(cls_id, f"class_{cls_id}")
        # 占位模型：使用 YOLO 自带的类别名（如 "person", "car"...）
        if hasattr(self.model, 'names'):
            return self.model.names.get(cls_id, f"class_{cls_id}")
        return f"class_{cls_id}"

    def compute_stats(self, detections: list[Detection]) -> dict:
        """
        从检测结果计算统计数字。

        Args:
            detections: detect() 的返回结果

        Returns:
            {
                "total_persons": int,
                "no_helmet": int,
                "no_vest": int,
            }
        """
        if self._is_fallback:
            # 占位模型：仅统计 person 类，无法区分装备状态
            person_count = sum(
                1 for d in detections if d.class_name == "person"
            )
            return {
                "total_persons": person_count,
                "no_helmet": 0,
                "no_vest": 0,
            }

        # 队友模型：4 个互斥组合类，直接按类别统计
        total = len(detections)
        no_helmet = sum(
            1 for d in detections
            if d.class_name in ("person_no_helmet_vest", "person_no_helmet_no_vest")
        )
        no_vest = sum(
            1 for d in detections
            if d.class_name in ("person_helmet_no_vest", "person_no_helmet_no_vest")
        )

        return {
            "total_persons": total,
            "no_helmet": no_helmet,
            "no_vest": no_vest,
        }
