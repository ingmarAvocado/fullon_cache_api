# 🚀 fullon_cache_api Examples

**WebSocket-based cache API examples demonstrating real-time data operations**

This directory contains examples that mirror **fullon_cache** functionality but expose operations via **WebSocket API** with clean async iterator patterns (NO CALLBACKS!).

## 🎯 Purpose

These examples demonstrate the **desired WebSocket API pattern** for fullon_cache_api:

```python
async with fullon_cache_api(ws_url="ws://localhost:8000") as handler:
    # One-shot queries via WebSocket
    ticker = await handler.get_ticker("binance", "BTC/USDT")
    
    # Real-time streams via WebSocket (async iterators)
    async for update in handler.stream_tickers("binance", ["BTC/USDT"]):
        print(f"Live: ${update['price']}")
```

## 📁 Available Examples

| Example | Description | Key Operations |
|---------|-------------|----------------|
| `basic_usage.py` | Basic WebSocket context manager demo | Connection, queries, streaming |
| `example_tick_cache.py` | Ticker cache WebSocket operations | get_ticker, stream_tickers |
| `example_account_cache.py` | Account cache WebSocket operations | get_balances, stream_positions |
| `example_bot_cache.py` | Bot cache WebSocket operations | is_blocked, stream_bot_status |
| `example_orders_cache.py` | Orders cache WebSocket operations | get_queue_length, stream_orders |
| `example_trades_cache.py` | Trades cache WebSocket operations | get_trades, stream_trade_updates |
| `example_ohlcv_cache.py` | OHLCV cache WebSocket operations | get_ohlcv_bars, stream_ohlcv |
| `example_process_cache.py` | Process cache WebSocket operations | get_system_health, stream_metrics |

## 🚀 Quick Start

### List All Examples
```bash
python run_all.py --list
```

### Run All Examples
```bash
# Run all examples
python run_all.py

# Run all examples (quick mode)
python run_all.py --quick

# Run all examples with detailed output
python run_all.py --verbose
```

### Run Specific Examples
```bash
# Run only ticker example
python run_all.py --only tick_cache

# Run ticker and bot examples
python run_all.py --only tick_cache bot_cache

# Run all except process monitoring
python run_all.py --exclude process_cache

# Run specific examples in quick mode with verbose output
python run_all.py --only tick_cache account_cache --quick --verbose
```

### Run Individual Examples
```bash
# Basic usage demo
python example_tick_cache.py --operations all --verbose

# Streaming demo
python example_tick_cache.py --operations streaming --duration 10

# Account operations
python example_account_cache.py --operations basic --accounts 3

# Bot coordination
python example_bot_cache.py --operations coordination --duration 15
```

## 🔧 Current Status: WORKING WEBSOCKET SERVER

**✅ The ticker cache example now uses a real WebSocket server with working cache operations!**

### What Works Now:
- ✅ **WebSocket context manager pattern**
- ✅ **Async iterator streaming (NO CALLBACKS!)**  
- ✅ **CLI interfaces matching fullon_cache**
- ✅ **Complete operation coverage**
- ✅ **Selective example running**
- ✅ **Real WebSocket server with in-memory cache**
- ✅ **Working ticker operations (get_ticker, set_ticker, streaming)**

### Next Phase:
- 🔧 **Integrate with fullon_cache for other examples**
- 🔧 **Test database integration** 
- 🔧 **Live Redis cache operations**
- 🔧 **Real-time pub/sub streaming**

## 📋 Example CLI Options

Each example supports similar CLI options to fullon_cache:

### Common Options
```bash
--operations CHOICE    # Operations to run: basic, streaming, all, etc.
--verbose, -v         # Detailed output
--help               # Show help
```

