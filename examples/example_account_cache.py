#!/usr/bin/env python3
"""
Account Cache WebSocket Operations Example

This mirrors fullon_cache example_account_cache.py but uses WebSocket API calls
instead of direct cache operations. Shows the desired WebSocket pattern for
account and position operations.

PROTOTYPE - Shows desired API, actual WebSocket implementation comes later.

Usage:
    python example_account_cache.py --operations basic --accounts 3
    python example_account_cache.py --operations positions --verbose
    python example_account_cache.py --operations all --accounts 5
"""

import argparse
import asyncio
import random
import sys
import time
from collections.abc import AsyncIterator
from typing import Any, Optional


class MockAccountWebSocketAPI:
    """Mock WebSocket API for account operations (shows desired pattern)."""

    def __init__(self, ws_url: str = "ws://localhost:8000"):
        self.ws_url = ws_url

    async def __aenter__(self):
        print("🔌 Account WebSocket connected")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("🔌 Account WebSocket disconnected")

    # READ-ONLY Account Operations (mirroring AccountCache)
    async def get_user_balances(self, exchange_id: int) -> dict[str, dict[str, float]]:
        """Get user balances via WebSocket (mirrors AccountCache.get_user_balances)."""
        await asyncio.sleep(0.02)  # Simulate WebSocket latency

        # Mock balance data
        currencies = ["BTC", "USDT", "ETH", "ADA"]
        balances = {}

        for currency in currencies:
            total = random.uniform(0.1, 100.0)
            used = total * random.uniform(0, 0.3)  # 0-30% used
            free = total - used

            balances[currency] = {
                "total": round(total, 8),
                "free": round(free, 8),
                "used": round(used, 8),
            }

        return balances

    async def get_user_balance(
        self, exchange_id: int, currency: str
    ) -> Optional[dict[str, float]]:
        """Get specific currency balance via WebSocket."""
        await asyncio.sleep(0.02)
        balances = await self.get_user_balances(exchange_id)
        return balances.get(currency)

    async def get_position(
        self, exchange_id: int, symbol: str
    ) -> Optional[dict[str, Any]]:
        """Get position data via WebSocket (mirrors AccountCache.get_position)."""
        await asyncio.sleep(0.02)

        # Mock position data
        volume = random.uniform(0.1, 5.0)
        price = random.uniform(10000, 50000)
        cost = volume * price

        return {
            "symbol": symbol,
            "volume": round(volume, 8),
            "cost": round(cost, 2),
            "price": round(price, 2),
            "fee": round(cost * 0.001, 2),  # 0.1% fee
            "timestamp": time.time(),
            "ex_id": str(exchange_id),
        }

    async def get_positions(self, exchange_id: int) -> dict[str, dict[str, Any]]:
        """Get all positions via WebSocket (mirrors AccountCache.get_positions)."""
        await asyncio.sleep(0.02)

        symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
        positions = {}

        for symbol in symbols:
            if random.random() > 0.3:  # 70% chance of having position
                positions[symbol] = await self.get_position(exchange_id, symbol)

        return positions

    async def get_portfolio_summary(self, exchange_id: int) -> dict[str, Any]:
        """Get portfolio summary via WebSocket."""
        await asyncio.sleep(0.02)

        balances = await self.get_user_balances(exchange_id)
        positions = await self.get_positions(exchange_id)

        # Calculate portfolio metrics
        total_balance_usd = sum(
            bal["total"] * random.uniform(20000, 50000)
            if curr == "BTC"
            else bal["total"] * random.uniform(2000, 4000)
            if curr == "ETH"
            else bal["total"]
            for curr, bal in balances.items()
        )

        return {
            "exchange_id": exchange_id,
            "total_balance_usd": round(total_balance_usd, 2),
            "currencies_count": len(balances),
            "positions_count": len(positions),
            "free_balance_ratio": random.uniform(0.6, 0.9),
            "last_updated": time.time(),
        }

    # Streaming Operations (async iterators)
    async def stream_balance_updates(
        self, exchange_id: int
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream live balance updates via WebSocket."""
        print(f"📡 Streaming balance updates for exchange {exchange_id}")

        for i in range(10):  # Mock 10 updates
            await asyncio.sleep(1.0)  # Real-time simulation

            # Mock balance change
            currency = random.choice(["BTC", "USDT", "ETH"])
            balance_change = random.uniform(-10.0, 10.0)

            yield {
                "type": "balance_update",
                "exchange_id": exchange_id,
                "currency": currency,
                "balance_change": round(balance_change, 8),
                "new_balance": round(random.uniform(10, 100), 8),
                "timestamp": time.time(),
                "update_id": i,
            }

    async def stream_position_updates(
        self, exchange_id: int
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream live position updates via WebSocket."""
        print(f"📡 Streaming position updates for exchange {exchange_id}")

        for i in range(8):  # Mock 8 updates
            await asyncio.sleep(1.5)  # Position updates slower than balance

            # Mock position change
            symbol = random.choice(["BTC/USDT", "ETH/USDT", "ADA/USDT"])
            action = random.choice(["opened", "modified", "closed"])

            yield {
                "type": "position_update",
                "exchange_id": exchange_id,
                "symbol": symbol,
                "action": action,
                "volume": round(random.uniform(0.1, 2.0), 8),
                "price": round(random.uniform(20000, 50000), 2),
                "timestamp": time.time(),
                "update_id": i,
            }


def fullon_cache_api(ws_url: str = "ws://localhost:8000") -> MockAccountWebSocketAPI:
    """Create account WebSocket API client."""
    return MockAccountWebSocketAPI(ws_url)


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


async def basic_account_operations(
    account_count: int = 3, verbose: bool = False
) -> bool:
    """Demonstrate basic account operations via WebSocket."""
    print("👤 === Basic Account WebSocket Operations ===")

    try:
        async with fullon_cache_api() as handler:
            print(f"🔄 Testing account operations for {account_count} accounts...")

            for exchange_id in range(1001, 1001 + account_count):
                # Get balances via WebSocket
                balances = await handler.get_user_balances(exchange_id)

                if verbose:
                    print(f"   💰 Exchange {exchange_id}: {len(balances)} currencies")
                    for currency, balance in balances.items():
                        print(
                            f"      {currency}: {balance['total']:.8f} "
                            f"(free: {balance['free']:.8f})"
                        )

                # Test specific balance query
                btc_balance = await handler.get_user_balance(exchange_id, "BTC")
                if btc_balance:
                    if verbose:
                        print(f"   ₿ BTC Balance: {btc_balance['total']:.8f}")

                # Get portfolio summary
                summary = await handler.get_portfolio_summary(exchange_id)

                print(
                    f"   📊 Exchange {exchange_id}: "
                    f"${summary['total_balance_usd']:,.2f} USD, "
                    f"{summary['currencies_count']} currencies, "
                    f"{summary['positions_count']} positions"
                )

            print(f"✅ Account operations completed for {account_count} accounts")
            return True

    except Exception as e:
        print(f"❌ Basic account operations failed: {e}")
        return False


async def position_operations(verbose: bool = False) -> bool:
    """Demonstrate position operations via WebSocket."""
    print("📈 === Position WebSocket Operations ===")

    try:
        async with fullon_cache_api() as handler:
            exchange_id = 2001

            # Get all positions
            positions = await handler.get_positions(exchange_id)
            print(f"🔄 Retrieved {len(positions)} positions for exchange {exchange_id}")

            for symbol, position in positions.items():
                pnl_pct = random.uniform(-5.0, 5.0)  # Mock P&L
                pnl_symbol = "📈" if pnl_pct > 0 else "📉" if pnl_pct < 0 else "➡️"

                if verbose:
                    print(
                        f"   {pnl_symbol} {symbol}: {position['volume']:.8f} @ "
                        f"${position['price']:.2f} (${position['cost']:.2f}) "
                        f"P&L: {pnl_pct:+.2f}%"
                    )

                # Get individual position
                single_pos = await handler.get_position(exchange_id, symbol)
                if not single_pos:
                    print(f"❌ Failed to get individual position for {symbol}")
                    return False

            if not positions:
                print("   📭 No positions found (this is normal for demo)")

            print("✅ Position operations completed successfully")
            return True

    except Exception as e:
        print(f"❌ Position operations failed: {e}")
        return False


async def streaming_demo(duration: int = 10, verbose: bool = False) -> bool:
    """Demonstrate real-time account streaming."""
    print("📡 === Account Streaming Demo ===")

    try:
        async with fullon_cache_api() as handler:
            exchange_id = 3001

            print(f"🔄 Starting account streams for {duration}s...")

            async def balance_monitor():
                update_count = 0
                async for update in handler.stream_balance_updates(exchange_id):
                    update_count += 1
                    change_symbol = "📈" if update["balance_change"] > 0 else "📉"

                    if verbose:
                        print(
                            f"   💰 {change_symbol} {update['currency']}: "
                            f"{update['balance_change']:+.8f} → "
                            f"{update['new_balance']:.8f}"
                        )
                    elif update_count % 3 == 0:
                        print(f"   📊 Balance updates: {update_count}")

                    if update.get("update_id", 0) >= 4:  # Limit updates
                        break

                return update_count

            async def position_monitor():
                update_count = 0
                async for update in handler.stream_position_updates(exchange_id):
                    update_count += 1
                    action_symbol = {"opened": "🟢", "modified": "🟡", "closed": "🔴"}
                    symbol = action_symbol.get(update["action"], "⚪")

                    if verbose:
                        print(
                            f"   📈 {symbol} {update['symbol']}: {update['action']} "
                            f"{update['volume']:.8f} @ ${update['price']:.2f}"
                        )
                    elif update_count % 2 == 0:
                        print(f"   📊 Position updates: {update_count}")

                    if update.get("update_id", 0) >= 3:  # Limit updates
                        break

                return update_count

            # Run both streams concurrently
            start_time = time.time()
            balance_count, position_count = await asyncio.gather(
                balance_monitor(), position_monitor()
            )
            elapsed = time.time() - start_time

            print(
                f"✅ Streaming completed: {balance_count} balance updates, "
                f"{position_count} position updates in {elapsed:.1f}s"
            )
            return True

    except Exception as e:
        print(f"❌ Account streaming failed: {e}")
        return False


async def run_demo(args) -> bool:
    """Main demo runner (mirrors fullon_cache example structure)."""
    print("🚀 fullon_cache_api Account WebSocket Demo")
    print("=========================================")
    print("📝 Mirrors fullon_cache AccountCache but via WebSocket")
    print("🔧 Shows async iterator patterns (NO CALLBACKS!)")

    # Connection test
    print("\n🔌 Testing WebSocket connection...")
    if not await test_websocket_connection():
        return False

    start_time = time.time()
    results = {}

    # Run selected operations
    if args.operations in ["basic", "all"]:
        results["basic"] = await basic_account_operations(args.accounts, args.verbose)

    if args.operations in ["positions", "all"]:
        results["positions"] = await position_operations(args.verbose)

    if args.operations in ["streaming", "all"]:
        results["streaming"] = await streaming_demo(args.duration, args.verbose)

    # Summary
    elapsed = time.time() - start_time
    success_count = sum(results.values())
    total_count = len(results)

    print("\n📊 === Summary ===")
    print(f"⏱️  Total time: {elapsed:.2f}s")
    print(f"✅ Success: {success_count}/{total_count} operations")

    if success_count == total_count:
        print("🎉 All account WebSocket operations completed!")
        print("🎯 This shows the pattern for AccountCache → WebSocket API")
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
        choices=["basic", "positions", "streaming", "all"],
        default="all",
        help="Operations to demonstrate (default: all)",
    )
    parser.add_argument(
        "--accounts",
        type=int,
        default=3,
        help="Number of accounts for basic operations (default: 3)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Streaming duration in seconds (default: 10)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output with detailed account info",
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
