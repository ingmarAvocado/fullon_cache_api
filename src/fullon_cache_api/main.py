"""
FastAPI application entry for fullon_cache_api (WebSocket-only).

Creates a FastAPI app and mounts the WebSocket gateway router at `/ws`.
No REST endpoints are exposed; use WebSocket for all interactions.
"""

from fastapi import FastAPI


def _safe_get_component_logger(name: str):
    try:
        from fullon_log import get_component_logger as _gcl  # type: ignore

        return _gcl(name)
    except Exception:  # pragma: no cover - environment dependent
        import logging

        class _KVLLoggerAdapter:
            def __init__(self, base):
                self._base = base

            def _fmt(self, msg: str, **kwargs):
                if kwargs:
                    kv = " ".join(f"{k}={v}" for k, v in kwargs.items())
                    return f"{msg} | {kv}"
                return msg

            def debug(self, msg, *args, **kwargs):
                self._base.debug(self._fmt(msg, **kwargs), *args)

            def info(self, msg, *args, **kwargs):
                self._base.info(self._fmt(msg, **kwargs), *args)

            def warning(self, msg, *args, **kwargs):
                self._base.warning(self._fmt(msg, **kwargs), *args)

            def error(self, msg, *args, **kwargs):
                self._base.error(self._fmt(msg, **kwargs), *args)

        return _KVLLoggerAdapter(logging.getLogger(name))


from .routers.accounts import router as accounts_router
from .routers.tickers import router as tickers_router
from .routers.websocket import router as ws_router

logger = _safe_get_component_logger("fullon.api.cache.app")


def create_app() -> FastAPI:
    app = FastAPI(title="fullon_cache_api", docs_url=None, redoc_url=None)
    app.include_router(ws_router)
    app.include_router(tickers_router)
    app.include_router(accounts_router)
    logger.info("FastAPI WebSocket app created")
    return app


# Uvicorn entrypoint
app = create_app()