### Example-Specific Options
```bash
# Ticker cache
--exchanges binance,kraken    # Exchanges to test
--symbols BTC/USDT,ETH/USDT  # Symbols to test  
--duration 15                # Streaming duration

# Account cache  
--accounts 3                 # Number of accounts
--duration 10               # Streaming duration

# Bot cache
--bots 5                    # Number of bots
--duration 20               # Coordination demo duration

# Orders cache
--orders 50                 # Number of orders
--batch-size 10            # Batch processing size

# OHLCV cache
--timeframes 1m,5m         # Timeframes to test

# Process cache
--duration 30              # Monitoring duration
```

## 🎯 Key Patterns Demonstrated

### 1. **WebSocket Context Manager**
```python
async with fullon_cache_api() as handler:
    # All operations inside context manager
    result = await handler.some_operation()
```

### 2. **Async Queries (Request/Response)**
```python
# READ-ONLY operations via WebSocket
ticker = await handler.get_ticker("binance", "BTC/USDT")
status = await handler.get_order_status("order123")
bots = await handler.get_bots()
```

### 3. **Async Iterators for Streaming (NO CALLBACKS!)**
```python
# Real-time streams via async iteration
async for ticker_update in handler.stream_tickers("binance", ["BTC/USDT"]):
    print(f"Live price: ${ticker_update['price']}")

async for bot_event in handler.stream_bot_status():
    print(f"Bot {bot_event['bot_id']} status: {bot_event['status']}")
```

### 4. **Concurrent Streaming**
```python
# Multiple streams concurrently
async def monitor_tickers():
    async for update in handler.stream_tickers("binance", ["BTC/USDT"]):
        process_ticker(update)

async def monitor_orders():
    async for update in handler.stream_order_queue("binance"):
        process_order_queue(update)

# Run concurrently
await asyncio.gather(monitor_tickers(), monitor_orders())
```

## 🔍 Operations Coverage

### READ-ONLY Operations (✅ Supported)
- **TickCache**: `get_ticker`, `get_price` + streaming
- **AccountCache**: `get_balances`, `get_positions` + streaming  
- **BotCache**: `is_blocked`, `get_bots` + streaming
- **OrdersCache**: `get_order_status`, `get_queue_length` + streaming
- **TradesCache**: `get_trades`, `get_trade_status` + streaming
- **OHLCVCache**: `get_latest_ohlcv_bars` + streaming
- **ProcessCache**: `get_system_health`, `get_active_processes` + streaming

### Write Operations (❌ Not in Scope)
- All `set_*`, `push_*`, `update_*`, `block_*` operations are **intentionally excluded**
- This is a **READ-ONLY** API following LRRS principles

## 🧪 Testing Strategy

### Development Workflow
```bash
# Test specific example during development
python run_all.py --only tick_cache --verbose

# Test multiple related examples
python run_all.py --only tick_cache account_cache bot_cache --quick

# Test everything except slow examples
python run_all.py --exclude process_cache ohlcv_cache
```

### Integration Testing
```bash
# Full test suite (when real WebSocket server is ready)
python run_all.py --verbose

# Quick smoke test
python run_all.py --quick
```

## 🚀 Next Steps

1. **Implement real WebSocket server** with fullon_cache integration
2. **Add test database setup/teardown** like fullon_cache examples
3. **Connect to live Redis** for real cache operations  
4. **Implement pub/sub streaming** for real-time updates
5. **Performance testing** with concurrent connections

## 💡 Tips for Development

### Run Single Example
```bash
# Fastest way to test one example
python example_tick_cache.py --operations basic

# Test streaming specifically
python example_tick_cache.py --operations streaming --duration 5 --verbose
```

### Debug Issues
```bash
# Verbose output shows detailed operations
python run_all.py --only problematic_example --verbose

# Quick mode for faster iteration
python run_all.py --only example_name --quick
```

### Performance Testing
```bash
# Run all examples to check performance
time python run_all.py

# Run streaming examples to check latency
python run_all.py --only tick_cache bot_cache trades_cache --verbose
```

---

**🎯 The ticker example now demonstrates a working WebSocket API pattern! The server starts automatically, connects to an in-memory cache, and provides real-time streaming data via async iterators.** 🚀

**Next step: Integrate the other examples with fullon_cache operations like the ticker example.**