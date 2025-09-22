#!/usr/bin/env python3
"""
Run All WebSocket Cache API Examples

This script runs all fullon_cache_api examples in sequence to demonstrate
the complete WebSocket API functionality.

PROTOTYPE - Shows desired pattern. Will be updated to use real WebSocket
server like fullon_cache examples.

Usage:
    python run_all.py
    python run_all.py --verbose
    python run_all.py --quick  # Run shorter versions
"""

import argparse
import asyncio
import subprocess
import sys
import time
from pathlib import Path


def run_example(script_name: str, args: list = None, verbose: bool = False) -> bool:
    """Run a single example script."""
    script_path = Path(__file__).parent / script_name

    if not script_path.exists():
        print(f"❌ Script not found: {script_name}")
        return False

    cmd = ["python", str(script_path)]
    if args:
        cmd.extend(args)

    print(f"\n🚀 Running {script_name}...")
    print(f"📝 Command: {' '.join(cmd)}")

    try:
        start_time = time.time()

        result = subprocess.run(
            cmd,
            capture_output=not verbose,  # Show output if verbose
            text=True,
            timeout=60,  # 1 minute timeout per example
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ {script_name} completed successfully in {elapsed:.2f}s")
            if not verbose and result.stdout:
                # Show last few lines of output
                lines = result.stdout.strip().split("\n")
                for line in lines[-3:]:
                    print(f"   {line}")
            return True
        else:
            print(f"❌ {script_name} failed with exit code {result.returncode}")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ {script_name} timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"💥 {script_name} crashed: {e}")
        return False


async def main():
    """Main runner for all examples."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output from each example",
    )
    parser.add_argument(
        "--quick", action="store_true", help="Run shorter/faster versions of examples"
    )
    parser.add_argument(
        "--only",
        nargs="*",
        help="Run only specific examples (e.g., --only tick_cache bot_cache)",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Exclude specific examples (e.g., --exclude tick_cache bot_cache)",
    )
    parser.add_argument(
        "--list", action="store_true", help="List all available examples and exit"
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Run real Redis WebSocket examples (requires server + .env)",
    )

    args = parser.parse_args()

    print("🚀 fullon_cache_api - Run All WebSocket Examples")
    print("===============================================")
    print("📝 This runs cache API examples to show WebSocket patterns")
    if args.real:
        print("🔌 Real mode: connects to running FastAPI WS + Redis (from .env)")
    else:
        print("🔧 Mock mode: local demo flows (no Redis required)")

    # Define all examples to run
    mock_examples = [
        {
            "script": "basic_usage.py",
            "args": [],
            "description": "Basic WebSocket context manager demo",
        },
        {
            "script": "example_tick_cache.py",
            "args": [
                "--operations",
                "streaming" if args.quick else "all",
                "--duration",
                "5" if args.quick else "10",
            ],
            "description": "Ticker cache WebSocket operations",
        },
        {
            "script": "example_account_cache.py",
            "args": [
                "--operations",
                "basic" if args.quick else "all",
                "--accounts",
                "2",
            ],
            "description": "Account cache WebSocket operations",
        },
        {
            "script": "example_bot_cache.py",
            "args": [
                "--operations",
                "status" if args.quick else "all",
                "--duration",
                "5" if args.quick else "10",
            ],
            "description": "Bot cache WebSocket operations",
        },
        {
            "script": "example_orders_cache.py",
            "args": [
                "--operations",
                "basic" if args.quick else "all",
                "--orders",
                "20" if args.quick else "50",
            ],
            "description": "Orders cache WebSocket operations",
        },
        {
            "script": "example_trades_cache.py",
            "args": ["--operations", "basic" if args.quick else "all"],
            "description": "Trades cache WebSocket operations",
        },
        {
            "script": "example_ohlcv_cache.py",
            "args": ["--operations", "basic" if args.quick else "all"],
            "description": "OHLCV cache WebSocket operations",
        },
        {
            "script": "example_process_cache.py",
            "args": [
                "--operations",
                "basic" if args.quick else "all",
                "--duration",
                "5" if args.quick else "15",
            ],
            "description": "Process cache WebSocket operations",
        },
    ]

    real_examples = [
        {
            "script": "ticker_websocket_real.py",
            "args": [],
            "description": "Real Redis: Ticker get + stream",
        },
        {
            "script": "orders_websocket_real.py",
            "args": [],
            "description": "Real Redis: Orders queue length + stream",
        },
        {
            "script": "ohlcv_websocket_real.py",
            "args": [],
            "description": "Real Redis: OHLCV latest bars + stream",
        },
    ]

    examples = real_examples if args.real else mock_examples

    # Handle --list option
    if args.list:
        print("\n📋 Available Examples:")
        for i, example in enumerate(mock_examples if not args.real else real_examples, 1):
            script_name = example["script"].replace("example_", "").replace(".py", "")
            print(f"   {i:2d}. {script_name:<12} - {example['description']}")
        print("\nUsage examples:")
        if args.real:
            print("   python run_all.py --real --verbose")
        else:
            print("   python run_all.py --only tick_cache")
            print("   python run_all.py --only tick_cache bot_cache --quick")
            print("   python run_all.py --exclude process_cache --verbose")
        return

    # Filter examples based on --only or --exclude
    if args.only:
        only_set = set(args.only)
        examples = [
            ex for ex in examples if any(only in ex["script"] for only in only_set)
        ]
        if not examples:
            print(f"❌ No examples found matching: {', '.join(args.only)}")
            print("💡 Use --list to see available examples")
            return
    elif args.exclude:
        exclude_set = set(args.exclude)
        examples = [
            ex
            for ex in examples
            if not any(excl in ex["script"] for excl in exclude_set)
        ]

    # Run all examples
    results = []
    start_time = time.time()

    print(f"\n📋 Running {len(examples)} examples ({'REAL' if args.real else 'MOCK'})...")

    for i, example in enumerate(examples, 1):
        print(f"\n{'='*50}")
        print(f"📊 Example {i}/{len(examples)}: {example['description']}")
        print(f"{'='*50}")

        success = run_example(example["script"], example["args"], verbose=args.verbose)

        results.append(
            {
                "script": example["script"],
                "description": example["description"],
                "success": success,
            }
        )

        if not success and not args.verbose:
            print("   💡 Use --verbose to see detailed error output")

    # Final summary
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r["success"])
    total = len(results)

    print(f"\n{'='*60}")
    print("📊 === FINAL SUMMARY ===")
    print(f"{'='*60}")
    print(f"⏱️  Total execution time: {total_time:.2f} seconds")
    print(f"✅ Successful examples: {successful}/{total}")
    print(f"❌ Failed examples: {total - successful}/{total}")

    if successful == total:
        print("\n🎉 ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("🎯 WebSocket API patterns demonstrated across all cache types")
        print("🔧 Ready for real WebSocket server implementation")

        success_rate = 100.0
    else:
        print("\n📋 Results by example:")
        for result in results:
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {result['script']}: {result['description']}")

        success_rate = (successful / total) * 100

    print(f"\n📈 Overall success rate: {success_rate:.1f}%")

    # Exit with appropriate code
    if successful == total:
        print("🚀 All examples ready for real WebSocket implementation!")
        sys.exit(0)
    else:
        print("🔧 Some examples need fixes before WebSocket server integration")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🔄 Run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Runner crashed: {e}")
        sys.exit(1)
