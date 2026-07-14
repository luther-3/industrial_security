"""
MJPEG video stream endpoint: GET /stream/video
"""
import time
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from server.state import SharedState


def create_stream_router(state: SharedState) -> APIRouter:
    router = APIRouter()

    @router.get("/stream/video")
    async def video_stream():
        """MJPEG stream with YOLO annotations."""
        return StreamingResponse(
            _frame_generator(state),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )

    return router


def _frame_generator(state: SharedState):
    """Yield JPEG frames as MJPEG stream."""
    while True:
        jpeg = state.get_jpeg()
        if jpeg is not None:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpeg
                + b"\r\n"
            )
        else:
            # No frame yet, yield a tiny placeholder to keep connection alive
            yield b""

        # Match inference rate: ~8-15 fps = 66-125ms per frame
        time.sleep(0.08)
