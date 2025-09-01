"""
FastAPI router providing the orders WebSocket endpoint.
"""

from fastapi import APIRouter, WebSocket

from ..handlers.order_handler import OrdersWebSocketHandler

router = APIRouter()
orders_handler = OrdersWebSocketHandler()


@router.websocket("/ws/orders/{connection_id}")
async def orders_websocket_endpoint(websocket: WebSocket, connection_id: str) -> None:
    await orders_handler.handle_connection(websocket, connection_id)

