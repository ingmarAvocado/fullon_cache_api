#!/usr/bin/env python3
"""
Bot Cache WebSocket Operations Example

This mirrors fullon_cache example_bot_cache.py but uses WebSocket API calls
instead of direct cache operations. Shows the desired WebSocket pattern for
bot coordination and blocking operations.

PROTOTYPE - Shows desired API, actual WebSocket implementation comes later.

Usage:
    python example_bot_cache.py --bots 3 --symbols BTC/USDT,ETH/USDT --duration 30
    python example_bot_cache.py --bots 5 --duration 60 --verbose
    python example_bot_cache.py --operations status --verbose
"""

import argparse
import asyncio
import random
import sys
import time
from collections.abc import AsyncIterator
from typing import Any, Optional


class MockBotWebSocketAPI:
    """Mock WebSocket API for bot operations (shows desired pattern)."""

    def __init__(self, ws_url: str = "ws://localhost:8000"):
        self.ws_url = ws_url

    async def __aenter__(self):
        print("🔌 Bot WebSocket connected")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("🔌 Bot WebSocket disconnected")

    # READ-ONLY Bot Operations (mirroring BotCache)
    async def is_blocked(self, exchange: str, symbol: str) -> Optional[str]:
        """Check if exchange/symbol is blocked (mirrors BotCache.is_blocked)."""
        await asyncio.sleep(0.02)  # Simulate WebSocket latency

        # Mock blocking status - 30% chance of being blocked
        if random.random() < 0.3:
            return str(random.randint(1001, 1005))  # Return blocking bot ID
        return None  # Not blocked

    async def get_bots(self) -> dict[str, dict[str, Any]]:
        """Get all bots data (mirrors BotCache.get_bots)."""
        await asyncio.sleep(0.02)

        # Mock bot data
        bot_count = random.randint(3, 8)
        bots = {}

        for i in range(bot_count):
            bot_id = str(1000 + i)
            bots[bot_id] = {
                "status": random.choice(
                    ["running", "paused", "stopped", "maintenance"]
                ),
                "name": f"Bot_{bot_id}",
                "strategy": random.choice(["scalping", "grid", "dca", "arbitrage"]),
                "exchange": random.choice(["binance", "kraken", "coinbase"]),
                "active_pairs": random.randint(1, 5),
                "uptime": random.uniform(100, 86400),  # Seconds
                "last_activity": time.time() - random.uniform(0, 3600),
            }

        return bots

    async def is_opening_position(self, exchange: str, symbol: str) -> bool:
        """Check if bot is opening position (mirrors BotCache.is_opening_position)."""
        await asyncio.sleep(0.02)

        # Mock opening status - 20% chance
        return random.random() < 0.2

    async def get_blocks(self) -> list[dict[str, str]]:
        """Get all current blocks (mirrors BotCache.get_blocks)."""
        await asyncio.sleep(0.02)

        # Mock block list
        symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT", "DOT/USDT"]
        exchanges = ["binance", "kraken", "coinbase"]
        blocks = []

        # Random number of blocks
        for _ in range(random.randint(0, 4)):
            blocks.append(
                {
                    "exchange": random.choice(exchanges),
                    "symbol": random.choice(symbols),
                    "bot_id": str(random.randint(1001, 1005)),
                    "blocked_since": str(int(time.time() - random.uniform(60, 3600))),
                }
            )

        return blocks

    # Streaming Operations (async iterators)
    async def stream_bot_status(self) -> AsyncIterator[dict[str, Any]]:
        """Stream live bot status updates via WebSocket."""
        print("📡 Streaming bot status updates")

        for i in range(12):  # Mock 12 updates
            await asyncio.sleep(2.0)  # Bot status changes slower

            # Mock bot status change
            bot_id = str(random.randint(1001, 1005))
            old_status = random.choice(["running", "paused", "stopped"])
            new_status = random.choice(["running", "paused", "stopped", "maintenance"])

            yield {
                "type": "bot_status_change",
                "bot_id": bot_id,
                "old_status": old_status,
                "new_status": new_status,
                "timestamp": time.time(),
                "update_id": i,
            }

    async def stream_blocking_events(self) -> AsyncIterator[dict[str, Any]]:
        """Stream live blocking/unblocking events via WebSocket."""
        print("📡 Streaming blocking events")

        for i in range(8):  # Mock 8 events
            await asyncio.sleep(3.0)  # Blocking events are less frequent

            # Mock blocking event
            action = random.choice(["blocked", "unblocked"])
            exchange = random.choice(["binance", "kraken", "coinbase"])
            symbol = random.choice(["BTC/USDT", "ETH/USDT", "ADA/USDT"])
            bot_id = str(random.randint(1001, 1005))

            yield {
                "type": "blocking_event",
                "action": action,
                "exchange": exchange,
                "symbol": symbol,
                "bot_id": bot_id if action == "blocked" else None,
                "timestamp": time.time(),
                "update_id": i,
            }

    async def stream_coordination_activity(self) -> AsyncIterator[dict[str, Any]]:
        """Stream bot coordination activity."""
        print("📡 Streaming coordination activity")

        for i in range(15):  # Mock coordination events
            await asyncio.sleep(1.5)

            # Mock coordination event
            event_type = random.choice(
                [
                    "position_opening",
                    "position_closing",
                    "conflict_resolved",
                    "priority_assigned",
                ]
            )

            yield {
                "type": "coordination_event",
                "event_type": event_type,
                "bot_id": str(random.randint(1001, 1005)),
                "exchange": random.choice(["binance", "kraken"]),
                "symbol": random.choice(["BTC/USDT", "ETH/USDT"]),
                "priority": random.randint(1, 10),
                "timestamp": time.time(),
                "update_id": i,
            }


