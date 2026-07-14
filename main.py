"""
Entry point: Industrial Security Monitoring System.

Usage:
    python main.py                  # Use camera (MJPEG URL from config)
    python main.py video.mp4        # Use video file for testing
    python main.py 0                # Use local webcam
"""
import sys
import threading
import uvicorn

from server.state import SharedState
from server.app import create_app
from engine.pipeline import Pipeline
from engine.config import HOST, PORT


def main():
    # Parse source argument
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        try:
            source = int(arg)  # webcam index
        except ValueError:
            source = arg       # video file path
    else:
        source = "camera"      # MJPEG camera URL

    print("=" * 55)
    print("  Industrial Security Monitoring System")
    print("=" * 55)
    print(f"  Video source: {source}")
    print(f"  Web: http://localhost:{PORT}")
    print(f"  Stream: http://localhost:{PORT}/stream/video")
    print(f"  Stats: ws://localhost:{PORT}/ws/stats")
    print(f"  Health: http://localhost:{PORT}/api/health")
    print("=" * 55)

    # Shared state between inference and web threads
    state = SharedState()

    # Pipeline (runs on background thread)
    pipeline = Pipeline(state, source=source)

    # Start inference thread
    inference_thread = threading.Thread(
        target=pipeline.run,
        daemon=True,
        name="InferenceThread",
    )

    try:
        pipeline.setup()
        inference_thread.start()

        # FastAPI on main thread
        app = create_app(state)
        uvicorn.run(app, host=HOST, port=PORT, log_level="info")

    except KeyboardInterrupt:
        print("\n[MAIN] Shutting down...")
        pipeline.stop()
    finally:
        pipeline.stop()
        print("[MAIN] Stopped.")


if __name__ == "__main__":
    main()
