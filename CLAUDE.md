# 🤖 CLAUDE.md - fullon_cache_api Development Guide

**For LLMs/Claude: Complete development guidelines for the fullon_cache_api project**

## 🎯 Project Mission

**LRRS-Compliant Library**: Create a composable FastAPI gateway that exposes **READ-ONLY** fullon_cache operations as secure REST endpoints, designed for integration into a master_api alongside other fullon libraries with perfect namespace separation.

## 🏗️ LRRS Architecture Principles

**This project MUST follow LRRS principles:**

- **Little**: Single purpose - READ-ONLY cache data API gateway only
- **Responsible**: One clear job - secure REST API for read-only cache operations
- **Reusable**: Works with any fullon_cache deployment, composable into master_api
- **Separate**: Zero coupling beyond fullon_cache + fullon_log

### **Critical Design Decision: Library vs Standalone**

```python
# Library usage (PRIMARY use case):
from fullon_cache_api import FullonCacheGateway, get_all_routers

# Master API integration with namespace separation:
app = FastAPI(title="Fullon Master API")
for router in get_all_routers():
    app.include_router(router, prefix="/api/v1/cache", tags=["Cache"])

# Standalone usage (TESTING only):
python -m fullon_cache_api.standalone_server
```

## 📊 Cache Focus Areas

**Core Cache Operations** (using fullon_cache dependency):

### **🔍 READ-ONLY CACHE API**
**IMPORTANT**: This API **ONLY** exposes read/fetch operations. No updates, inserts, or write operations are in scope.

### **1. Cache Data Retrieval**
- Retrieve ticker data from Redis cache - **READ ONLY**
- Retrieve account/position data from Redis - **READ ONLY**
- Query order status and queue information
- Bot coordination status and exchange blocking info
- Trade queue status and processing metrics
- OHLCV cached data retrieval
- Process monitoring and health status

### **2. fullon_cache Integration Pattern**
```python
# READ-ONLY cache operations:
from fullon_cache import TickCache, OrdersCache, BotCache

# Ticker data queries
async with TickCache() as cache:
    ticker = await cache.get_ticker("binance", "BTC/USDT")
    all_tickers = await cache.get_all_tickers("binance")

# Order queue status  
async with OrdersCache() as cache:
    queue_size = await cache.get_queue_size("binance")
    order_status = await cache.get_order_status("order123")

# Bot coordination status
async with BotCache() as cache:
    bot_status = await cache.get_bot_status("bot_1")
    is_blocked = await cache.is_exchange_blocked("binance", "BTC/USDT")
```

### **3. Read-Only Cache API Endpoints** (with namespace separation)
- `GET /api/v1/cache/tickers/{exchange}/{symbol}` - Retrieve ticker data
- `GET /api/v1/cache/tickers/{exchange}` - All tickers for exchange
- `GET /api/v1/cache/accounts/{user_id}/positions` - Account positions from cache
- `GET /api/v1/cache/orders/{order_id}/status` - Order status from Redis
- `GET /api/v1/cache/orders/queue/size` - Order queue metrics
- `GET /api/v1/cache/bots/{bot_id}/status` - Bot coordination status
- `GET /api/v1/cache/trades/queue/status` - Trade processing queue info
- `GET /api/v1/cache/ohlcv/{symbol}/{timeframe}` - Cached OHLCV data
- `GET /api/v1/cache/processes/status` - Process monitoring data

## 🛠️ Architecture Overview

### **Master API Ecosystem with Namespace Separation**
```
┌─────────────────────────────────────────────────────────────────┐
│                        Fullon Master API                       │
│                     (Authentication Hub)                       │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ fullon_orm_api  │ │fullon_cache_api │ │fullon_ohlcv_api │   │
│  │   (Database)    │ │     (Redis)     │ │  (Market Data)  │   │
│  │ /api/v1/orm/*   │ │ /api/v1/cache/* │ │/api/v1/market/* │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
   fullon_orm              Redis Cache             Market Data APIs
    Database               Operations              (External APIs)

# Perfect namespace separation prevents conflicts:
GET /api/v1/orm/trades/         # Database: Trade records 
GET /api/v1/cache/trades/queue  # Redis: Trade processing queue ← THIS PROJECT
GET /api/v1/market/trades/      # Market: Historical trade data
```

