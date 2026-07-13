# BACKEND_STRUCTURE.md — 后端结构蓝图

## 1. 后端架构概览

```
main.py (启动入口)
    │
    ├── engine/                    # 推理引擎（后台线程）
    │   ├── config.py              # 全局配置常量
    │   ├── capture.py             # 视频流采集器
    │   ├── detector.py            # 目标检测器
    │   ├── pose_estimator.py      # 姿态估计器 + 摔倒判断
    │   ├── alarm.py               # 告警音频管理器
    │   ├── draw.py                # 图像标注绘制
    │   └── pipeline.py            # 主推理管线（编排上述模块）
    │
    └── server/                    # Web 服务（主线程）
        ├── app.py                 # FastAPI 应用工厂
        ├── stream.py              # MJPEG 视频流端点
        ├── ws.py                  # WebSocket 统计推送端点
        └── state.py               # 共享状态（线程安全）
```

### 1.1 线程模型

```
主线程 (MainThread):
  └─ FastAPI + uvicorn 事件循环
     ├─ GET /                    → 静态页面
     ├─ GET /stream/video        → MJPEG StreamingResponse
     ├─ WS /ws/stats             → WebSocket 端点
     └─ GET /api/health          → 健康检查

后台线程 (InferenceThread, daemon=True):
  └─ pipeline.run() 无限循环
      ├─ capture.read()          → 获取一帧
      ├─ detector.detect()       → 检测 4 类目标
      ├─ pose_estimator.estimate() → 姿态 + 摔倒
      ├─ draw.annotate()         → 绘制标注
      ├─ alarm.evaluate()        → 评估 + 播放/停止告警
      ├─ state.update_frame()    → 写入共享帧（线程安全）
      └─ state.update_stats()    → 写入共享统计（线程安全）
```

### 1.2 共享状态 (server/state.py)

```python
# 使用 threading.Lock 保护的共享状态
import threading
from typing import Optional
import numpy as np
from datetime import datetime

class SharedState:
    """线程安全的共享状态，推理线程写入，Web 线程读取"""

    def __init__(self):
        self._lock = threading.Lock()

        # 最新带标注的视频帧 (numpy array)
        self._frame: Optional[np.ndarray] = None

        # 最新 JPEG 编码后的帧 (bytes)
        self._jpeg_frame: Optional[bytes] = None

        # 最新统计数据
        self._stats: dict = {
            "total_persons": 0,
            "no_helmet": 0,
            "no_vest": 0,
            "fall": False,
            "camera_status": "connecting",
            "fps": 0.0,
            "timestamp": None,
        }

    def update_frame(self, frame: np.ndarray, jpeg: bytes):
        with self._lock:
            self._frame = frame
            self._jpeg_frame = jpeg

    def update_stats(self, stats: dict):
        with self._lock:
            self._stats = stats

    def get_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self._jpeg_frame

    def get_stats(self) -> dict:
        with self._lock:
            return self._stats.copy()
```

---

## 2. 数据库设计（远期，本次仅设计）

### 2.1 数据库选型

| 属性 | 值 |
|------|-----|
| 数据库 | SQLite |
| 文件路径 | `data/security_monitor.db` |
| ORM | SQLAlchemy 2.x (远期引入) |
| 本次实现 | ❌ 不实现查询接口，仅定义表结构 |

### 2.2 表设计

#### 表 1: `alarm_events` — 告警事件记录

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 自增主键 |
| `alarm_type` | VARCHAR(20) | NOT NULL | 告警类型: `"no_helmet"`, `"no_vest"`, `"fall"` |
| `violator_count` | INTEGER | NOT NULL DEFAULT 1 | 违规人数（告警触发瞬间） |
| `status` | VARCHAR(10) | NOT NULL DEFAULT "active" | `"active"` / `"resolved"` |
| `started_at` | DATETIME | NOT NULL | 告警开始时间 |
| `resolved_at` | DATETIME | NULL | 告警解除时间 |
| `created_at` | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | 记录创建时间 |

#### 表 2: `detection_snapshots` — 检测快照记录

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 自增主键 |
| `total_persons` | INTEGER | NOT NULL DEFAULT 0 | 总人数 |
| `no_helmet_count` | INTEGER | NOT NULL DEFAULT 0 | 未戴安全帽人数 |
| `no_vest_count` | INTEGER | NOT NULL DEFAULT 0 | 未穿反光衣人数 |
| `fall_detected` | BOOLEAN | NOT NULL DEFAULT 0 | 是否检测到摔倒 |
| `fps` | REAL | NULL | 当前帧率 |
| `recorded_at` | DATETIME | NOT NULL | 记录时间 |

