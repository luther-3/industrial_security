#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能摄像头控制终端 - 摄像头修复版
"""

import os
import sys
import time
import datetime
import threading
import queue

if os.geteuid() != 0:
    print("请使用 sudo 运行！")
    sys.exit(1)

# 导入依赖
try:
    from flask import Flask, render_template_string, Response, jsonify, request
except ImportError:
    os.system("pip3 install flask -i https://pypi.tuna.tsinghua.edu.cn/simple")
    from flask import Flask, render_template_string, Response, jsonify, request

try:
    import cv2
except ImportError:
    os.system("pip3 install opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple")
    import cv2

try:
    import wiringpi
except ImportError:
    os.system("pip3 install wiringpi -i https://pypi.tuna.tsinghua.edu.cn/simple")
    import wiringpi

app = Flask(__name__)

# 全局变量
start_time = datetime.datetime.now()
operation_logs = []
current_temp = 0.0
current_hum = 0.0
camera = None
camera_ready = False
camera_lock = threading.Lock()
motor_queue = queue.Queue()
motor_thread = None
motor_running = True

IN1, IN2, IN3, IN4 = 3, 4, 6, 9
IN5, IN6, IN7, IN8 = 10, 13, 15, 16
pins = [IN1, IN2, IN3, IN4, IN5, IN6, IN7, IN8]

sequence = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1]
]


def log_record(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_str = f"[{now}] {msg}"
    print(log_str, flush=True)
    operation_logs.append(log_str)


def save_log():
    end_time = datetime.datetime.now()
    log_content = f"程序启动：{start_time}\n结束：{end_time}\n\n操作记录：\n"
    log_content += "\n".join(operation_logs)
    filename = f"run_log_{end_time.strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(log_content)
    log_record(f"日志已保存: {filename}")


def init_humiture():
    try:
        wiringpi.wiringPiSetup()
        BASE = 64
        wiringpi.htu21dSetup(BASE)
        log_record("温湿度传感器初始化成功")
        return BASE + 0, BASE + 1
    except Exception as e:
        log_record(f"温湿度初始化失败: {e}")
        return None, None


def read_humiture(A0, A1):
    global current_temp, current_hum
    try:
        temp_raw = wiringpi.analogRead(A0)
        hum_raw = wiringpi.analogRead(A1)
        current_temp = temp_raw / 10.0
        current_hum = hum_raw / 10.0
        log_record(f"温湿度: {current_temp:.1f}°C, {current_hum:.1f}%RH")
    except Exception as e:
        log_record(f"温湿度读取失败: {e}")


def motor_worker():
    global motor_running
    try:
        for pin in pins:
            wiringpi.pinMode(pin, 1)
            wiringpi.digitalWrite(pin, 0)
        log_record("电机引脚初始化完成")
    except Exception as e:
        log_record(f"电机初始化失败: {e}")
        return

    while motor_running:
        try:
            item = motor_queue.get(timeout=0.1)
            motor_pins, angle = item
            if angle != 0:
                seq = sequence if angle >= 0 else sequence[::-1]
                step_num = int(abs(angle) / 360.0 * 4096)
                for i in range(step_num):
                    step = seq[i % 8]
                    for pin, value in zip(motor_pins, step):
                        wiringpi.digitalWrite(pin, value)
                    time.sleep(0.001)
                for pin in motor_pins:
                    wiringpi.digitalWrite(pin, 0)
                log_record(f"电机旋转 {angle}°")
            motor_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            log_record(f"电机控制异常: {e}")


def start_motor_thread():
    global motor_thread
    motor_thread = threading.Thread(target=motor_worker, daemon=True)
    motor_thread.start()
    log_record("电机控制线程已启动")


def rotate_async(motor_pins, angle):
    motor_queue.put((motor_pins, angle))


def motor_stop_all():
    while not motor_queue.empty():
        try:
            motor_queue.get_nowait()
            motor_queue.task_done()
        except:
            pass
    for pin in pins:
        wiringpi.digitalWrite(pin, 0)
    log_record("所有电机停止")


# ====================== 摄像头修复版 ======================
def test_camera_backends(device_index):
    """测试所有可用的摄像头后端"""
    backends = [
        ("CAP_V4L2", cv2.CAP_V4L2),
        ("CAP_ANY", cv2.CAP_ANY),
        ("CAP_GSTREAMER", cv2.CAP_GSTREAMER),
        ("CAP_FFMPEG", cv2.CAP_FFMPEG),
    ]

    for name, backend in backends:
        try:
            log_record(f"  尝试后端 {name}...")
            cap = cv2.VideoCapture(device_index, backend)
            if cap.isOpened():
                # 测试读取
                time.sleep(0.3)
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    h, w = frame.shape[:2]
                    cap.release()
                    log_record(f"  后端 {name} 成功 ({w}x{h})")
                    return name, backend
                cap.release()
            else:
                cap.release()
        except Exception as e:
            log_record(f"  后端 {name} 失败: {e}")

    return None, None


def init_camera():
    """初始化摄像头 - 增强版"""
    global camera, camera_ready

    if camera is not None:
        try:
            camera.release()
        except:
            pass
        camera = None

    camera_ready = False

    # 检查设备文件
    video_devices = []
    for i in range(10):
        if os.path.exists(f"/dev/video{i}"):
            video_devices.append(i)

    if not video_devices:
        log_record("错误：未找到 /dev/video* 设备")
        return False

    log_record(f"发现视频设备: {video_devices}")

    # 测试每个设备
    for i in video_devices:
        log_record(f"测试 /dev/video{i}...")

        # 先测试所有后端
        backend_name, backend = test_camera_backends(i)

        if backend is None:
            log_record(f"  所有后端都失败，尝试默认方式...")
            # 最后尝试不带后端参数
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        backend_name = "default"
                        backend = None
                    else:
                        cap.release()
                        continue
                else:
                    cap.release()
                    continue
            except Exception as e:
                log_record(f"  默认方式也失败: {e}")
                continue

        # 使用成功的后端重新打开
        try:
            if backend is not None:
                camera = cv2.VideoCapture(i, backend)
            else:
                camera = cv2.VideoCapture(i)

            # 设置参数
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            # 验证
            time.sleep(0.5)
            for _ in range(5):
                ret, frame = camera.read()
                if ret and frame is not None and frame.size > 0:
                    h, w = frame.shape[:2]
                    camera_ready = True
                    log_record(f"摄像头就绪: /dev/video{i} 后端={backend_name} ({w}x{h})")
                    return True
                time.sleep(0.1)

            camera.release()
            camera = None

        except Exception as e:
            log_record(f"  最终初始化失败: {e}")
            if camera:
                try:
                    camera.release()
                except:
                    pass
                camera = None

    log_record("摄像头初始化失败")
    return False


def generate_frames():
    global camera, camera_ready
    fail_count = 0

    while True:
        with camera_lock:
            cap = camera
            ready = camera_ready

        if cap is None or not ready:
            time.sleep(0.5)
            continue

        try:
            ret, frame = cap.read()
            if not ret or frame is None:
                fail_count += 1
                if fail_count > 30:
                    log_record("摄像头读取失败过多，尝试重启...")
                    with camera_lock:
                        camera_ready = False
                    init_camera()
                    fail_count = 0
                time.sleep(0.1)
                continue

            fail_count = 0

            try:
                cv2.putText(frame, f"Temp: {current_temp:.1f}C", (10, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(frame, f"Hum: {current_hum:.1f}%RH", (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            except:
                pass

            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

            time.sleep(0.04)

        except Exception as e:
            log_record(f"视频流异常: {e}")
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
            font-family: Arial, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 15px;
            min-height: 100vh;
        }
        h1 { color: #58a6ff; margin-bottom: 15px; font-size: 22px; }
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
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .info-item {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 12px 24px;
        }
        .info-item .value { color: #3fb950; font-weight: bold; font-size: 18px; }
        .controls {
            display: grid;
            grid-template-columns: repeat(3, 90px);
            grid-template-rows: repeat(3, 90px);
            gap: 12px;
        }
        .btn {
            width: 90px; height: 90px;
            border: none; border-radius: 12px;
            background: #21262d; color: #c9d1d9;
            font-size: 32px; cursor: pointer;
            border: 1px solid #30363d;
        }
        .btn:hover { background: #30363d; }
        .btn:active { transform: scale(0.95); }
        .btn-up { grid-column: 2; grid-row: 1; background: #1f4d1f; }
        .btn-left { grid-column: 1; grid-row: 2; background: #1f4d1f; }
        .btn-center { grid-column: 2; grid-row: 2; background: #da3633; font-size: 14px; }
        .btn-right { grid-column: 3; grid-row: 2; background: #1f4d1f; }
        .btn-down { grid-column: 2; grid-row: 3; background: #1f4d1f; }
        .status { margin-top: 15px; padding: 10px 20px; border-radius: 8px; }
        .status.ok { background: #238636; }
        .status.err { background: #da3633; }
        .status.warn { background: #9e8c00; }

        @media (max-width: 480px) {
            .controls { grid-template-columns: repeat(3, 75px); grid-template-rows: repeat(3, 75px); }
            .btn { width: 75px; height: 75px; font-size: 26px; }
        }
    </style>
</head>
<body>
    <h1>智能摄像头控制终端</h1>

    <div class="video-box">
        <img src="{{ url_for('video_feed') }}" alt="摄像头画面"
             onerror="this.src='{{ url_for('video_feed') }}?' + Date.now()">
    </div>

    <div class="info-bar">
        <div class="info-item">温度：<span class="value" id="temp">--</span>℃</div>
        <div class="info-item">湿度：<span class="value" id="hum">--</span>%RH</div>
    </div>

    <div class="controls">
        <button class="btn btn-up" onclick="control('up')">▲</button>
        <button class="btn btn-left" onclick="control('left')">◀</button>
        <button class="btn btn-center" onclick="control('stop')">STOP</button>
        <button class="btn btn-right" onclick="control('right')">▶</button>
        <button class="btn btn-down" onclick="control('down')">▼</button>
    </div>

    <div id="status" class="status ok">系统就绪</div>

    <script>
        function updateData() {
            fetch('/api/data').then(r => r.json()).then(data => {
                document.getElementById('temp').textContent = data.temp.toFixed(1);
                document.getElementById('hum').textContent = data.hum.toFixed(1);
            });
        }
        setInterval(updateData, 2000);
        updateData();

        function control(direction) {
            const status = document.getElementById('status');
            status.className = 'status warn';
            status.textContent = '执行中...';

            fetch('/api/control', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({direction: direction})
            })
            .then(r => r.json())
            .then(data => {
                status.className = 'status ok';
                const names = {up:'俯仰上', down:'俯仰下', left:'左转', right:'右转', stop:'停止'};
                status.textContent = '已执行: ' + (names[direction] || direction);
            })
            .catch(() => {
                status.className = 'status err';
                status.textContent = '控制失败';
            });
        }
    </script>
</body>
</html>'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/video_feed')
def video_feed():
    global camera_ready
    if not camera_ready:
        return Response(b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x3b',
                        mimetype='image/gif')
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/data')
def api_data():
    global camera_ready
    return jsonify({
        'temp': current_temp,
        'hum': current_hum,
        'camera_ready': camera_ready
    })


@app.route('/api/control', methods=['POST'])
def api_control():
    try:
        data = request.get_json() or {}
    except:
        data = {}

    direction = data.get('direction', '')

    if direction == 'up':
        rotate_async([IN5, IN6, IN7, IN8], 15)
    elif direction == 'down':
        rotate_async([IN5, IN6, IN7, IN8], -15)
    elif direction == 'left':
        rotate_async([IN1, IN2, IN3, IN4], -15)
    elif direction == 'right':
        rotate_async([IN1, IN2, IN3, IN4], 15)
    elif direction == 'stop':
        motor_stop_all()

    return jsonify({'status': 'ok', 'direction': direction})


def humiture_loop(A0, A1):
    while True:
        if A0 is not None and A1 is not None:
            read_humiture(A0, A1)
        time.sleep(2)


def main():
    log_record("=" * 50)
    log_record("智能摄像头控制终端启动")
    log_record("=" * 50)

    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        log_record(f"本机IP: {ip}")
    except:
        ip = "未知"

    A0, A1 = init_humiture()
    start_motor_thread()
    init_camera()

    threading.Thread(target=humiture_loop, args=(A0, A1), daemon=True).start()

    def camera_watchdog():
        global camera_ready
        while True:
            time.sleep(5)
            if not camera_ready:
                log_record("尝试恢复摄像头...")
                init_camera()

    threading.Thread(target=camera_watchdog, daemon=True).start()

    log_record(f"请访问: http://{ip}:8081")

    try:
        app.run(host='0.0.0.0', port=8081, debug=False, threaded=True)
    except KeyboardInterrupt:
        pass
    finally:
        global motor_running
        motor_running = False
        motor_stop_all()
        if camera is not None:
            try:
                camera.release()
            except:
                pass
        save_log()
        print("程序已退出")


if __name__ == "__main__":
    main()
