# TECH_STACK.md — 技术栈文档

## 1. 开发环境

| 项目 | 版本/说明 |
|------|----------|
| 操作系统 | Windows 11 Home China 10.0.26200 |
| Conda 环境 | `yolo26_env` (路径: `<conda-environment>`) |
| Python | 3.12.13 |
| Node.js | ≥ 18.x (LTS) |
| 包管理器 (Python) | pip (conda 环境内置) |
| 包管理器 (Node) | npm |
| Shell | Git Bash (Windows) |
| IDE | VS Code |
| 版本管理 | Git |

---

## 2. Python 依赖 (requirements.txt)

### 2.1 核心依赖 (已安装 ✅ / 待安装 ⬜)

| 包名 | 当前版本 | 用途 | 状态 |
|------|---------|------|------|
| `ultralytics` | `8.4.92` | YOLO 目标检测 + 姿态估计 | ✅ 已安装 |
| `opencv-python` | `4.12.0.88` | 视频流采集 + 图像绘制 | ✅ 已安装 |
| `fastapi` | `0.139.0` | Web 后端框架 | ✅ 已安装 |
| `uvicorn` | `0.51.0` | ASGI 服务器 | ✅ 已安装 |
| `numpy` | `2.2.6` | 数组计算 | ✅ 已安装 |
| `websockets` | `16.1` | WebSocket 支持 | ✅ 已安装 |
| `torch` | `2.13.0` | PyTorch 后端 | ✅ 已安装 |
| `torchvision` | `0.28.0` | 图像变换 | ✅ 已安装 |
| `pygame` | — | 音频播放 (PC 扬声器告警) | ⬜ 待安装 |

### 2.2 待安装依赖

```bash
conda activate yolo26_env
pip install pygame
```

---

## 3. 前端依赖 (package.json)

### 3.1 核心依赖

| 包名 | 版本锁定 | 用途 |
|------|---------|------|
| `vue` | `^3.5.0` | 前端框架 |
| `element-plus` | `^2.9.0` | UI 组件库 |
| `pinia` | `^2.2.0` | 状态管理 |
| `@element-plus/icons-vue` | `^2.3.0` | Element Plus 图标 |

### 3.2 开发依赖

| 包名 | 版本锁定 | 用途 |
|------|---------|------|
| `vite` | `^6.0.0` | 构建工具 |
| `@vitejs/plugin-vue` | `^5.2.0` | Vite Vue 插件 |

### 3.3 完整 package.json dependencies

```json
{
  "dependencies": {
    "vue": "^3.5.0",
    "element-plus": "^2.9.0",
    "pinia": "^2.2.0",
    "@element-plus/icons-vue": "^2.3.0"
  },
  "devDependencies": {
    "vite": "^6.0.0",
    "@vitejs/plugin-vue": "^5.2.0"
  }
}
```

---

## 4. 外部模型文件

| 文件 | 来源 | 用途 | 备注 |
|------|------|------|------|
| `yolov8n-pose.pt` | Ultralytics 官方 | 人体姿态估计 (17 关键点) | 首次运行自动下载 |
| `helmet_vest.pt` | 队友交付 | 安全帽/反光衣 4 类检测 | 手动放入 `models/` |

---

## 5. API 与服务

### 5.1 对外暴露

| 服务 | 协议 | 地址 | 说明 |
|------|------|------|------|
| Web 前端 | HTTP | `http://localhost:8000/` | SPA 入口 |
| MJPEG 视频流 | HTTP | `http://localhost:8000/stream/video` | 带标注框的实时视频 |
| WebSocket 统计 | WS | `ws://localhost:8000/ws/stats` | 实时 JSON 统计推送 |
| 健康检查 | HTTP | `http://localhost:8000/api/health` | 服务状态 |

### 5.2 外部依赖

| 服务 | 协议 | 地址 | 说明 |
|------|------|------|------|
| 摄像头 MJPEG 流 | HTTP | `http://<camera-ip>:8081/video_feed/` | H618 摄像头推流地址 |

---

## 6. 不依赖的服务

以下内容本项目**不需要**，明确排除：

| 不需要的服务 | 原因 |
|-------------|------|
| Redis | 无缓存需求 |
| PostgreSQL / MySQL | 无数据库查询需求（仅设计表结构） |
| Docker | 单机 Python 直接运行 |
| Nginx | uvicorn 直接服务，单机访问 |
| GPU / CUDA | CPU 推理 |

---

## 7. 版本兼容性说明

- Python 版本下限为 3.10（支持 `match` 语法和类型注解）
- ultralytics 8.3.x 已确认支持 YOLOv8-pose 和自定义 `.pt` 模型加载
- pygame 2.6.x 在 Windows 上已确认支持 MP3 播放
- Vue 3.5 + Element Plus 2.9 组合稳定，国内镜像可正常安装
- Vite 6.x 要求 Node.js ≥ 18.x

---

## 8. 开发环境搭建命令

```bash
# 1. 激活 conda 环境（每次开发前执行）
conda activate yolo26_env

# 2. 安装缺失依赖（仅首次需要）
pip install pygame

# 3. 前端（仅首次需要安装）
cd web
npm install

# 4. 前端开发模式
cd web
npm run dev                    # 开发模式 (http://localhost:5173)

# 5. 前端生产构建
cd web
npm run build                  # 输出到 web/dist/

# 6. 启动后端
cd industrial_security
python main.py                 # 访问 http://localhost:8000
```