#### 表 3: `system_events` — 系统事件记录

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 自增主键 |
| `event_type` | VARCHAR(30) | NOT NULL | 事件类型: `"system_start"`, `"system_stop"`, `"camera_connected"`, `"camera_disconnected"` |
| `event_data` | TEXT | NULL | JSON 附加数据 |
| `created_at` | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | 事件时间 |

### 2.3 完整 DDL（远期执行）

```sql
CREATE TABLE IF NOT EXISTS alarm_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    alarm_type      VARCHAR(20)  NOT NULL,
    violator_count  INTEGER      NOT NULL DEFAULT 1,
    status          VARCHAR(10)  NOT NULL DEFAULT 'active',
    started_at      DATETIME     NOT NULL,
    resolved_at     DATETIME     NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alarm_events_type ON alarm_events(alarm_type);
CREATE INDEX idx_alarm_events_status ON alarm_events(status);
CREATE INDEX idx_alarm_events_started ON alarm_events(started_at);

CREATE TABLE IF NOT EXISTS detection_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    total_persons   INTEGER NOT NULL DEFAULT 0,
    no_helmet_count INTEGER NOT NULL DEFAULT 0,
    no_vest_count   INTEGER NOT NULL DEFAULT 0,
    fall_detected   BOOLEAN NOT NULL DEFAULT 0,
    fps             REAL    NULL,
    recorded_at     DATETIME NOT NULL
);

CREATE INDEX idx_snapshots_time ON detection_snapshots(recorded_at);

CREATE TABLE IF NOT EXISTS system_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type      VARCHAR(30) NOT NULL,
    event_data      TEXT        NULL,
    created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. API 路由详细定义

### 3.1 `GET /` — 前端入口

- **响应**: `text/html`
- **说明**: 返回 Vue 前端构建后的 `index.html`
- **开发阶段**: 代理到 Vite dev server (`http://localhost:5173`)
- **生产阶段**: 返回 `web/dist/index.html` 内容

### 3.2 `GET /stream/video` — MJPEG 视频流

- **响应**: `multipart/x-mixed-replace; boundary=frame`
- **说明**: 持续推送带 YOLO 标注框的 JPEG 帧

```
帧格式:
--frame
Content-Type: image/jpeg

<JPEG bytes>
--frame
Content-Type: image/jpeg

<JPEG bytes>
...
```

- **实现**: FastAPI `StreamingResponse` + 生成器函数从 `SharedState` 读取最新 JPEG
- **帧率**: 由推理线程决定，约 8-15 FPS（CPU 双模型）
- **空闲时**: 如果没有新帧，等待最多 100ms 后返回当前帧或继续等待

### 3.3 `WS /ws/stats` — WebSocket 统计推送

- **协议**: WebSocket
- **方向**: 服务端 → 客户端（单向推送）

**消息格式:**
```json
{
  "type": "stats",
  "data": {
    "total_persons": 5,
    "no_helmet": 2,
    "no_vest": 1,
    "fall": false,
    "camera_status": "connected",
    "fps": 24.5,
    "timestamp": "2026-07-13T14:30:25.123456"
  }
}
```

- **推送频率**: 由 `server/ws.py` 定时器驱动，每 0.1-0.2 秒（5-10 Hz）从 SharedState 读取最新统计并广播，而非推理线程逐帧推送
- **连接管理**: 维护已连接客户端集合，断开时自动移除

### 3.4 `GET /api/health` — 健康检查

- **响应**: `application/json`

```json
{
  "status": "ok",
  "camera_connected": true,
  "models_loaded": true,
  "uptime_seconds": 3600.5,
  "fps": 24.5
}
```

---

## 4. 模块接口定义

### 4.1 engine/config.py

