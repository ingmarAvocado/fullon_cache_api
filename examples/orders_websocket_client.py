"""Minimal example client for Orders WebSocket API.

Usage:
    poetry run python examples/orders_websocket_client.py
"""

import asyncio
import json

import websockets


async def main() -> None:
    uri = "ws://127.0.0.1:8000/ws/orders/example"
    async with websockets.connect(uri) as ws:
        # Query queue length (binance)
        await ws.send(
            json.dumps(
                {
                    "action": "get_queue_length",
                    "request_id": "ql1",
                    "params": {"exchange": "binance"},
                }
            )
        )
        print("queue length:", await ws.recv())

        # Start stream
        await ws.send(
            json.dumps(
                {
                    "action": "stream_order_queue",
                    "request_id": "s1",
                    "params": {"exchange": "binance"},
                }
            )
        )
        # Print a few updates
        for _ in range(3):
            print("update:", await ws.recv())


if __name__ == "__main__":
    asyncio.run(main())

