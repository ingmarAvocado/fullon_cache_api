# 🏗️ fullon_cache_api Project Structure

**LRRS-Compliant Cache Data API Gateway Architecture**

## 📋 Project Overview

fullon_cache_api is a composable FastAPI gateway library that exposes **read-only** Redis cache operations as secure REST endpoints. It follows LRRS (Little, Responsible, Reusable, Separate) principles and integrates seamlessly into master_api alongside other fullon libraries with perfect namespace separation.

**🔍 READ-ONLY API**: This library **only** exposes data retrieval operations from Redis cache. No updates, inserts, or write operations are in scope.

**🌐 Namespace Separation**: All endpoints use `/api/v1/cache/` prefix to prevent conflicts with other fullon APIs.

## 🏗️ Architecture Principles

### LRRS Compliance
- **Little**: Single purpose - READ-ONLY cache data API gateway
- **Responsible**: Secure REST API for read-only Redis cache operations  
- **Reusable**: Composable into master_api, works with any fullon_cache deployment
- **Separate**: Zero coupling beyond fullon_cache + fullon_log dependencies

### Design Philosophy
- **Library First**: Primary use case is composition into master_api
- **Standalone Secondary**: Testing and development server mode
- **Cache Focused**: Optimized for read-only Redis cache data patterns
- **Read-Only Operations**: No write/update/insert operations in scope
- **Async Throughout**: All operations are asynchronous
- **Namespace Isolation**: Perfect separation with `/api/v1/cache/` prefix

## 📁 Directory Structure

```
fullon_cache_api/
├── CLAUDE.md                    # 🤖 Development guidelines for LLMs
├── PROJECT_STRUCTURE.md         # 📋 This architecture documentation
├── README.md                    # 📖 Project overview and usage guide
├── Makefile                     # 🔧 Development automation commands
├── pyproject.toml              # 📦 Modern Python project configuration
├── run_test.py                 # 🧪 Comprehensive test runner script
│
├── src/                        # 📂 Source code directory
│   └── fullon_cache_api/      # 📦 Main package
│       ├── __init__.py         # 🔌 Library exports and public API
│       ├── main.py             # 🔄 Legacy compatibility module
│       ├── gateway.py          # 🏗️ Main FullonCacheGateway class
│       ├── standalone_server.py # 🖥️ Development/testing server
│       │
│       ├── dependencies/       # 🔗 FastAPI dependency injection
│       │   ├── __init__.py
│       │   └── cache.py        # 📊 Cache session management
│       │
│       ├── models/            # 📋 Pydantic data models
│       │   ├── __init__.py
│       │   ├── requests.py     # 📥 API request models
│       │   └── responses.py    # 📤 API response models
│       │
│       └── routers/           # 🛣️ FastAPI endpoint routers
│           ├── __init__.py
│           ├── tickers.py      # 📈 Ticker cache endpoints
│           ├── accounts.py     # 👤 Account cache endpoints
│           ├── orders.py       # 📋 Order cache endpoints
│           ├── bots.py        # 🤖 Bot cache endpoints
│           ├── trades.py      # 💹 Trade cache endpoints
│           ├── ohlcv.py       # 🕯️ OHLCV cache endpoints
│           └── processes.py   # ⚙️ Process monitoring endpoints
│
├── examples/                  # 📚 Working code examples
│   ├── basic_usage.py         # 🚀 Simple cache API usage
│   └── library_usage.py       # 🏗️ Master API composition patterns
│
├── tests/                     # 🧪 Comprehensive test suite
│   ├── __init__.py
│   ├── conftest.py            # ⚙️ Pytest configuration and fixtures
│   ├── test_main.py           # 🔬 Main module tests
│   ├── unit/                  # 🔬 Unit tests directory
│   │   └── __init__.py
│   └── integration/           # 🔗 Integration tests directory
│       └── __init__.py
│
└── docs/                      # 📖 Additional documentation
    └── (additional docs)
```

## 🔌 Library Interface

### Public API Exports (`__init__.py`)
```python
from .gateway import FullonCacheGateway

def get_all_routers():
    """Return all routers for master_api composition."""
    pass

# Public exports
__all__ = ["FullonCacheGateway", "get_all_routers"]
```

### Primary Usage Patterns
```python
# Library usage in master_api:
from fullon_cache_api import FullonCacheGateway, get_all_routers

# Standalone usage for testing:
python -m fullon_cache_api.standalone_server
```

## 🏗️ Core Components

### 1. FullonCacheGateway (`gateway.py`)
**Main library class providing composable FastAPI gateway functionality.**