```python
# 全局配置常量

# 摄像头
MJPEG_URL = "http://192.168.1.100:8081/video_feed/"  # 需根据实际 IP 修改
CAMERA_RECONNECT_INTERVAL = 3  # 断连重试间隔（秒）

# 模型路径
DETECTION_MODEL_PATH = "models/helmet_vest.pt"        # 队友模型
FALLBACK_MODEL_PATH = "yolov8n.pt"                     # 占位模型
POSE_MODEL_PATH = "yolov8n-pose.pt"                    # 姿态模型（自动下载）

# 检测阈值
DETECTION_CONFIDENCE = 0.5     # 检测置信度阈值
POSE_CONFIDENCE = 0.5           # 姿态关键点置信度阈值

# 摔倒判断（多条件 AND，见 PRD.md §F3）
FALL_TORSO_RATIO = 0.25             # 躯干高度(肩-髋) / 身体高度(肩-踝) < 此值
FALL_BBOX_RATIO = 1.2               # bbox_width / bbox_height > 此值（摔倒时宽>高）
POSE_REQUIRED_KEYPOINT_CONF = 0.5   # 肩、髋、踝 6 个关键点置信度 ≥ 此值
FALL_TRIGGER_FRAMES = 3             # 连续 N 帧满足条件 → 触发摔倒告警
FALL_CLEAR_FRAMES = 5               # 连续 N 帧不满足 → 解除摔倒告警

# 安全违规告警状态机
VIOLATION_TRIGGER_FRAMES = 3        # 连续 N 帧检测到违规 → 触发告警
VIOLATION_CLEAR_FRAMES = 5          # 连续 N 帧违规消失 → 解除告警

# 统计推送
STATS_PUSH_INTERVAL = 0.15          # WebSocket 统计推送间隔（秒），即约 6-7 Hz

# JPEG 编码
JPEG_QUALITY = 70                   # MJPEG 推流 JPEG 质量 (0-100)

# 告警音频
ALARM1_PATH = "alarms/alarm1.mp3"   # 安全违规告警
ALARM2_PATH = "alarms/alarm2.mp3"   # 摔倒告警
ALARM_VOLUME = 0.8                   # 音量 (0.0 - 1.0)

# 服务
HOST = "0.0.0.0"
PORT = 8000

# 检测类别映射（队友交付的人体级互斥组合框，每人一个框）
# 4 个类别互斥，一个框 = 一个人，无需去重
CLASS_NAMES = {
    0: "person_helmet_vest",
    1: "person_helmet_no_vest",
    2: "person_no_helmet_vest",
    3: "person_no_helmet_no_vest",
}
```

### 4.2 engine/capture.py

```python
class VideoCapture:
    """从 MJPEG URL 读取视频帧"""

    def __init__(self, url: str):
        self.url = url
        self.cap: cv2.VideoCapture | None = None

    def connect(self) -> bool:
        """建立连接，返回是否成功"""

    def read(self) -> tuple[bool, np.ndarray | None]:
        """读取一帧，返回 (成功, 帧)"""

    def release(self):
        """释放资源"""

    @property
    def is_connected(self) -> bool:
        """当前连接状态"""
```

### 4.3 engine/detector.py

```python
class SafetyGearDetector:
    """安全装备检测器"""

    def __init__(self, model_path: str):
        self.model = YOLO(model_path)

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """
        检测一帧中的安全装备
        返回: [Detection, ...]
        """

class Detection:
    """单个检测结果"""
    bbox: tuple[int, int, int, int]   # (x1, y1, x2, y2)
    class_name: str                    # "person_helmet_vest" | "person_helmet_no_vest" | "person_no_helmet_vest" | "person_no_helmet_no_vest"
    confidence: float
```

### 4.4 engine/pose_estimator.py

```python
class PoseEstimator:
    """人体姿态估计"""

    def __init__(self, model_path: str = "yolov8n-pose.pt"):
        self.model = YOLO(model_path)

    def estimate(self, frame: np.ndarray) -> list[PoseResult]:
        """
        估计一帧中所有人的姿态
        返回: [PoseResult, ...]
        """

class PoseResult:
    """单个姿态估计结果"""
    bbox: tuple[int, int, int, int]              # 人体边界框
    keypoints: list[tuple[float, float, float]]   # 17 个 (x, y, conf)
    is_fallen: bool                                # 是否摔倒

def is_fallen(keypoints: list, bbox: tuple, frame_h: int) -> bool:
    """
    摔倒判断核心逻辑（单帧，多条件 AND，见 PRD.md §F3）
    - 躯干高度 / 身体高度 < FALL_TORSO_RATIO
    - bbox 宽高比 > FALL_BBOX_RATIO
    - 肩、髋、踝 6 关键点置信度 ≥ POSE_REQUIRED_KEYPOINT_CONF
    时序确认（触发 FALL_TRIGGER_FRAMES / 解除 FALL_CLEAR_FRAMES）由调用方 Pipeline 维护
    """
```

