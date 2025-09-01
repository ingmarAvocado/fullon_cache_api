"""
FastAPI router providing the ticker WebSocket endpoint.
"""

from fastapi import APIRouter, WebSocket

from ..handlers.ticker_handler import TickerWebSocketHandler

router = APIRouter()
ticker_handler = TickerWebSocketHandler()


@router.websocket("/ws/tickers/{connection_id}")
async def ticker_websocket_endpoint(websocket: WebSocket, connection_id: str) -> None:
    await ticker_handler.handle_connection(websocket, connection_id)
