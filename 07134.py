#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能摄像头控制终端 - 修复电机控制版本
"""

import os
import sys
import time
import datetime
import threading

# ====================== 权限检查 ======================
if os.geteuid() != 0:
    print("=" * 60)
    print("错误：需要使用 root 权限运行！")
    print("请执行：sudo python3 " + " ".join(sys.argv))
    print("=" * 60)
    sys.exit(1)

# ====================== 导入依赖 ======================
print("正在导入依赖库...")

try:
    from flask import Flask, render_template_string, Response, jsonify, request

    print("  Flask: OK")
except ImportError:
    print("  Flask: 安装中...")
    os.system("pip3 install flask -i https://pypi.tuna.tsinghua.edu.cn/simple")
    from flask import Flask, render_template_string, Response, jsonify, request

try:
    import cv2

    print(f"  OpenCV: OK (版本 {cv2.__version__})")
except ImportError:
    print("  OpenCV: 安装中...")
    os.system("pip3 install opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple")
    import cv2

try:
    import wiringpi

    print("  wiringpi: OK")
except ImportError:
    print("  wiringpi: 安装中...")
    os.system("pip3 install wiringpi -i https://pypi.tuna.tsinghua.edu.cn/simple")
    import wiringpi

print("所有依赖导入完成\n")

# ====================== Flask应用 ======================
app = Flask(__name__)

# ====================== 全局变量 =======================
start_time = datetime.datetime.now()
operation_logs = []
current_temp = 0.0
current_hum = 0.0
camera = None
camera_lock = threading.Lock()
camera_ready = False
A0_global = None
A1_global = None

# 电机控制锁（防止并发操作）
motor_lock = threading.Lock()


# ====================== 日志模块 ======================
def log_record(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_str = f"[{now}] {msg}"
    print(log_str, flush=True)
    operation_logs.append(log_str)


# ====================== 温湿度模块 ======================
def init_humiture():
    global A0_global, A1_global
    try:
        wiringpi.wiringPiSetup()
        BASE = 64
        A0_global = BASE + 0
        A1_global = BASE + 1
        wiringpi.htu21dSetup(BASE)
        log_record("温湿度传感器初始化成功")
        return True
    except Exception as e:
        log_record(f"温湿度传感器初始化失败: {e}")
        return False


def read_humiture():
    global current_temp, current_hum
    if A0_global is None or A1_global is None:
        return
    try:
        temp_raw = wiringpi.analogRead(A0_global)
        hum_raw = wiringpi.analogRead(A1_global)
        current_temp = temp_raw / 10.0
        current_hum = hum_raw / 10.0
    except Exception as e:
        log_record(f"温湿度读取失败: {e}")


# ====================== 电机模块（关键修复）======================
# 水平电机（左右转）
HORIZONTAL_PINS = [3, 4, 6, 9]
# 俯仰电机（上下转）
VERTICAL_PINS = [10, 13, 15, 16]
ALL_PINS = HORIZONTAL_PINS + VERTICAL_PINS

# 步进序列
SEQUENCE = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1]
]


def init_motor():
    try:
        for pin in ALL_PINS:
            wiringpi.pinMode(pin, 1)  # 输出模式
            wiringpi.digitalWrite(pin, 0)  # 初始低电平
        log_record(f"电机引脚初始化完成: 水平{HORIZONTAL_PINS}, 俯仰{VERTICAL_PINS}")
    except Exception as e:
        log_record(f"电机初始化失败: {e}")


def rotate_motor(motor_pins, angle):
    """
    直接控制电机旋转 - 同步执行，带锁保护
    """
    with motor_lock:  # 确保同一时间只有一个电机在转
        if angle == 0:
            return

        try:
            log_record(f"【电机启动】引脚{motor_pins} 旋转{angle}°")

            # 选择正转或反转序列
            seq = SEQUENCE if angle > 0 else SEQUENCE[::-1]

            # 计算步数 (4096步 = 360°)
            step_num = int(abs(angle) / 360.0 * 4096)
            if step_num == 0:
                step_num = 1  # 至少走一步

            log_record(f"  步数: {step_num}")

            # 逐步执行
            for i in range(step_num):
                step = seq[i % 8]
                for pin, value in zip(motor_pins, step):
                    wiringpi.digitalWrite(pin, value)
                time.sleep(0.002)  # 稍微慢一点，更稳定

            # 断电（防止发热）
            for pin in motor_pins:
                wiringpi.digitalWrite(pin, 0)

            log_record(f"【电机完成】旋转{angle}° 完成")

        except Exception as e:
            log_record(f"【电机错误】{e}")
            # 出错时全部断电
            for pin in ALL_PINS:
                wiringpi.digitalWrite(pin, 0)


def motor_stop_all():
    with motor_lock:
        try:
            for pin in ALL_PINS:
                wiringpi.digitalWrite(pin, 0)
            log_record("所有电机停止")
        except Exception as e:
            log_record(f"电机停止失败: {e}")


# ====================== 摄像头模块 ======================
def init_camera():
    global camera, camera_ready

    # 释放旧摄像头
    if camera is not None:
        try:
            camera.release()
        except:
            pass
        camera = None

    camera_ready = False

    # 查找可用摄像头
    for i in range(10):
        dev_path = f"/dev/video{i}"
        if not os.path.exists(dev_path):
            continue

        try:
            cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
            if not cap.isOpened():
                continue

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            time.sleep(0.3)

            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                camera = cap
                camera_ready = True
                h, w = frame.shape[:2]
                log_record(f"摄像头就绪 /dev/video{i}: {w}x{h}")
                return True

            cap.release()
        except:
            pass

    log_record("摄像头初始化失败")
    return False


def generate_frames():
    global camera, camera_ready

    while True:
        with camera_lock:
            local_camera = camera
            is_ready = camera_ready

        if local_camera is None or not is_ready:
            time.sleep(0.5)
            continue

        try:
            ret, frame = local_camera.read()
            if not ret or frame is None:
                time.sleep(0.1)
                continue

            # 叠加温湿度
            cv2.putText(frame, f"Temp: {current_temp:.1f}C", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Hum: {current_hum:.1f}%RH", (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # 编码
            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

            time.sleep(0.04)  # ~25fps

        except Exception as e:
            time.sleep(0.1)


# ====================== Web页面 ======================
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能摄像头控制终端</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 15px;
            min-height: 100vh;
        }
        h1 { color: #58a6ff; margin-bottom: 15px; font-size: 22px; text-align: center; }
        .video-box {
            width: 100%;
            max-width: 640px;
            background: #161b22;
            border: 2px solid #30363d;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 15px;
        }
        .video-box img { width: 100%; height: auto; display: block; }
        .info-bar {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .info-item {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 16px;
        }
        .info-item .label { color: #8b949e; }
        .info-item .value { color: #3fb950; font-weight: bold; font-size: 18px; }
        .controls {
            display: grid;
            grid-template-columns: repeat(3, 90px);
            grid-template-rows: repeat(3, 90px);
            gap: 12px;
            margin-top: 10px;
        }
        .btn {
            width: 90px;
            height: 90px;
            border: none;
            border-radius: 12px;
            background: #21262d;
            color: #c9d1d9;
            font-size: 32px;
            cursor: pointer;
            transition: all 0.15s;
            border: 1px solid #30363d;
        }
        .btn:hover { background: #30363d; transform: scale(1.05); }
        .btn:active { transform: scale(0.95); }
        .btn-up { grid-column: 2; grid-row: 1; background: #1f4d1f; }
        .btn-left { grid-column: 1; grid-row: 2; background: #1f4d1f; }
        .btn-center { grid-column: 2; grid-row: 2; background: #da3633; font-size: 14px; font-weight: bold; }
        .btn-right { grid-column: 3; grid-row: 2; background: #1f4d1f; }
        .btn-down { grid-column: 2; grid-row: 3; background: #1f4d1f; }
        .status {
            margin-top: 15px;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            text-align: center;
        }
        .status.ok { background: #238636; color: #fff; }
        .status.err { background: #da3633; color: #fff; }
        .status.info { background: #1f6feb; color: #fff; }
        .status.warn { background: #9e8c00; color: #fff; }

        @media (max-width: 480px) {
            h1 { font-size: 18px; }
            .controls { grid-template-columns: repeat(3, 75px); grid-template-rows: repeat(3, 75px); }
            .btn { width: 75px; height: 75px; font-size: 26px; }
            .btn-center { font-size: 12px; }
            .info-item { padding: 10px 18px; font-size: 14px; }
        }
    </style>
</head>
<body>
    <h1>智能摄像头控制终端</h1>

    <div class="video-box">
        <img src="{{ url_for('video_feed') }}" alt="摄像头画面">
    </div>

    <div class="info-bar">
        <div class="info-item">
            <span class="label">温度：</span>
            <span class="value" id="temp">--</span>
            <span class="label">℃</span>
        </div>
        <div class="info-item">
            <span class="label">湿度：</span>
            <span class="value" id="hum">--</span>
            <span class="label">%RH</span>
        </div>
    </div>

    <div class="controls">
        <button class="btn btn-up" onclick="control('up')" title="俯仰上">▲</button>
        <button class="btn btn-left" onclick="control('left')" title="水平左转">◀</button>
        <button class="btn btn-center" onclick="control('stop')" title="停止">STOP</button>
        <button class="btn btn-right" onclick="control('right')" title="水平右转">▶</button>
        <button class="btn btn-down" onclick="control('down')" title="俯仰下">▼</button>
    </div>

    <div id="status" class="status info">等待操作...</div>

    <script>
        // 更新温湿度
        function updateData() {
            fetch('/api/data')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('temp').textContent = data.temp.toFixed(1);
                    document.getElementById('hum').textContent = data.hum.toFixed(1);
                })
                .catch(() => {
                    document.getElementById('temp').textContent = '--';
                    document.getElementById('hum').textContent = '--';
                });
        }
        setInterval(updateData, 2000);
        updateData();

        // 控制云台 - 关键修复：添加更多调试
        function control(direction) {
            const status = document.getElementById('status');
            status.className = 'status info';
            status.textContent = '执行: ' + direction + '...';

            console.log('发送控制:', direction);  // 浏览器调试

            fetch('/api/control', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({direction: direction})
            })
            .then(r => {
                console.log('响应状态:', r.status);
                return r.json();
            })
            .then(data => {
                console.log('响应数据:', data);
                status.className = 'status ok';
                status.textContent = '完成: ' + direction;
            })
            .catch(e => {
                console.error('错误:', e);
                status.className = 'status err';
                status.textContent = '失败: ' + e;
            });
        }
    </script>
</body>
</html>'''


# ====================== Flask路由 ======================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/video_feed')
def video_feed():
    global camera_ready

    is_ready = False
    with camera_lock:
        is_ready = camera_ready

    if not is_ready:
        # 返回空白图片
        return Response(b'\x89PNG\r\n\x1a\n', mimetype='image/png')

    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/data')
def api_data():
    return jsonify({
        'temp': current_temp,
        'hum': current_hum,
        'camera_ready': camera_ready
    })


@app.route('/api/control', methods=['POST'])
def api_control():
    """
    电机控制API - 关键修复：直接同步执行，不用子线程
    """
    try:
        data = request.get_json() or {}
    except:
        data = {}

    direction = data.get('direction', '')
    log_record(f"【API收到】方向: {direction}")

    # 直接执行电机控制（不用子线程，避免wiringPi线程问题）
    if direction == 'up':
        rotate_motor(VERTICAL_PINS, 15)  # 俯仰上
    elif direction == 'down':
        rotate_motor(VERTICAL_PINS, -15)  # 俯仰下
    elif direction == 'left':
        rotate_motor(HORIZONTAL_PINS, -15)  # 水平左转
    elif direction == 'right':
        rotate_motor(HORIZONTAL_PINS, 15)  # 水平右转
    elif direction == 'stop':
        motor_stop_all()
    else:
        log_record(f"【API错误】未知方向: {direction}")
        return jsonify({'status': 'error', 'message': 'unknown direction'})

    return jsonify({'status': 'ok', 'direction': direction})


# ====================== 后台线程 ======================
def humiture_loop():
    while True:
        read_humiture()
        time.sleep(2)


# ====================== 主程序 ======================
def main():
    log_record("=" * 50)
    log_record("智能摄像头控制终端启动")
    log_record("=" * 50)

    # 获取IP
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        log_record(f"本机IP: {ip}")
    except:
        ip = "unknown"

    # 初始化硬件
    init_humiture()
    init_motor()
    init_camera()

    # 启动温湿度采集
    threading.Thread(target=humiture_loop, daemon=True).start()

    log_record(f"请访问: http://{ip}:8081")
    log_record("电机引脚: 水平" + str(HORIZONTAL_PINS) + " 俯仰" + str(VERTICAL_PINS))

    # 启动Flask
    try:
        app.run(host='0.0.0.0', port=8081, debug=False, threaded=True)
    except KeyboardInterrupt:
        log_record("收到退出信号")
    finally:
        motor_stop_all()
        if camera is not None:
            try:
                camera.release()
            except:
                pass
        log_record("程序退出")


if __name__ == "__main__":
    main()
