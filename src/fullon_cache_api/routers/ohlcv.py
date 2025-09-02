"""
FastAPI router providing the OHLCV WebSocket endpoint.
"""

from fastapi import APIRouter, WebSocket

from ..handlers.ohlcv_handler import OHLCVWebSocketHandler

router = APIRouter()
ohlcv_handler = OHLCVWebSocketHandler()


@router.websocket("/ws/ohlcv/{connection_id}")
async def ohlcv_websocket_endpoint(websocket: WebSocket, connection_id: str) -> None:
    await ohlcv_handler.handle_connection(websocket, connection_id)