### 4.5 engine/alarm.py

```python
class AlarmManager:
    """告警音频管理器"""

    def __init__(self):
        pygame.mixer.init()
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.active_channels: dict[str, pygame.mixer.Channel] = {}

    def load(self, name: str, filepath: str):
        """加载音频文件"""

    def play(self, name: str, loop: bool = True):
        """播放告警（循环），如果已在播放则不做操作"""

    def stop(self, name: str):
        """停止告警"""

    def stop_all(self):
        """停止所有告警"""
```

### 4.6 engine/draw.py

```python
def annotate_frame(
    frame: np.ndarray,
    detections: list[Detection],
    poses: list[PoseResult],
    stats: dict,
) -> np.ndarray:
    """
    在原始帧上绘制：
    - 安全装备检测框（绿色=合规，红色=违规）
    - 人体姿态关键点 + 骨架连线
    - 摔倒标记（红色 "⚠ FALL"）
    - 统计信息叠加（左上角）
    返回带标注的帧
    """
```

### 4.7 engine/pipeline.py

```python
class Pipeline:
    """主推理管线，编排所有模块"""

    def __init__(self, state: SharedState):
        self.state = state
        self.capture = VideoCapture(MJPEG_URL)
        self.detector = SafetyGearDetector(DETECTION_MODEL_PATH)
        self.pose_estimator = PoseEstimator(POSE_MODEL_PATH)
        self.alarm = AlarmManager()

    def run(self):
        """主循环（运行在后台线程）"""
        while True:
            # 1. 读帧
            success, frame = self.capture.read()
            if not success:
                self._handle_disconnect()
                continue

            # 2. 检测
            detections = self.detector.detect(frame)

            # 3. 姿态 + 摔倒
            poses = self.pose_estimator.estimate(frame)

            # 4. 统计
            stats = self._compute_stats(detections, poses)

            # 5. 告警
            self._evaluate_alarm(stats)

            # 6. 绘图
            annotated = annotate_frame(frame, detections, poses, stats)

            # 7. 编码 JPEG（质量 70，平衡清晰度与带宽，见 PRD.md §4.1）
            _, jpeg = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])

            # 8. 更新共享状态
            self.state.update_frame(annotated, jpeg.tobytes())
            self.state.update_stats(stats)

    def _compute_stats(self, detections, poses) -> dict:
        """从检测结果计算统计数据"""

    def _evaluate_alarm(self, stats: dict):
        """根据统计决定播放/停止告警"""

    def _handle_disconnect(self):
        """处理摄像头断连"""
```

---

## 5. FastAPI 应用工厂 (server/app.py)

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from server.state import SharedState
from server.stream import create_stream_router
from server.ws import create_ws_router

def create_app(state: SharedState) -> FastAPI:
    app = FastAPI(title="工业安防监测系统")

    # 流路由
    app.include_router(create_stream_router(state))

    # WebSocket 路由
    app.include_router(create_ws_router(state))

    # 健康检查
    @app.get("/api/health")
    async def health():
        stats = state.get_stats()
        return {
            "status": "ok",
            "camera_connected": stats["camera_status"] == "connected",
            "models_loaded": True,
            "fps": stats["fps"],
        }

    # 生产环境：挂载前端静态文件
    # app.mount("/", StaticFiles(directory="web/dist", html=True), name="static")

    return app
```

---

## 6. 启动入口 (main.py)

```python
import threading
import uvicorn
from engine.pipeline import Pipeline
from server.state import SharedState
from server.app import create_app

def main():
    # 1. 创建共享状态
    state = SharedState()

    # 2. 创建推理管线
    pipeline = Pipeline(state)

    # 3. 启动推理线程（后台）
    inference_thread = threading.Thread(
        target=pipeline.run,
        daemon=True,
        name="InferenceThread"
    )
    inference_thread.start()

    # 4. 创建 FastAPI 应用
    app = create_app(state)

    # 5. 启动 Web 服务（主线程阻塞）
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
```
