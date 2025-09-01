#!/usr/bin/env python3
"""
Orders Cache WebSocket Operations Example

PROTOTYPE - Shows desired WebSocket API pattern.
Will be updated to use real WebSocket server like fullon_cache examples.

Usage:
    python example_orders_cache.py --operations basic --orders 50
    python example_orders_cache.py --operations queue --batch-size 10 --verbose
"""

import argparse
import asyncio
import random
import sys
import time
from collections.abc import AsyncIterator
from typing import Any, Optional


class MockOrdersWebSocketAPI:
    """MOCK - will be replaced with real WebSocket client."""

    def __init__(self, ws_url: str = "ws://localhost:8000"):
        self.ws_url = ws_url

    async def __aenter__(self):
        print("🔌 Orders WebSocket connected (MOCK)")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("🔌 Orders WebSocket disconnected (MOCK)")

    # READ-ONLY Order Operations
    async def get_order_status(self, order_id: str) -> Optional[str]:
        await asyncio.sleep(0.02)
        return random.choice(["pending", "filled", "cancelled", "rejected", "partial"])

    async def get_queue_length(self, exchange: str) -> int:
        await asyncio.sleep(0.02)
        return random.randint(10, 100)

    async def get_order_data(
        self, exchange: str, ex_order_id: str
    ) -> Optional[dict[str, Any]]:
        await asyncio.sleep(0.02)
        return {
            "id": random.randint(5000, 6000),
            "ex_order_id": ex_order_id,
            "symbol": random.choice(["BTC/USDT", "ETH/USDT"]),
            "side": random.choice(["buy", "sell"]),
            "amount": round(random.uniform(0.1, 2.0), 8),
            "price": round(random.uniform(20000, 50000), 2),
            "status": "filled",
            "timestamp": time.time(),
        }

    # Streaming Operations
    async def stream_order_queue(self, exchange: str) -> AsyncIterator[dict[str, Any]]:
        print(f"📡 Streaming order queue for {exchange} (MOCK)")
        for i in range(8):
            await asyncio.sleep(1.0)
            yield {
                "exchange": exchange,
                "queue_size": random.randint(20, 80),
                "processing_rate": round(random.uniform(5.0, 15.0), 2),
                "update_id": i,
            }


def fullon_cache_api(ws_url: str = "ws://localhost:8000") -> MockOrdersWebSocketAPI:
    return MockOrdersWebSocketAPI(ws_url)


async def basic_queue_operations(order_count: int = 50, verbose: bool = False) -> bool:
    print("📋 === Basic Order Queue WebSocket Operations (MOCK) ===")

    try:
        async with fullon_cache_api() as handler:
            print(f"🔄 Testing {order_count} order operations...")

            # Test order status checks
            for i in range(min(order_count, 10)):
                order_id = f"order_{i:04d}"
                status = await handler.get_order_status(order_id)
                if verbose:
                    print(f"   📊 {order_id}: {status}")

            # Test queue lengths
            exchanges = ["binance", "kraken", "coinbase"]
            total_queue_size = 0

            for exchange in exchanges:
                queue_size = await handler.get_queue_length(exchange)
                total_queue_size += queue_size
                if verbose:
                    print(f"   📊 {exchange} queue: {queue_size} orders")

            print(
                f"✅ Order operations completed: {total_queue_size} total queued orders"
            )
            return True

    except Exception as e:
        print(f"❌ Basic queue operations failed: {e}")
        return False


async def streaming_demo(verbose: bool = False) -> bool:
    print("📡 === Order Queue Streaming Demo (MOCK) ===")

    try:
        async with fullon_cache_api() as handler:
            update_count = 0
            async for update in handler.stream_order_queue("binance"):
                update_count += 1
                if verbose:
                    print(
                        f"   📊 Queue: {update['queue_size']} orders "
                        f"(rate: {update['processing_rate']}/s)"
                    )

                if update.get("update_id", 0) >= 4:
                    break

            print(f"✅ Streaming completed: {update_count} updates")
            return True

    except Exception as e:
        print(f"❌ Order streaming failed: {e}")
        return False


async def run_demo(args) -> bool:
    print("🚀 fullon_cache_api Orders WebSocket Demo (MOCK)")
    print("===============================================")
    print("🔧 Will be updated to use real WebSocket server")

    results = {}

    if args.operations in ["basic", "all"]:
        results["basic"] = await basic_queue_operations(args.orders, args.verbose)

    if args.operations in ["streaming", "all"]:
        results["streaming"] = await streaming_demo(args.verbose)

    success_count = sum(results.values())
    total_count = len(results)

    print(f"\n📊 Success: {success_count}/{total_count} operations")
    return success_count == total_count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--operations", choices=["basic", "streaming", "all"], default="all"
    )
    parser.add_argument("--orders", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    try:
        success = asyncio.run(run_demo(args))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🔄 Demo interrupted")
        sys.exit(1)


if __name__ == "__main__":
    main()