def fullon_cache_api(ws_url: str = "ws://localhost:8000") -> MockBotWebSocketAPI:
    """Create bot WebSocket API client."""
    return MockBotWebSocketAPI(ws_url)


async def test_websocket_connection() -> bool:
    """Test WebSocket connection."""
    try:
        async with fullon_cache_api() as handler:
            print("✅ WebSocket connection successful")
            return True
    except Exception as e:
        print("❌ WebSocket connection failed")
        print(f"   Error: {e}")
        return False


async def basic_blocking_demo(verbose: bool = False) -> bool:
    """Demonstrate basic exchange blocking operations."""
    print("🔒 === Basic Exchange Blocking WebSocket Demo ===")

    try:
        async with fullon_cache_api() as handler:
            exchanges = ["binance", "kraken", "coinbase"]
            symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]

            print("🔄 Testing blocking status checks...")
            blocked_count = 0

            for exchange in exchanges:
                for symbol in symbols:
                    # Check if blocked via WebSocket
                    blocking_bot = await handler.is_blocked(exchange, symbol)

                    if blocking_bot:
                        blocked_count += 1
                        if verbose:
                            print(
                                f"   🔒 {exchange}:{symbol} blocked by bot {blocking_bot}"
                            )
                    elif verbose:
                        print(f"   ✅ {exchange}:{symbol} available")

            # Get all blocks
            all_blocks = await handler.get_blocks()

            print(
                f"✅ Blocking check completed: {blocked_count} blocked pairs, "
                f"{len(all_blocks)} total blocks in system"
            )

            if verbose and all_blocks:
                print("   📋 Current blocks:")
                for block in all_blocks:
                    print(
                        f"      🔒 {block['exchange']}:{block['symbol']} → "
                        f"Bot {block['bot_id']}"
                    )

            return True

    except Exception as e:
        print(f"❌ Basic blocking demo failed: {e}")
        return False


