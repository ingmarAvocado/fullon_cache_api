#!/usr/bin/env python3
"""
OHLCV Cache WebSocket Operations Example

PROTOTYPE - Shows desired WebSocket API pattern.
Will be updated to use real WebSocket server like fullon_cache examples.

Usage:
    python example_ohlcv_cache.py --operations basic --symbols BTC/USDT,ETH/USDT
    python example_ohlcv_cache.py --operations streaming --timeframes 1m,5m --verbose
"""

import argparse
import asyncio
import random
import sys
import time
from collections.abc import AsyncIterator
from typing import Any


class MockOHLCVWebSocketAPI:
    """MOCK - will be replaced with real WebSocket client."""

    def __init__(self, ws_url: str = "ws://localhost:8000"):
        self.ws_url = ws_url

    async def __aenter__(self):
        print("🔌 OHLCV WebSocket connected (MOCK)")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("🔌 OHLCV WebSocket disconnected (MOCK)")

    # READ-ONLY OHLCV Operations
    async def get_latest_ohlcv_bars(
        self, symbol: str, timeframe: str, count: int
    ) -> list[list[float]]:
        await asyncio.sleep(0.02)

        # Mock OHLCV bars: [timestamp, open, high, low, close, volume]
        bars = []
        base_price = 47000.0 if "BTC" in symbol else 3100.0
        base_time = int(time.time()) - (count * 60)  # 1 minute bars

        current_price = base_price
        for i in range(count):
            timestamp = base_time + (i * 60)
            open_price = current_price
            high_price = open_price * (1 + random.uniform(0, 0.02))
            low_price = open_price * (1 - random.uniform(0, 0.02))
            close_price = open_price * (1 + random.uniform(-0.015, 0.015))
            volume = random.uniform(100, 1000)

            bars.append(
                [timestamp, open_price, high_price, low_price, close_price, volume]
            )
            current_price = close_price

        return bars

    # Streaming Operations
    async def stream_ohlcv_updates(
        self, symbol: str, timeframe: str
    ) -> AsyncIterator[dict[str, Any]]:
        print(f"📡 Streaming OHLCV updates for {symbol} {timeframe} (MOCK)")

        base_price = 47000.0 if "BTC" in symbol else 3100.0
        current_price = base_price

        for i in range(12):
            await asyncio.sleep(2.0)  # OHLCV updates every 2 seconds

            # Mock new bar
            timestamp = int(time.time())
            open_price = current_price
            high_price = open_price * (1 + random.uniform(0, 0.01))
            low_price = open_price * (1 - random.uniform(0, 0.01))
            close_price = open_price * (1 + random.uniform(-0.008, 0.008))
            volume = random.uniform(200, 800)

            yield {
                "type": "ohlcv_update",
                "symbol": symbol,
                "timeframe": timeframe,
                "bar": [
                    timestamp,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume,
                ],
                "update_id": i,
            }

            current_price = close_price


def fullon_cache_api(ws_url: str = "ws://localhost:8000") -> MockOHLCVWebSocketAPI:
    return MockOHLCVWebSocketAPI(ws_url)


async def basic_ohlcv_operations(symbols: list[str], verbose: bool = False) -> bool:
    print("🕯️ === Basic OHLCV WebSocket Operations (MOCK) ===")

    try:
        async with fullon_cache_api() as handler:
            timeframes = ["1m", "5m", "1h"]
            total_bars = 0

            for symbol in symbols:
                for timeframe in timeframes:
                    bars = await handler.get_latest_ohlcv_bars(
                        symbol, timeframe, count=50
                    )
                    total_bars += len(bars)

                    if verbose and bars:
                        latest_bar = bars[-1]
                        print(
                            f"   🕯️ {symbol} {timeframe}: {len(bars)} bars, "
                            f"latest close: ${latest_bar[4]:.2f}"
                        )

            print(f"✅ Retrieved {total_bars} total OHLCV bars")
            return True

    except Exception as e:
        print(f"❌ Basic OHLCV operations failed: {e}")
        return False


async def streaming_demo(
    symbols: list[str], timeframes: list[str], verbose: bool = False
) -> bool:
    print("📡 === OHLCV Streaming Demo (MOCK) ===")

    try:
        async with fullon_cache_api() as handler:

            async def stream_symbol_timeframe(symbol: str, timeframe: str):
                update_count = 0
                async for update in handler.stream_ohlcv_updates(symbol, timeframe):
                    update_count += 1

                    if verbose:
                        bar = update["bar"]
                        print(
                            f"   🕯️ {symbol} {timeframe}: "
                            f"O:{bar[1]:.2f} H:{bar[2]:.2f} L:{bar[3]:.2f} C:{bar[4]:.2f}"
                        )

                    if update.get("update_id", 0) >= 3:  # Limit updates
                        break

                return update_count

            # Stream multiple symbol/timeframe combinations
            tasks = []
            for symbol in symbols[:2]:  # Limit to 2 symbols
                for timeframe in timeframes[:2]:  # Limit to 2 timeframes
                    task = stream_symbol_timeframe(symbol, timeframe)
                    tasks.append(task)

            if not tasks:  # Fallback
                tasks.append(stream_symbol_timeframe("BTC/USDT", "1m"))

            results = await asyncio.gather(*tasks)
            total_updates = sum(results)

            print(f"✅ OHLCV streaming completed: {total_updates} total updates")
            return True

    except Exception as e:
        print(f"❌ OHLCV streaming failed: {e}")
        return False


async def run_demo(args) -> bool:
    print("🚀 fullon_cache_api OHLCV WebSocket Demo (MOCK)")
    print("==============================================")
    print("🔧 Will be updated to use real WebSocket server")

    # Parse arguments
    symbols = (
        [s.strip() for s in args.symbols.split(",")]
        if args.symbols
        else ["BTC/USDT", "ETH/USDT"]
    )
    timeframes = (
        [t.strip() for t in args.timeframes.split(",")]
        if args.timeframes
        else ["1m", "5m"]
    )

    results = {}

    if args.operations in ["basic", "all"]:
        results["basic"] = await basic_ohlcv_operations(symbols, args.verbose)

    if args.operations in ["streaming", "all"]:
        results["streaming"] = await streaming_demo(symbols, timeframes, args.verbose)

    success_count = sum(results.values())
    total_count = len(results)

    print(f"\n📊 Success: {success_count}/{total_count} operations")
    return success_count == total_count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--operations", choices=["basic", "streaming", "all"], default="all"
    )
    parser.add_argument(
        "--symbols", default="BTC/USDT,ETH/USDT", help="Comma-separated symbols"
    )
    parser.add_argument(
        "--timeframes", default="1m,5m", help="Comma-separated timeframes"
    )
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
