"""
FastAPI application factory.
"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from server.state import SharedState
from server.stream import create_stream_router
from server.ws import create_ws_router


def create_app(state: SharedState) -> FastAPI:
    app = FastAPI(title="Industrial Security Monitor")

    # API routes (must be before static mount so they take priority)
    app.include_router(create_stream_router(state))
    app.include_router(create_ws_router(state))

    @app.get("/api/health")
    async def health():
        stats = state.get_stats()
        return {
            "status": "ok",
            "camera_connected": stats["camera_status"] == "connected",
            "fps": stats["fps"],
        }

    # Serve built frontend if available
    dist_dir = os.path.join(os.path.dirname(__file__), "..", "web", "dist")
    if os.path.isdir(dist_dir):
        app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")
        print(f"[APP] Serving frontend from {dist_dir}")

    return app