async def bot_status_demo(verbose: bool = False) -> bool:
    """Demonstrate bot status tracking."""
    print("📊 === Bot Status WebSocket Demo ===")

    try:
        async with fullon_cache_api() as handler:
            # Get all bots via WebSocket
            bots = await handler.get_bots()

            print(f"🔄 Retrieved {len(bots)} bots from cache")

            # Analyze bot statuses
            status_counts = {}
            strategy_counts = {}

            for bot_id, bot_data in bots.items():
                status = bot_data["status"]
                strategy = bot_data["strategy"]

                status_counts[status] = status_counts.get(status, 0) + 1
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

                if verbose:
                    uptime_hours = bot_data["uptime"] / 3600
                    last_active = time.time() - bot_data["last_activity"]

                    status_emoji = {
                        "running": "🟢",
                        "paused": "🟡",
                        "stopped": "🔴",
                        "maintenance": "🟠",
                    }.get(status, "⚪")

                    print(
                        f"   {status_emoji} Bot {bot_id}: {bot_data['name']} "
                        f"({status}) - {bot_data['strategy']} strategy"
                    )
                    print(
                        f"      Exchange: {bot_data['exchange']}, "
                        f"Pairs: {bot_data['active_pairs']}, "
                        f"Uptime: {uptime_hours:.1f}h, "
                        f"Last active: {last_active:.0f}s ago"
                    )

            print("📈 Bot Status Distribution:")
            for status, count in status_counts.items():
                print(f"   📊 {status}: {count} bots")

            print("🎯 Strategy Distribution:")
            for strategy, count in strategy_counts.items():
                print(f"   📊 {strategy}: {count} bots")

            return True

    except Exception as e:
        print(f"❌ Bot status demo failed: {e}")
        return False


async def position_opening_demo(verbose: bool = False) -> bool:
    """Demonstrate position opening state management."""
    print("📈 === Position Opening State WebSocket Demo ===")

    try:
        async with fullon_cache_api() as handler:
            exchanges = ["binance", "kraken"]
            symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]

            print("🔄 Checking position opening states...")
            opening_count = 0

            for exchange in exchanges:
                for symbol in symbols:
                    # Check if opening position via WebSocket
                    is_opening = await handler.is_opening_position(exchange, symbol)

                    if is_opening:
                        opening_count += 1
                        if verbose:
                            print(f"   📈 {exchange}:{symbol} - position being opened")
                    elif verbose:
                        print(f"   ➖ {exchange}:{symbol} - no position opening")

            print(
                f"✅ Position opening check completed: "
                f"{opening_count} pairs with positions being opened"
            )

            return True

    except Exception as e:
        print(f"❌ Position opening demo failed: {e}")
        return False


