# 工业安全监测系统

基于 Ultralytics YOLO、OpenCV、FastAPI 和 Vue 的安全装备与人员摔倒监测课程项目。后端处理视频帧，前端展示画面、人数、违规状态和运行状态，并支持本地声音告警。

## 功能

- 使用 Construction-PPE 检测模型识别安全帽、反光衣等装备；结合人体框统计违规情况。
- 使用 YOLO 姿态模型与连续帧状态判断人员摔倒。
- 支持网络 MJPEG 摄像头、USB 摄像头和本地视频文件。
- 通过 MJPEG 视频流和 WebSocket 向网页推送画面与统计。
- 使用 Pygame 告警音频和 pyttsx3 离线语音播报。

模型效果需要在实际场景中验证，项目当前不提供精度或安全保障承诺。

## 环境与安装

建议使用 Python 3.10 或更高版本；前端使用 Node.js 22.12 或更高版本。语音播报主要在 Windows 环境下开发和使用。

在仓库根目录创建虚拟环境并安装后端依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

如果需要 GPU 加速，请根据硬件及 CUDA 环境选择适配的 PyTorch 安装方式；本仓库不锁定 CUDA 版本。`requirements.txt` 是运行依赖清单，尚未提供经完整环境复现验证的版本锁文件。

安装并构建前端：

```powershell
cd web
npm ci
npm run build
cd ..
```

## 模型与告警音频

- 装备检测模型默认读取 `models/best (2).pt`，需自行准备具有相应使用授权的训练结果。
- 未找到装备模型时，会回退到 `yolov8n.pt`。该通用模型不等同于装备检测模型，不能完成相同的安全帽、反光衣识别。
- 姿态模型默认使用 `yolov8n-pose.pt`。缺失的标准模型可能由 Ultralytics 在首次使用时下载，需要网络连接。
- 可选告警音频放在 `alarms/alarm1.mp3` 和 `alarms/alarm2.mp3`。音频缺失时对应声音告警会停用。
- 模型、音频、训练产物不随本仓库发布；应单独核对模型、数据集和音频授权。

模型路径、置信度和告警参数集中在 `engine/config.py`。

## 本地摄像头配置

真实设备地址不写入源码。配置方式二选一，**环境变量优先于本地 JSON 文件**。

方式一，在启动程序的终端设置环境变量：

```powershell
$env:INDUSTRIAL_SECURITY_MJPEG_URL = "http://127.0.0.1:8081/video_feed"
python main.py
```

方式二，将示例复制为本地配置文件：

```powershell
Copy-Item config.local.example.json config.local.json
```

在 `config.local.json` 的 `mjpeg_url` 中填写自己的实际地址，然后执行 `python main.py`。示例中的 localhost URL 是占位值，不代表仓库自带摄像头服务。本地配置已被 Git 忽略，不要强制提交它。

未配置地址时，网络摄像头模式会在初始化模型前提示配置缺失；USB 和视频文件模式无需网络摄像头地址。`.env` 文件被忽略，但程序不会自动加载 `.env`。

## 启动与访问

从仓库根目录启动：

```powershell
python main.py                 # 网络 MJPEG 摄像头，需要先配置
python main.py 0               # USB 摄像头
python main.py sample.mp4      # 本地视频文件
```

Windows 也可运行 `start.bat` 选择网络或 USB 摄像头；它使用当前终端的 Python 环境。

构建前端后，访问 `http://localhost:8000`。后端接口包括：

| 地址 | 用途 |
|---|---|
| `/api/health` | 服务与摄像头状态 |
| `/stream/video` | MJPEG 视频流 |
| `/ws/stats` | WebSocket 统计 |

开发前端时保持后端运行，另开终端执行 `cd web`、`npm run dev`，访问 Vite 打印的本机地址；开发代理已配置到后端 8000 端口。

后端默认监听 `0.0.0.0:8000`，现有接口没有登录鉴权。请根据实际网络环境限制访问；摄像头画面和视频数据不应提交到公开仓库。

## 项目结构

```text
engine/                     检测、姿态、视频流水线、绘制与告警
server/                     FastAPI、视频流与统计推送
web/                        Vue 前端
docs/                       项目设计与开发记录
main.py                     运行入口
train.py                    模型训练示例
config.local.example.json   公开配置示例
requirements.txt            后端运行依赖
start.bat                   Windows 启动菜单
```

## 验证

配置读取测试不需要摄像头或模型：

```powershell
python -m unittest discover -s tests -v
```

现有 `test_detector.py`、`test_pose.py`、`test_alarm.py` 是需要模型、设备或音频的手动验证脚本，运行前请检查输入资源和声音输出。

## 许可

本版本的项目原创代码采用 **GNU Affero General Public License v3.0 only（AGPL-3.0-only）**，完整条款见 [LICENSE](LICENSE)。允许商业使用；分发受许可覆盖的软件和提供修改版网络服务时，需要按条款提供相应源码。企业内部离线使用不等于自动要求向公众公开全部代码。

Copyright (C) 2026 luther-3 and contributors.

第三方依赖、模型、数据集和音频保留各自许可。Ultralytics 使用 AGPL-3.0 / 企业许可方式提供其软件和模型，请根据实际使用方式核对其 [官方许可说明](https://www.ultralytics.com/license)。