### **Project Structure**
```
fullon_cache_api/
├── src/fullon_cache_api/
│   ├── __init__.py              # Library exports: FullonCacheGateway, get_all_routers
│   ├── gateway.py               # Main library class (composable)
│   ├── standalone_server.py     # Testing server only
│   ├── main.py                  # Legacy compatibility
│   ├── dependencies/            # FastAPI dependencies
│   │   └── cache.py             # Cache session management
│   ├── routers/                 # Cache endpoints
│   │   ├── tickers.py           # Ticker cache endpoints
│   │   ├── accounts.py          # Account cache endpoints
│   │   ├── orders.py            # Order cache endpoints
│   │   ├── bots.py             # Bot cache endpoints
│   │   ├── trades.py           # Trade cache endpoints
│   │   ├── ohlcv.py            # OHLCV cache endpoints
│   │   └── processes.py        # Process monitoring endpoints
│   └── models/                  # Pydantic request/response models
│       ├── requests.py          # Cache API request models
│       └── responses.py         # Cache API response models
├── examples/                    # Working code examples
├── tests/                       # Comprehensive test suite
└── docs/                        # Additional documentation
```

## 🚀 Core Development Patterns

### **1. Read-Only Cache Repository Endpoint Pattern**
```python
# Standard pattern for all READ-ONLY cache endpoints:
@router.get("/{exchange}/{symbol}/ticker", response_model=TickerResponse)
async def get_ticker(
    exchange: str,
    symbol: str
):
    # 1. Validate exchange and symbol
    validate_exchange_symbol(exchange, symbol)
    
    # 2. READ-ONLY cache operation
    async with TickCache() as cache:
        ticker = await cache.get_ticker(exchange, symbol)
        if not ticker:
            raise HTTPException(status_code=404, detail="Ticker not found in cache")
    
    # 3. Return formatted response (no modifications to cache)
    return TickerResponse(
        exchange=exchange,
        symbol=symbol,
        ticker=ticker,
        cached_at=ticker.timestamp
    )
```

### **2. Cache Connection Management**
```python
# Cache session patterns:
from fullon_cache import TickCache, OrdersCache, BotCache

# Health check pattern
async def check_cache_health():
    async with TickCache() as cache:
        return await cache.test()  # Redis connection test

# Multiple cache operations
async def get_trading_status(user_id: str):
    async with OrdersCache() as orders_cache, BotCache() as bot_cache:
        order_count = await orders_cache.get_user_order_count(user_id)
        bot_status = await bot_cache.get_user_bot_status(user_id)
        return {"orders": order_count, "bots": bot_status}
```

### **3. Error Handling Pattern**
```python
from fastapi import HTTPException

# Cache-specific HTTP errors:
raise HTTPException(status_code=404, detail="Data not found in cache")
raise HTTPException(status_code=503, detail="Cache service unavailable")
raise HTTPException(status_code=422, detail="Invalid cache key format")
raise HTTPException(status_code=408, detail="Cache operation timeout")
```

### **4. Logging Pattern (fullon_log)**
```python
from fullon_log import get_component_logger
import time

# Component-specific logging (REQUIRED pattern):
logger = get_component_logger("fullon.api.cache")

# Standard cache endpoint logging pattern:
async def get_ticker_with_logging(exchange: str, symbol: str):
    start_time = time.time()
    logger.info("Cache operation started", 
               operation="get_ticker", 
               exchange=exchange, 
               symbol=symbol)
    
    try:
        async with TickCache() as cache:
            ticker = await cache.get_ticker(exchange, symbol)
            cache_hit = ticker is not None
            
        duration_ms = (time.time() - start_time) * 1000
        
        # Success logging with performance metrics
        logger.info("Cache operation completed", 
                   operation="get_ticker", 
                   exchange=exchange, 
                   symbol=symbol,
                   cache_hit=cache_hit,
                   latency_ms=duration_ms,
                   status="success")
        
        return ticker
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        # Error logging with context
        logger.error("Cache operation failed", 
                    operation="get_ticker",
                    exchange=exchange,
                    symbol=symbol,
                    error=str(e),
                    error_type=type(e).__name__,
                    latency_ms=duration_ms,
                    status="error")
        raise

# Health check logging:
async def log_cache_health():
    try:
        async with TickCache() as cache:
            await cache.test()
        logger.info("Cache health check passed", service="redis", status="healthy")
    except Exception as e:
        logger.error("Cache health check failed", service="redis", status="unhealthy", error=str(e))

# Component initialization logging:
class FullonCacheGateway:
    def __init__(self, prefix: str = "", title: str = "fullon_cache_api"):
        self.logger = get_component_logger("fullon.api.cache.gateway")
        self.logger.info("Cache gateway initialized", prefix=prefix, title=title)
```

## 🔑 Environment Configuration

### **Required Environment Variables**
```bash
# Redis Configuration (handled by fullon_cache)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=optional

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Logging (fullon-log)
LOG_LEVEL=DEBUG              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=development       # beautiful, minimal, development, detailed, trading, json
LOG_CONSOLE=true             # Enable console output
LOG_COLORS=true              # Enable colored output
LOG_FILE_PATH=/tmp/fullon/cache_api.log
LOG_ROTATION=100 MB          # Optional: file rotation
LOG_RETENTION=7 days         # Optional: retention period
```

