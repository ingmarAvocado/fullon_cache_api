"""
FastAPI application entry for fullon_cache_api (WebSocket-only).

Creates a FastAPI app and mounts the WebSocket gateway router at `/ws`.
No REST endpoints are exposed; use WebSocket for all interactions.
"""

from fastapi import FastAPI


from fullon_log import get_component_logger  # type: ignore


from .routers.accounts import router as accounts_router
from .routers.orders import router as orders_router
from .routers.tickers import router as tickers_router
from .routers.websocket import router as ws_router

logger = get_component_logger("fullon.api.cache.app")


def create_app() -> FastAPI:
    app = FastAPI(title="fullon_cache_api", docs_url=None, redoc_url=None)
    app.include_router(ws_router)
    app.include_router(tickers_router)
    app.include_router(orders_router)
    app.include_router(accounts_router)
    logger.info("FastAPI WebSocket app created")
    return app


# Uvicorn entrypoint
app = create_app()