```python
class FullonCacheGateway:
    """
    Configurable cache API gateway for master_api integration.
    
    Features:
    - Configurable URL prefix for composition
    - Auto-generated OpenAPI documentation  
    - Built-in health and info endpoints
    - Router composition for modular design
    - Perfect namespace separation
    """
    
    def __init__(self, prefix: str = "", title: str = "fullon_cache_api"):
        pass
    
    def get_app(self) -> FastAPI:
        """Return configured FastAPI application."""
        pass
        
    def get_routers(self) -> List[APIRouter]:
        """Return all routers for external composition."""
        pass
```

### 2. Router Architecture (`routers/`)
**Modular endpoint organization by cache operation type.**

#### Ticker Cache Router (`tickers.py`) - **READ-ONLY**
- `GET /{exchange}/tickers` - All tickers for exchange
- `GET /{exchange}/{symbol}/ticker` - Specific ticker data
- `GET /{exchange}/tickers/active` - Active tickers list
- `GET /tickers/health` - Ticker cache health status

#### Account Cache Router (`accounts.py`) - **READ-ONLY**
- `GET /{user_id}/positions` - User account positions
- `GET /{user_id}/balances` - Account balance data
- `GET /{user_id}/status` - Account cache status
- `GET /accounts/summary` - Account cache summary

#### Order Cache Router (`orders.py`) - **READ-ONLY**
- `GET /{order_id}/status` - Order status from cache
- `GET /queue/size` - Order queue metrics
- `GET /queue/status` - Queue processing status
- `GET /{user_id}/orders` - User orders from cache

#### Bot Cache Router (`bots.py`) - **READ-ONLY**
- `GET /{bot_id}/status` - Bot coordination status
- `GET /{exchange}/{symbol}/blocked` - Exchange blocking status
- `GET /{user_id}/bots` - User bot statuses
- `GET /coordination/status` - Multi-bot coordination info

#### Trade Cache Router (`trades.py`) - **READ-ONLY**
- `GET /queue/status` - Trade processing queue status
- `GET /queue/size` - Trade queue metrics
- `GET /{trade_id}/status` - Trade processing status
- `GET /performance/metrics` - Trade queue performance

#### OHLCV Cache Router (`ohlcv.py`) - **READ-ONLY**
- `GET /{symbol}/{timeframe}` - Cached OHLCV data
- `GET /{symbol}/timeframes` - Available timeframes
- `GET /cache/status` - OHLCV cache health
- `GET /performance/metrics` - Cache performance stats

#### Process Monitoring Router (`processes.py`) - **READ-ONLY**
- `GET /status` - System process status
- `GET /health` - Process health monitoring
- `GET /performance` - Process performance metrics
- `GET /cache/overview` - System-wide cache status

### 3. Data Models (`models/`)
**Pydantic models for request/response validation and OpenAPI documentation.**

#### Request Models (`requests.py`)
```python
class CacheQueryRequest(BaseModel):
    exchange: str
    symbol: str
    timeout: Optional[int] = 5

class TimeRangeRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    # READ-ONLY: No write operation models
```

#### Response Models (`responses.py`) 
```python
class TickerResponse(BaseModel):
    exchange: str
    symbol: str
    ticker: TickerData
    cached_at: datetime
    cache_hit: bool

class QueueStatusResponse(BaseModel):
    queue_name: str
    size: int
    processing_rate: float
    health_status: str
```

### 4. Dependencies (`dependencies/`)
**FastAPI dependency injection for cache sessions and validation.**

#### Cache Dependencies (`cache.py`)
```python
async def get_ticker_cache() -> TickCache:
    """Provide configured TickCache instance for READ-ONLY operations."""
    pass

async def get_orders_cache() -> OrdersCache:
    """Provide configured OrdersCache instance for READ-ONLY operations."""
    pass
```

## 🔄 Data Flow Architecture

### Read-Only Cache Request Processing Flow
```
1. HTTP GET Request → FastAPI Router
2. Router → Pydantic Request Validation
3. Dependencies → fullon_cache Instance Creation (READ-ONLY)
4. Cache → Redis Query (READ-ONLY)
5. Redis → Cached Data Return (NO MODIFICATIONS)
6. Cache → Data Processing & Formatting
7. Router → Pydantic Response Validation
8. FastAPI → JSON HTTP Response
```

### Master API Integration Flow
```
1. Master API Startup
2. Import fullon_cache_api.get_all_routers()
3. Mount Routers with /api/v1/cache prefix
4. Compose with other fullon APIs
5. Single unified API documentation
6. Centralized logging and monitoring
```

