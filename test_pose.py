"""
测试脚本：人体姿态估计 + 摔倒检测（视频）

用法:
    # 使用视频文件验证
    python test_pose.py path/to/fall_test.mp4

    # 使用摄像头实时测试
    python test_pose.py

按 Q 退出，空格键暂停/播放。
"""
import sys
import os
from datetime import datetime

import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.pose_estimator import PoseEstimator, FallStateManager
from engine.draw import annotate_frame


def main():
    # 1. 确定视频源
    if len(sys.argv) > 1:
        source = sys.argv[1]
        print(f"[TEST] 视频文件: {source}")
    else:
        source = 0  # 摄像头
        print("[TEST] 使用摄像头（默认设备）")

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[ERROR] 无法打开视频源: {source}")
        sys.exit(1)

    # 2. 加载姿态估计模型
    estimator = PoseEstimator()
    print(f"[TEST] 姿态模型已加载: {estimator.model_path}")

    # 3. 摔倒状态机
    fall_manager = FallStateManager()

    # 4. 视频信息
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[TEST] 分辨率: {frame_w}x{frame_h}, FPS: {fps:.1f}, 总帧数: {total_frames}")
    print(f"[TEST] 摔倒触发阈值: {3} 帧 | 解除阈值: {5} 帧")
    print(f"[TEST] 按 Q 退出 | 空格 暂停/播放")
    print()

    paused = False
    frame_idx = 0

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                print("[TEST] 视频结束或无法读取。")
                break
            frame_idx += 1

        # 姿态估计
        poses = estimator.estimate(frame)

        # 摔倒状态机：检测画面中是否至少有一人摔倒
        any_fall_single = any(p.is_fallen for p in poses)
        fall_confirmed = fall_manager.update(any_fall_single)

        # 统计
        stats = {
            "total_persons": 0,       # 姿态模型只在有人时输出
            "no_helmet": 0,           # pose 模型不检测装备
            "no_vest": 0,
            "fall": fall_confirmed,
        }
        if poses:
            stats["total_persons"] = len(poses)

        # 绘制
        annotated = annotate_frame(frame, detections=[], poses=poses, stats=stats)

        # 如果摔倒状态机已触发，在帧上用红色覆盖标记
        if fall_confirmed:
            _draw_fall_overlay(annotated)

        # 显示帧号 / 时间戳
        ts = datetime.now().strftime("%H:%M:%S")
        cv2.putText(
            annotated, f"Frame: {frame_idx} | {ts}",
            (10, frame_h - 12),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1,
        )

        cv2.imshow("Pose + Fall Detection Test", annotated)

        key = cv2.waitKey(max(1, int(1000 / max(fps, 10)))) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused
            print(f"[TEST] {'暂停' if paused else '播放'}")

    cap.release()
    cv2.destroyAllWindows()
    print("[TEST] 测试完成。")


def _draw_fall_overlay(img):
    """在画面中心叠加红色摔倒警告"""
    h, w = img.shape[:2]

    # 半透明红色遮罩
    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 200), -1)
    cv2.addWeighted(overlay, 0.08, img, 0.92, 0, img)

    # 大字警告
    text = "WARNING: FALL DETECTED"
    font_scale = min(w, h) / 500
    (tw, th), baseline = cv2.getTextSize(
        text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2
    )
    tx = (w - tw) // 2
    ty = (h + th) // 2

    # 文字阴影
    cv2.putText(img, text, (tx + 2, ty + 2),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 3)
    # 文字主体
    cv2.putText(img, text, (tx, ty),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), 2)


if __name__ == "__main__":
    main()
