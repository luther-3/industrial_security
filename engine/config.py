"""
全局配置常量
公共参数集中管理；设备地址由环境变量或本地配置提供。
"""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit


def load_mjpeg_url(config_path: Path | None = None) -> str:
    """Read the private camera URL without putting its value in errors."""
    value = os.environ.get("INDUSTRIAL_SECURITY_MJPEG_URL", "").strip()
    if not value:
        config_path = config_path or Path(__file__).resolve().parents[1] / "config.local.json"
        try:
            settings = json.loads(config_path.read_text(encoding="utf-8-sig"))
        except FileNotFoundError:
            return ""
        except (OSError, ValueError):
            raise ValueError("无法读取 config.local.json，请检查文件权限和 JSON 格式。") from None
        if not isinstance(settings, dict):
            raise ValueError("config.local.json 必须是 JSON 对象。")
        value = settings.get("mjpeg_url", "")
        if not isinstance(value, str):
            raise ValueError("config.local.json 的 mjpeg_url 必须是字符串。")
        value = value.strip()
    if value:
        try:
            parsed = urlsplit(value)
            valid = parsed.scheme in {"http", "https"} and bool(parsed.hostname)
            # Reject malformed ports without echoing the private address.
            parsed.port
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("摄像头地址必须是有效的 HTTP 或 HTTPS URL。")
    return value

# ============================================================
# 摄像头
# ============================================================

# 环境变量优先；config.local.json 不提交到 Git。
# USB 摄像头和视频文件模式无需设置此值。
MJPEG_URL = load_mjpeg_url()

# 断连重试间隔（秒）
CAMERA_RECONNECT_INTERVAL = 3

# 视频帧缩放到此尺寸输入模型（降低 CPU 负载）
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# ============================================================
# 模型路径
# ============================================================

# Construction-PPE 官方数据集训练模型（11类装备级检测）
DETECTION_MODEL_PATH = "models/best (2).pt"

# 占位模型：队友模型未交付时使用 YOLOv8n COCO 预训练
FALLBACK_MODEL_PATH = "yolov8n.pt"

# 姿态估计模型（YOLOv8n-pose，首次运行自动下载）
POSE_MODEL_PATH = "yolov8n-pose.pt"

# ============================================================
# 检测阈值
# ============================================================

# 安全装备检测置信度阈值
DETECTION_CONFIDENCE = 0.1

# 姿态关键点置信度阈值
POSE_CONFIDENCE = 0.5

# ============================================================
# 摔倒判断（多条件 AND）
# ============================================================

# 躯干高度(肩-髋) / 身体高度(肩-踝) < 此值
FALL_TORSO_RATIO = 0.35

# bbox_width / bbox_height > 此值（摔倒时宽 > 高）
FALL_BBOX_RATIO = 0.8

# 肩、髋、踝 6 个关键点置信度 ≥ 此值
POSE_REQUIRED_KEYPOINT_CONF = 0.4

# 连续满足条件的帧数 → 触发摔倒告警
FALL_TRIGGER_FRAMES = 3

# 连续不满足条件的帧数 → 解除摔倒告警（比触发慢，防止警告字符闪烁）
FALL_CLEAR_FRAMES = 15

# ============================================================
# 安全违规告警状态机
# ============================================================

# 连续检测到违规的帧数 → 触发告警
VIOLATION_TRIGGER_FRAMES = 3

# 连续违规消失的帧数 → 解除告警
VIOLATION_CLEAR_FRAMES = 5

# ============================================================
# 统计推送
# ============================================================

# WebSocket 统计推送间隔（秒），约 6-7 Hz
STATS_PUSH_INTERVAL = 0.15

# ============================================================
# JPEG 编码
# ============================================================

# MJPEG 推流 JPEG 质量 (0-100)，平衡清晰度与带宽
JPEG_QUALITY = 70

# ============================================================
# 告警音频
# ============================================================

# 安全违规告警音频文件
ALARM1_PATH = "alarms/alarm1.mp3"

# 摔倒告警音频文件
ALARM2_PATH = "alarms/alarm2.mp3"

# 音量 (0.0 - 1.0)
ALARM_VOLUME = 0.3

# ============================================================
# 服务
# ============================================================

HOST = "0.0.0.0"
PORT = 8000

# ============================================================
# 检测类别映射（Construction-PPE 官方数据集，11类装备级检测）
# ============================================================

CLASS_NAMES = {
    0:  "helmet",
    1:  "gloves",
    2:  "vest",
    3:  "boots",
    4:  "goggles",
    5:  "none",
    6:  "Person",
    7:  "no_helmet",
    8:  "no_goggle",
    9:  "no_gloves",
    10: "no_boots",
}

CLASS_COLORS = {
    "helmet":    (103, 194, 58), "vest":      (103, 194, 58),
    "gloves":    (103, 194, 58), "boots":     (103, 194, 58),
    "goggles":   (103, 194, 58),
    "no_helmet": (108, 108, 245), "none":     (108, 108, 245),
    "no_goggle": (108, 108, 245), "no_gloves": (108, 108, 245),
    "no_boots":  (108, 108, 245),
    "Person":    (200, 200, 200),
}

CLASS_LABELS = {
    "helmet": "HELMET", "vest": "VEST", "no_helmet": "NO-HELMET",
    "none": "NO-GEAR", "Person": "PERSON",
}

# 违规类别集合（用于装备→人体 IoU 匹配统计）
NO_HELMET_CLASSES = {"no_helmet", "none"}
NO_VEST_CLASSES = {"none"}

# 画面显示的类别（其他11类不画框，减少视觉干扰）
DISPLAY_CLASSES = {"helmet", "no_helmet", "vest", "Person"}