## 🌐 Namespace Separation Benefits

### Perfect Integration with Fullon Ecosystem
```python
# Master API composition with zero namespace conflicts:
from fullon_orm_api import get_all_routers as get_orm_routers
from fullon_cache_api import get_all_routers as get_cache_routers  
from fullon_ohlcv_api import get_all_routers as get_ohlcv_routers

# Database operations
for router in get_orm_routers():
    app.include_router(router, prefix="/api/v1/orm", tags=["Database"])

# Cache operations (THIS PROJECT)
for router in get_cache_routers():
    app.include_router(router, prefix="/api/v1/cache", tags=["Cache"])

# Market data operations  
for router in get_ohlcv_routers():
    app.include_router(router, prefix="/api/v1/market", tags=["Market Data"])
```

### Clear Endpoint Separation
```
GET /api/v1/orm/trades/         # Database: Trade records (fullon_orm_api)
GET /api/v1/cache/trades/queue  # Redis: Trade processing queue (THIS PROJECT)
GET /api/v1/market/trades/      # Market: Historical trade data (fullon_ohlcv_api)
```

## 🔄 Redis Cache Integration

### fullon_cache Dependency Pattern
```python
# Standard cache usage pattern:
from fullon_cache import TickCache, OrdersCache, BotCache

async with TickCache() as cache:
    ticker = await cache.get_ticker("binance", "BTC/USDT")
    
async with OrdersCache() as cache:
    queue_size = await cache.get_queue_size("binance")
    
async with BotCache() as cache:
    bot_status = await cache.get_bot_status("bot_1")
```

### Cache Connection Management
- **Connection Pooling**: Automatic Redis connection optimization
- **Context Managers**: Proper resource cleanup guaranteed
- **Health Monitoring**: Built-in Redis connection health checks
- **Performance Metrics**: Cache hit/miss ratio tracking

## 🧪 Testing Architecture

### Test Organization
```
tests/
├── conftest.py              # Shared fixtures and Redis test setup
├── test_main.py             # Integration tests for main components
├── unit/                    # Isolated component testing
│   ├── test_gateway.py      # Gateway class unit tests
│   ├── test_routers.py      # Router endpoint unit tests
│   └── test_models.py       # Pydantic model validation tests
└── integration/             # End-to-end workflow testing  
    ├── test_api_workflows.py # Complete API operation flows
    └── test_redis_integration.py # fullon_cache integration tests
```

### Test-Driven Development (TDD)
- **Tests First**: Write tests before implementation
- **100% Coverage**: All code must have test coverage
- **`./run_test.py`**: Comprehensive test runner (must pass before commits)
- **Async Testing**: All tests use pytest-asyncio for async operations
- **Redis Testing**: Real Redis instance testing (no mocking where possible)

## 🚀 Development Workflow

### Setup and Development
```bash
# Project setup
make setup          # Install dependencies, setup pre-commit hooks

# Development server  
make dev           # Start development server with auto-reload

# Code quality
make format        # Format code with Black + Ruff
make lint         # Run linting checks
make test         # Run test suite
make check        # Run all quality checks

# Comprehensive validation
./run_test.py     # Full test suite (required before commits)
```

### Master API Integration Example
```python
# master_api/main.py
from fastapi import FastAPI
from fullon_cache_api import get_all_routers as cache_routers

app = FastAPI(title="Fullon Master API")

# Compose Cache API with perfect namespace separation
for router in cache_routers():
    app.include_router(router, prefix="/api/v1/cache", tags=["Cache"])

# Result: Clean API structure
# /api/v1/cache/tickers/{exchange}/{symbol}
# /api/v1/cache/orders/queue/status
# /api/v1/cache/bots/{bot_id}/status
# /docs - Combined API documentation
```

## 📈 Performance Considerations

### Cache-Specific Optimizations (READ-ONLY)
- **Connection Pooling**: Optimized Redis connections for read operations
- **Data Serialization**: Efficient JSON serialization for cached data
- **Query Optimization**: Fast Redis key-value lookups
- **Memory Management**: Efficient handling of large cached datasets

### Scaling Patterns (READ-ONLY)
- **Connection Pooling**: Redis connection optimization for read operations
- **Data Export**: Efficient cache data analysis operations
- **Monitoring**: Real-time cache performance metrics
- **Health Checks**: Comprehensive Redis connection monitoring

---

**This project structure enables a composable, high-performance cache API gateway that integrates seamlessly into the broader fullon ecosystem while maintaining perfect namespace separation and independence.** 🚀