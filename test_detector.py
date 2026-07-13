"""
测试脚本：安全装备检测器 + 静态图片验证

用法:
    # 使用 ultralytics 内置测试图片（bus.jpg）
    python test_detector.py

    # 使用自定义图片
    python test_detector.py path/to/image.jpg

在窗口中显示带标注框的检测结果。按任意键退出。
"""
import sys
import os

import cv2

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.detector import SafetyGearDetector
from engine.draw import annotate_frame


def main():
    # 1. 确定测试图片
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # 使用 ultralytics 内置测试图片
        import ultralytics
        pkg_dir = os.path.dirname(ultralytics.__file__)
        image_path = os.path.join(pkg_dir, "assets", "bus.jpg")

    if not os.path.exists(image_path):
        print(f"[ERROR] 图片不存在: {image_path}")
        sys.exit(1)

    print(f"[TEST] 测试图片: {image_path}")

    # 2. 加载检测器
    detector = SafetyGearDetector()
    print(f"[TEST] 模型已加载: {detector.model_path}")

    # 3. 读图 + 推理
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"[ERROR] 无法读取图片: {image_path}")
        sys.exit(1)

    print(f"[TEST] 图片尺寸: {frame.shape[1]}x{frame.shape[0]}")
    print("[TEST] 正在推理...")

    detections = detector.detect(frame)
    stats = detector.compute_stats(detections)

    # 4. 打印结果
    print(f"\n{'='*50}")
    print(f"  检测结果")
    print(f"{'='*50}")
    print(f"  总检测框数: {stats['total_persons']}")
    print(f"  未戴安全帽: {stats['no_helmet']}")
    print(f"  未穿反光衣: {stats['no_vest']}")
    print(f"{'='*50}")

    if detections:
        print(f"\n  详情:")
        for i, det in enumerate(detections, 1):
            x1, y1, x2, y2 = det.bbox
            print(
                f"  [{i}] {det.class_name:<30s} "
                f"conf={det.confidence:.2f}  "
                f"bbox=({x1},{y1},{x2},{y2})  "
                f"label={det.label}"
            )
    else:
        print("\n  未检测到任何目标（可能是图片中无人或模型不匹配）")

    # 5. 绘制标注并显示
    annotated = annotate_frame(frame, detections, stats)

    window_name = "Detection Test — press any key to close"
    cv2.imshow(window_name, annotated)
    print(f"\n[TEST] 显示标注结果，按任意键关闭窗口...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print("[TEST] 测试完成。")


if __name__ == "__main__":
    main()