## 📋 Cache Endpoint Coverage Requirements

**Every READ-ONLY fullon_cache operation MUST have an API endpoint:**

### **TickCache Endpoints (READ-ONLY)** - `/api/v1/cache/tickers/`
- Ticker data retrieval by exchange/symbol
- All tickers for an exchange
- Ticker subscription status
- Price data with timestamp information

### **AccountCache Endpoints (READ-ONLY)** - `/api/v1/cache/accounts/`
- Account position data retrieval
- User balance information from cache
- Account status and metadata
- Portfolio summaries from cached data

### **OrdersCache Endpoints (READ-ONLY)** - `/api/v1/cache/orders/`
- Order status queries from Redis
- Order queue size and metrics
- Queue processing status
- Order history from cache

### **BotCache Endpoints (READ-ONLY)** - `/api/v1/cache/bots/`
- Bot coordination status
- Exchange blocking status
- Bot activity monitoring
- Multi-bot coordination info

### **TradesCache Endpoints (READ-ONLY)** - `/api/v1/cache/trades/`
- Trade processing queue status
- Trade data from cache
- Trade statistics and metrics
- Queue performance monitoring

### **OHLCVCache Endpoints (READ-ONLY)** - `/api/v1/cache/ohlcv/`
- Cached OHLCV data retrieval
- Timeframe-specific cache queries
- OHLCV data freshness status
- Cache performance metrics

### **ProcessCache Endpoints (READ-ONLY)** - `/api/v1/cache/processes/`
- System process monitoring
- Process health status
- Process performance metrics
- System-wide cache status

## 🧪 Testing Strategy

### **Test Categories**
```bash
# Unit tests - Individual components
tests/test_gateways.py
tests/test_cache_operations.py  
tests/test_models.py

# Integration tests - End-to-end workflows
tests/integration/test_cache_lifecycle.py
tests/integration/test_redis_operations.py

# Performance tests - Cache performance testing
tests/performance/test_endpoints.py
```

### **Required Test Coverage**
- **Cache Operations**: Data retrieval, Redis connections, cache misses
- **Redis Integration**: All cache operations, connection handling
- **Data Validation**: Cache model validation, exchange/symbol validation
- **Integration**: Complete cache workflows, multi-cache operations
- **Performance**: Response times, large dataset handling, concurrent requests
- **Namespace**: Verify all endpoints use /api/v1/cache/ prefixes correctly

## 🚀 Quick Start Commands

```bash
# Initial setup
make setup      # Install dependencies, setup pre-commit

# Development
make dev        # Start development server
make test       # Run test suite
make check      # Full quality check

# Testing & Quality  
./run_test.py   # Comprehensive test runner (REQUIRED before commits)
make format     # Format code with Black + Ruff
make lint       # Check code quality

# Cache API Exploration
open http://localhost:8000/docs    # Swagger UI
open http://localhost:8000/redoc   # ReDoc interface
```

## 📖 Key References

- **Cache Operations**: See fullon_cache documentation for all available methods
- **Examples**: Working code in `examples/` directory
- **Tests**: Pattern examples in `tests/conftest.py`
- **fullon_cache Guide**: Refer to dependency documentation

## ⚠️ Critical Rules

1. **LRRS Compliance**: Never violate Little, Responsible, Reusable, Separate
2. **TDD Only**: Tests first, implementation second, `./run_test.py` must pass
3. **Library First**: Design for master_api composition, standalone is secondary
4. **Read-Only**: No write/update/insert operations in scope
5. **Namespace Separation**: Always use /api/v1/cache/ prefix
6. **Async Only**: Every operation must be asynchronous

## 🔄 Cache-Specific Best Practices

### **1. Always Use Context Managers**
```python
# Correct:
async with TickCache() as cache:
    data = await cache.get_ticker("binance", "BTC/USDT")

# Wrong:
cache = TickCache()
data = await cache.get_ticker("binance", "BTC/USDT")  # No cleanup
```

### **2. Handle Cache Misses Gracefully**
```python
# Provide meaningful responses for cache misses:
async def get_cached_ticker(exchange: str, symbol: str):
    async with TickCache() as cache:
        ticker = await cache.get_ticker(exchange, symbol)
        if not ticker:
            raise HTTPException(
                status_code=404, 
                detail=f"Ticker {symbol} not found in {exchange} cache"
            )
        return ticker
```

### **3. Redis Connection Health Monitoring**
```python
# Include health check endpoints:
@router.get("/health")
async def cache_health():
    try:
        async with BaseCache() as cache:
            await cache.test()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Cache unavailable")
```

