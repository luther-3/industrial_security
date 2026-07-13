# IMPLEMENTATION_PLAN.md — 实施计划

## 总览

```
阶段 1         阶段 2         阶段 3          阶段 4
环境搭建  →   摄像头连通  →  检测器骨架  →   姿态+摔倒
[1-2h]        [1h]           [2-3h]          [2-3h]

阶段 5         阶段 6         阶段 7          阶段 8
告警音频  →   FastAPI后端  →  Vue前端     →   队友模型接入
[1h]          [3-4h]         [3-4h]          [1-2h]

阶段 9
联调测试
[2-3h]
```

**总预计时间**: 约 18-24 小时

---

## 阶段 1: 环境搭建

### 目标
创建项目骨架，安装所有依赖，确认 Python 和 Node.js 环境可用。

### 步骤

#### 1.1 创建目录结构
```bash
mkdir -p industrial_security/{engine,server,web/src/{components,composables,stores,assets},models,alarms,docs}
```

#### 1.2 编写 requirements.txt
- 内容参见 TECH_STACK.md § 2.3

#### 1.3 激活 conda 环境并安装缺失依赖
```bash
conda activate yolo26_env
pip install pygame                # 唯一缺失的依赖
```
其他依赖（ultralytics, opencv, fastapi, uvicorn, numpy, websockets）已在 yolo26_env 中安装。

#### 1.4 搭建 Vue 3 前端项目
```bash
cd web
npm create vite@latest . -- --template vue   # 在当前目录创建
npm install
npm install element-plus pinia @element-plus/icons-vue
```

#### 1.5 验证
```bash
python -c "import ultralytics; print('YOLO OK')"
python -c "import cv2; print('OpenCV OK:', cv2.__version__)"
python -c "import fastapi; print('FastAPI OK')"
python -c "import pygame; print('pygame OK')"
cd web && npm run dev   # 确认 Vite 启动成功
```

### 产出物
- [x] 完整的项目目录
- [x] requirements.txt
- [x] 虚拟环境可用
- [x] Vue 项目骨架可启动

---

## 阶段 2: 摄像头连通

### 目标
通过 OpenCV 从摄像头 MJPEG 地址成功拉流并显示。

### 前提条件
- 知道摄像头的 IP 地址（需现场确认）
- 摄像头已上电并推流

### 步骤

#### 2.1 编写 engine/config.py
- 填入以下变量（值后续修改）：
  - `MJPEG_URL = "http://<camera-ip>:8081/video_feed/"`
  - 其他常量见 BACKEND_STRUCTURE.md § 4.1

#### 2.2 编写 engine/capture.py
- `VideoCapture` 类，封装 `cv2.VideoCapture(url)`
- `connect()` 方法
- `read()` 返回 `(success, frame)`
- `is_connected` 属性

#### 2.3 编写测试脚本 test_camera.py
```python
from engine.capture import VideoCapture
from engine.config import MJPEG_URL
import cv2

cap = VideoCapture(MJPEG_URL)
if not cap.connect():
    print(f"无法连接到摄像头: {MJPEG_URL}")
    exit(1)

print("已连接，按 Q 退出")
while True:
    success, frame = cap.read()
    if success:
        cv2.imshow("Camera Test", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

#### 2.4 验证
- 运行 `python test_camera.py`，看到摄像头实时画面

### 产出物
- [x] engine/config.py
- [x] engine/capture.py
- [x] test_camera.py（验证用）

---

## 阶段 3: 检测器骨架

### 目标
用 YOLO 预训练模型跑通目标检测管线，验证模型加载和推理流程。

### 步骤

#### 3.1 编写 engine/detector.py
- `SafetyGearDetector` 类
- `Detection` 数据类
- 先用 YOLOv8n（COCO 预训练）作为占位模型
- 仅检测 `person` 类作为验证

#### 3.2 编写 engine/draw.py
- `annotate_frame()` 函数
- 绘制边界框 + 类别标签
- 颜色映射：合规用绿色，违规用红色

#### 3.3 编写测试脚本 test_detector.py
```python
from engine.capture import VideoCapture
from engine.detector import SafetyGearDetector
from engine.draw import annotate_frame
from engine.config import MJPEG_URL
import cv2

# 使用占位模型（COCO person 检测）
detector = SafetyGearDetector("yolov8n.pt")
cap = VideoCapture(MJPEG_URL)
cap.connect()