async def streaming_coordination_demo(
    duration: int = 15, verbose: bool = False
) -> bool:
    """Demonstrate real-time bot coordination streaming."""
    print("📡 === Bot Coordination Streaming Demo ===")

    try:
        async with fullon_cache_api() as handler:
            print(f"🔄 Starting coordination streams for {duration}s...")

            async def status_monitor():
                update_count = 0
                async for update in handler.stream_bot_status():
                    update_count += 1

                    status_emoji = {
                        "running": "🟢",
                        "paused": "🟡",
                        "stopped": "🔴",
                        "maintenance": "🟠",
                    }
                    old_emoji = status_emoji.get(update["old_status"], "⚪")
                    new_emoji = status_emoji.get(update["new_status"], "⚪")

                    if verbose:
                        print(
                            f"   🤖 Bot {update['bot_id']}: "
                            f"{old_emoji} → {new_emoji} "
                            f"({update['old_status']} → {update['new_status']})"
                        )
                    elif update_count % 3 == 0:
                        print(f"   📊 Status updates: {update_count}")

                    if update.get("update_id", 0) >= 5:  # Limit updates
                        break

                return update_count

            async def blocking_monitor():
                event_count = 0
                async for event in handler.stream_blocking_events():
                    event_count += 1

                    action_emoji = {"blocked": "🔒", "unblocked": "🔓"}
                    emoji = action_emoji.get(event["action"], "⚪")

                    if verbose:
                        bot_info = (
                            f" by bot {event['bot_id']}" if event["bot_id"] else ""
                        )
                        print(
                            f"   {emoji} {event['exchange']}:{event['symbol']} "
                            f"{event['action']}{bot_info}"
                        )
                    elif event_count % 2 == 0:
                        print(f"   📊 Blocking events: {event_count}")

                    if event.get("update_id", 0) >= 3:  # Limit events
                        break

                return event_count

            async def coordination_monitor():
                coord_count = 0
                async for coord in handler.stream_coordination_activity():
                    coord_count += 1

                    event_emoji = {
                        "position_opening": "📈",
                        "position_closing": "📉",
                        "conflict_resolved": "✅",
                        "priority_assigned": "🎯",
                    }
                    emoji = event_emoji.get(coord["event_type"], "⚪")

                    if verbose:
                        print(
                            f"   {emoji} {coord['event_type']}: "
                            f"Bot {coord['bot_id']} on {coord['symbol']} "
                            f"(priority: {coord['priority']})"
                        )
                    elif coord_count % 4 == 0:
                        print(f"   📊 Coordination events: {coord_count}")

                    if coord.get("update_id", 0) >= 6:  # Limit events
                        break

                return coord_count

            # Run all streams concurrently
            start_time = time.time()
            status_count, blocking_count, coord_count = await asyncio.gather(
                status_monitor(), blocking_monitor(), coordination_monitor()
            )
            elapsed = time.time() - start_time

            print(
                f"✅ Coordination streaming completed: "
                f"{status_count} status updates, "
                f"{blocking_count} blocking events, "
                f"{coord_count} coordination events in {elapsed:.1f}s"
            )
            return True

    except Exception as e:
        print(f"❌ Bot coordination streaming failed: {e}")
        return False


async def run_demo(args) -> bool:
    """Main demo runner (mirrors fullon_cache example structure)."""
    print("🚀 fullon_cache_api Bot WebSocket Demo")
    print("====================================")
    print("📝 Mirrors fullon_cache BotCache but via WebSocket")
    print("🔧 Shows async iterator patterns (NO CALLBACKS!)")

    # Connection test
    print("\n🔌 Testing WebSocket connection...")
    if not await test_websocket_connection():
        return False

    start_time = time.time()
    results = {}

    # Run selected operations
    if args.operations in ["basic", "all"]:
        results["basic"] = await basic_blocking_demo(args.verbose)

    if args.operations in ["status", "all"]:
        results["status"] = await bot_status_demo(args.verbose)

    if args.operations in ["positions", "all"]:
        results["positions"] = await position_opening_demo(args.verbose)

    if args.operations in ["coordination", "all"]:
        results["coordination"] = await streaming_coordination_demo(
            args.duration, args.verbose
        )

    # Summary
    elapsed = time.time() - start_time
    success_count = sum(results.values())
    total_count = len(results)

    print("\n📊 === Summary ===")
    print(f"⏱️  Total time: {elapsed:.2f}s")
    print(f"✅ Success: {success_count}/{total_count} operations")

    if success_count == total_count:
        print("🎉 All bot WebSocket operations completed!")
        print("🎯 This shows the pattern for BotCache → WebSocket API")
        return True
    else:
        failed = [op for op, success in results.items() if not success]
        print(f"❌ Failed operations: {', '.join(failed)}")
        return False


def main():
    """Main CLI interface (mirrors fullon_cache example style)."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--operations",
        choices=["basic", "status", "positions", "coordination", "all"],
        default="all",
        help="Operations to demonstrate (default: all)",
    )
    parser.add_argument(
        "--bots",
        type=int,
        default=3,
        help="Number of bots for coordination demo (default: 3)",
    )
    parser.add_argument(
        "--symbols",
        default="BTC/USDT,ETH/USDT",
        help="Comma-separated symbols (default: BTC/USDT,ETH/USDT)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=15,
        help="Streaming duration in seconds (default: 15)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output with detailed bot activity",
    )

    args = parser.parse_args()

    try:
        success = asyncio.run(run_demo(args))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🔄 Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