### **4. Performance Monitoring**
```python
# Log cache performance:
import time

async def get_ticker_with_metrics(exchange: str, symbol: str):
    start_time = time.time()
    async with TickCache() as cache:
        result = await cache.get_ticker(exchange, symbol)
    
    duration = (time.time() - start_time) * 1000
    logger.info("Cache operation completed",
               operation="get_ticker",
               duration_ms=duration,
               cache_hit=result is not None)
    return result
```

## 📊 Fullon Log Integration Best Practices

### **1. Component-Specific Logger Setup**
```python
from fullon_log import get_component_logger, configure_logger

class FullonCacheGateway:
    def __init__(self):
        self.logger = get_component_logger("fullon.api.cache.gateway")
        
        # Optional: Component-specific file logging
        configure_logger(
            file_path="/var/log/fullon/cache_api.log",
            console=True,
            level="INFO"
        )
        
        self.logger.info("Cache gateway initialized", component="gateway")
```

### **2. Router-Level Logging Patterns**
```python
# In each router file (tickers.py, orders.py, etc.)
from fullon_log import get_component_logger

# Router-specific logger
logger = get_component_logger("fullon.api.cache.tickers")

@router.get("/{exchange}/{symbol}")
async def get_ticker(exchange: str, symbol: str):
    logger.info("Ticker request started", exchange=exchange, symbol=symbol)
    
    try:
        # Cache operation with timing
        start_time = time.time()
        async with TickCache() as cache:
            ticker = await cache.get_ticker(exchange, symbol)
        
        duration_ms = (time.time() - start_time) * 1000
        
        if ticker:
            logger.info("Ticker retrieved successfully", 
                       exchange=exchange, 
                       symbol=symbol,
                       latency_ms=duration_ms,
                       cache_hit=True)
        else:
            logger.warning("Ticker not found in cache", 
                          exchange=exchange, 
                          symbol=symbol,
                          latency_ms=duration_ms,
                          cache_hit=False)
            
        return ticker
        
    except Exception as e:
        logger.error("Ticker retrieval failed", 
                    exchange=exchange, 
                    symbol=symbol,
                    error=str(e),
                    error_type=type(e).__name__)
        raise
```

### **3. Environment-Based Logging Configuration**
```python
# Example configurations for different environments

# Development (.env.development)
LOG_LEVEL=DEBUG
LOG_FORMAT=development
LOG_COLORS=true
LOG_CONSOLE=true
LOG_FILE_PATH=/tmp/fullon/cache_api_dev.log

# Production (.env.production)  
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_COLORS=false
LOG_CONSOLE=false
LOG_FILE_PATH=/var/log/fullon/cache_api.log
LOG_ROTATION=100 MB
LOG_RETENTION=30 days

# Trading-specific (.env.trading)
LOG_LEVEL=INFO
LOG_FORMAT=trading
LOG_COLORS=true
LOG_CONSOLE=true
LOG_FILE_PATH=/var/log/fullon/trading_cache.log
```

### **4. Performance and Metrics Logging**
```python
from fullon_log import get_component_logger
import time
from contextlib import asynccontextmanager

logger = get_component_logger("fullon.api.cache.metrics")

@asynccontextmanager
async def log_cache_operation(operation: str, **context):
    """Context manager for consistent cache operation logging."""
    start_time = time.time()
    logger.info(f"Cache {operation} started", operation=operation, **context)
    
    try:
        yield
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Cache {operation} completed", 
                   operation=operation, 
                   latency_ms=duration_ms,
                   status="success",
                   **context)
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Cache {operation} failed", 
                    operation=operation,
                    error=str(e),
                    error_type=type(e).__name__,
                    latency_ms=duration_ms,
                    status="error",
                    **context)
        raise

# Usage:
async def get_ticker(exchange: str, symbol: str):
    async with log_cache_operation("get_ticker", exchange=exchange, symbol=symbol):
        async with TickCache() as cache:
            return await cache.get_ticker(exchange, symbol)
```

### **5. Health Check and Monitoring Integration**
```python
from fullon_log import get_component_logger

logger = get_component_logger("fullon.api.cache.health")

@router.get("/health")
async def health_check():
    """Health check with comprehensive logging."""
    health_status = {"status": "healthy", "services": {}}
    
    # Redis health check
    try:
        async with TickCache() as cache:
            await cache.test()
        health_status["services"]["redis"] = "healthy"
        logger.info("Health check passed", service="redis", status="healthy")
    except Exception as e:
        health_status["services"]["redis"] = "unhealthy"
        health_status["status"] = "unhealthy"
        logger.error("Health check failed", service="redis", status="unhealthy", error=str(e))
    
    # Log overall health status
    logger.info("Health check completed", 
               overall_status=health_status["status"],
               services_count=len(health_status["services"]))
    
    return health_status
```

---

**Remember**: This is a composable library that will integrate with 3-4 other similar libraries in a master_api. Design every decision with composition, namespace separation, and reusability in mind! 🚀