while True:
    success, frame = cap.read()
    if not success: continue

    detections = detector.detect(frame)
    annotated = annotate_frame(frame, detections)

    cv2.imshow("Detection Test", annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'): break
```

#### 3.4 验证
- 画面中的人物被检测框包围
- 检测框颜色和标签正确

### 产出物
- [x] engine/detector.py
- [x] engine/draw.py
- [x] test_detector.py（验证用）

---

## 阶段 4: 姿态估计 + 摔倒检测

### 目标
用 YOLOv8n-pose 跑通姿态估计，实现摔倒判断逻辑。

### 步骤

#### 4.1 编写 engine/pose_estimator.py
- `PoseEstimator` 类
- `PoseResult` 数据类（包含 `is_fallen` 字段）
- `is_fallen()` 独立函数：COCO 17 关键点 → 几何计算 → bool
- 首次运行自动下载 `yolov8n-pose.pt`

#### 4.2 摔倒检测逻辑实现
```python
def is_fallen(keypoints, frame_h):
    shoulder_y = (keypoints[5][1] + keypoints[6][1]) / 2
    hip_y      = (keypoints[11][1] + keypoints[12][1]) / 2
    ankle_y    = (keypoints[15][1] + keypoints[16][1]) / 2
    torso_height = abs(hip_y - shoulder_y)
    body_height  = abs(shoulder_y - ankle_y)
    if body_height > 0 and torso_height / body_height < 0.25:
        return True
    return False
```

#### 4.3 增强 draw.py
- 在人体上绘制 17 个关键点（圆点）
- 绘制骨架连线（肩-肘-腕、肩-髋-膝-踝）
- 摔倒人物绘制红色 "⚠ FALL" 文字 + 闪烁红色边框

#### 4.4 编写测试脚本 test_pose.py
- 验证姿态估计 + 摔倒判断
- 模拟摔倒场景测试

#### 4.5 验证
- 正常站立人物显示骨架
- 模拟弯腰/躺倒 → 触发 `is_fallen = True` → 显示 "⚠ FALL"

### 产出物
- [x] engine/pose_estimator.py
- [x] engine/draw.py（更新）
- [x] test_pose.py（验证用）

---

## 阶段 5: 告警音频

### 目标
用 pygame 实现告警音播放/停止管理。

### 步骤

#### 5.1 准备音频文件
- `alarms/alarm1.mp3` — 安全违规（短促连续警报）
- `alarms/alarm2.mp3` — 摔倒（更高音调的紧急警报）
- 建议从免费音效网站下载（如 freesound.org）

#### 5.2 编写 engine/alarm.py
- `AlarmManager` 类
- `load(name, filepath)` — 加载音频
- `play(name, loop=True)` — 循环播放（幂等：已播放则跳过）
- `stop(name)` — 停止播放
- `stop_all()` — 停止所有

#### 5.3 编写测试脚本 test_alarm.py
- 加载两个音频
- 播放 3 秒后自动停止
- 检查无报错

#### 5.4 验证
- 运行测试脚本，PC 扬声器播放告警音

### 产出物
- [x] alarms/alarm1.mp3
- [x] alarms/alarm2.mp3
- [x] engine/alarm.py
- [x] test_alarm.py（验证用）

---

## 阶段 6: FastAPI 后端

### 目标
搭建 Web 服务，提供 MJPEG 视频流 + WebSocket 统计推送。

### 步骤

#### 6.1 编写 server/state.py
- `SharedState` 类，线程安全
- `update_frame()`, `get_jpeg()`
- `update_stats()`, `get_stats()`

#### 6.2 编写 server/stream.py
- MJPEG 流端点 `GET /stream/video`
- 生成器函数从 SharedState 持续读取 JPEG
- 帧间隔自适应

#### 6.3 编写 server/ws.py
- WebSocket 端点 `WS /ws/stats`
- 维护客户端集合
- 定时从 SharedState 读取统计并广播

#### 6.4 编写 server/app.py
- FastAPI 应用工厂
- 挂载路由
- 健康检查端点

#### 6.5 编写 engine/pipeline.py
- `Pipeline` 类，编排 capture → detector → pose → draw → alarm → state
- `run()` 方法，无线循环

#### 6.6 编写 main.py
- 启动入口
- 创建 SharedState → Pipeline → 推理线程 → FastAPI 启动

#### 6.7 验证
- 运行 `python main.py`
- 浏览器访问 `http://localhost:8000/stream/video` — 看到 MJPEG 视频流
- 浏览器控制台连接 `ws://localhost:8000/ws/stats` — 收到 JSON 统计

### 产出物
- [x] server/state.py
- [x] server/stream.py
- [x] server/ws.py
- [x] server/app.py
- [x] engine/pipeline.py
- [x] main.py

---

## 阶段 7: Vue 前端

### 目标
搭建完整的监控仪表盘界面。

### 步骤

#### 7.1 Vite 代理配置 (vite.config.js)
```javascript
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/stream': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
      '/api': 'http://localhost:8000',
    }
  }
})
```

#### 7.2 Pinia Store (stores/monitor.js)
- 定义状态结构和更新 mutation
- 见 FRONTEND_GUIDELINES.md § 11

#### 7.3 WebSocket Composable (composables/useWebSocket.js)
- `connect(url)` — 建立连接
- `onMessage(callback)` — 消息处理
- `disconnect()` — 断开
- 自动重连（断连后 3 秒重试）

#### 7.4 组件开发顺序

**7.4.1 TopNavBar.vue**
- 左侧 Logo + 标题 "工业安防监测系统"
- 右侧系统状态灯

**7.4.2 VideoMonitor.vue**
- `<img>` 标签，src 指向 `/stream/video`
- 摔倒时叠加 AlertOverlay

**7.4.3 AlertOverlay.vue**
- 条件渲染 `v-if="store.fall"`
- CSS 动画闪烁
- 文字 "⚠ 摔倒警告"

**7.4.4 StatCard.vue**
- Props: `label`, `value`, `isAlert`
- 正常态绿色数字，告警态红色数字 + 淡红背景

**7.4.5 StatsPanel.vue**
- 包含 4 个 StatCard（总人数、未戴帽、未穿衣、摔倒）
- 从 Pinia store 读取数据

**7.4.6 SystemInfo.vue**
- FPS 显示、运行时间、摄像头状态

**7.4.7 BottomStatusBar.vue**
- 摄像头 IP、模型文件名

**7.4.8 App.vue (布局组合)**
- 组合上述所有组件
- CSS Grid/Flexbox 布局

#### 7.5 验证
- `npm run dev` 启动前端开发服务器
- 同时运行 `python main.py`
- 浏览器访问 `http://localhost:5173`（开发模式）
- 画面正常显示、统计数据实时更新、告警态正确切换

### 产出物
- [x] web/src/stores/monitor.js
- [x] web/src/composables/useWebSocket.js
- [x] web/src/components/* （全部组件）
- [x] web/src/App.vue
- [x] web/vite.config.js

---

## 阶段 8: 队友模型接入

### 目标
将占位模型替换为队友训练的 `helmet_vest.pt`。

### 前提条件
- 队友交付 `helmet_vest.pt`
- 模型类别名为 `helmet`, `no-helmet`, `vest`, `no-vest`

### 步骤

#### 8.1 放入模型文件
- 复制 `helmet_vest.pt` 到 `models/helmet_vest.pt`

#### 8.2 更新 config.py
- 将 `DETECTION_MODEL_PATH` 指向队友模型
- 移除 fallback 逻辑（或保留作为不存在时的降级）

#### 8.3 更新 draw.py
- 类别名对应颜色映射
- 安全装备标签中文或英文

#### 8.4 验证
- 运行系统，确认：
  - 戴安全帽 → 绿色框 "HELMET"
  - 未戴安全帽 → 红色框 "NO-HELMET" + 告警音 1 播放
  - 穿反光衣 → 绿色框 "VEST"
  - 未穿反光衣 → 红色框 "NO-VEST" + 告警音 1 播放

### 产出物
- [x] models/helmet_vest.pt（队友交付）
- [x] config.py（已更新）
- [x] 正常工作的安全装备检测

---

## 阶段 9: 联调测试

### 目标
端到端测试完整系统，修复问题。

### 测试场景

#### 9.1 正常场景
- 人在摄像头前正常行走，佩戴安全帽 + 反光衣
- **预期**: 绿色框、无告警、统计数字全 0

#### 9.2 安全违规场景
- 人摘下安全帽 / 脱下反光衣
- **预期**: 红色框、"NO-HELMET" / "NO-VEST"、告警音 1 循环播放、统计面板红色高亮

#### 9.3 摔倒场景
- 人模拟摔倒动作（坐下/躺下）
- **预期**: "⚠ FALL" 标记、视频叠加警告、告警音 2 循环播放

#### 9.4 混合场景
- 多人同时存在，有的违规有的正常
- **预期**: 统计数字准确、每个人框颜色独立正确

#### 9.5 异常场景
- 摄像头断电后恢复
- **预期**: 界面显示断连状态，恢复后自动重连

#### 9.6 长时间运行
- 系统持续运行 10+ 分钟
- **预期**: 无内存泄漏、FPS 稳定、无明显卡顿

### 产出物
- [x] 测试通过记录
- [x] 已知问题列表（如有）

---

## 开发原则

1. **每个阶段独立可验证**: 完成一个阶段后立即测试，不要全部写完再测
2. **先跑通再优化**: 优先实现功能，FPS 优化和代码清理后续再做
3. **测试脚本保留**: 每个阶段的测试脚本放在项目根目录，方便后续调试
4. **Git 提交时机**: 每个阶段完成后提交一次
5. **队友接口提前对齐**: 在阶段 3 就用占位模型跑通，队友模型到了直接替换
