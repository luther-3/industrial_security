"""
FastAPI application factory.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from server.state import SharedState
from server.stream import create_stream_router
from server.ws import create_ws_router


def create_app(state: SharedState) -> FastAPI:
    app = FastAPI(title="Industrial Security Monitor")

    # API routes
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

    return app
