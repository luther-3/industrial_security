"""
WebSocket stats push: WS /ws/stats
Push at STATS_PUSH_INTERVAL (~5-10 Hz), not per-frame.
"""
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from server.state import SharedState
from engine.config import STATS_PUSH_INTERVAL


def create_ws_router(state: SharedState) -> APIRouter:
    router = APIRouter()

    @router.websocket("/ws/stats")
    async def stats_websocket(ws: WebSocket):
        await ws.accept()
        try:
            while True:
                stats = state.get_stats()
                await ws.send_json({"type": "stats", "data": stats})
                await asyncio.sleep(STATS_PUSH_INTERVAL)
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    return router
