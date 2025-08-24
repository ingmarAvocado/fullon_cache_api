# 🗄️ FULLON_ORM_EXPERT.md
**Complete Expert Manual for fullon_orm Library**

*Deep technical analysis and comprehensive usage guide for the async SQLAlchemy ORM library*

---

## 📋 Table of Contents
1. [Architecture Overview](#-architecture-overview)
2. [Core Models Deep Dive](#-core-models-deep-dive)
3. [Repository Pattern Mastery](#-repository-pattern-mastery)
4. [Session Management & Transactions](#-session-management--transactions)
5. [Caching Strategy](#-caching-strategy)
6. [Performance Optimization](#-performance-optimization)
7. [Advanced Usage Patterns](#-advanced-usage-patterns)
8. [Integration Strategies](#-integration-strategies)

---

## 🏗️ Architecture Overview

### Core Design Principles
```python
# fullon_orm follows these architectural patterns:
# 1. Async-first with uvloop optimization (2x performance boost)
# 2. Repository pattern for clean data access abstraction
# 3. Redis caching with automatic invalidation
# 4. Connection pooling with 20 connections, 10 overflow
# 5. Hierarchical user management with role-based access
```

### Package Structure
```
fullon_orm/
├── models/           # SQLAlchemy ORM models
│   ├── user.py       # User authentication & management
│   ├── bot.py        # Trading bot entities
│   ├── exchange.py   # Exchange account management
│   ├── order.py      # Order management
│   ├── trade.py      # Trade execution tracking
│   ├── symbol.py     # Trading pair definitions
│   ├── strategy.py   # Trading strategies
│   ├── feed.py       # Data feed configurations
│   └── ...
├── repositories/     # Repository pattern implementations
│   ├── base.py       # BaseRepository with common operations
│   ├── user.py       # UserRepository
│   ├── bot.py        # BotRepository
│   ├── symbol.py     # SymbolRepository (with caching)
│   └── ...
├── database.py       # Session management & connection pooling
├── cache.py          # Redis caching with dogpile.cache
├── types.py          # Custom PostgreSQL types
└── base.py           # SQLAlchemy declarative base
```

### Key Dependencies
```python
from fullon_orm import (
    # Session Management
    get_async_session,
    get_async_session_maker,
    get_engine,
    
    # Models (Direct Import Available)
    User, Bot, Exchange, Order, Trade, Symbol, Strategy, Feed,
    Balance, Position, DryTrade, BotExchange, BotLog,
    CatExchange, CatStrategy,  # Catalog/Template models
    
    # Repositories
    BaseRepository, UserRepository, BotRepository,
    ExchangeRepository, SymbolRepository, OrderRepository,
    TradeRepository, StrategyRepository,
    
    # Enums & Types
    RoleEnum,
    
    # Performance
    UVLoopManager, run_with_uvloop, setup_uvloop
)
```

---

## 🗂️ Core Models Deep Dive

### User Model - Central Authentication Entity
```python
from fullon_orm import User, RoleEnum

class User(Base):
    """
    Central user entity with hierarchical management capabilities.
    
    Key Features:
    - Role-based access (ADMIN, USER)
    - Hierarchical management (manager/managed_users)
    - Cascade delete protection for all owned entities
    - External system integration via external_id
    """
    
    # Primary Attributes
    uid: int                    # Auto-incrementing primary key
    mail: str                   # Unique email (max 80 chars)
    password: str               # SHA256 hash (fixed 64 chars)
    f2a: str                    # Two-factor auth code (max 16 chars)
    role: RoleEnum              # 'ADMIN' or 'USER'
    name: str                   # First name (max 50 chars)
    lastname: str               # Last name (max 50 chars)
    phone: str                  # Phone number (max 12 chars)
    id_num: str                 # Government ID (max 15 chars)
    note: str                   # Free-form notes
    manager: int                # Manager's uid (hierarchical structure)
    external_id: str            # External system identifier (unique)
    timestamp: datetime         # Account creation (UTC)
    active: bool                # Account status (default True)
    
    # Relationships (CASCADE DELETE)
    exchanges: List[Exchange]           # User's exchange accounts
    bots: List[Bot]                     # User's trading bots
    orders: List[Order]                 # All orders by user
    trades: List[Trade]                 # Live trades
    dry_trades: List[DryTrade]          # Simulated trades
    exchange_history: List[ExchangeHistory]  # Balance history
    
    # Hierarchical Management
    manager_user: User                  # The managing user object
    managed_users: List[User]           # Users managed by this user

# Usage Patterns:
async with get_async_session() as session:
    user_repo = UserRepository(session)
    
    # Create user with role conversion
    admin_user = await user_repo.create({
        "mail": "admin@company.com",
        "password": sha256_hash("password"),
        "role": "ADMIN",  # Automatically converted to RoleEnum.ADMIN
        "name": "Admin",
        "lastname": "User"
    })
    
    # Hierarchical management
    regular_user = await user_repo.create({
        "mail": "user@company.com",
        "manager": admin_user.uid,  # Set hierarchy
        "role": "USER"
    })
```

### Bot Model - Trading Automation Engine
```python
from fullon_orm import Bot, BotRepository

class Bot(Base):
    """
    Trading bot entity with strategy and exchange relationships.
    
    Key Features:
    - Live vs Dry-run mode toggle
    - Multiple strategy support
    - Multi-exchange trading capability
    - Comprehensive logging and simulation tracking
    """
    
    # Core Attributes
    bot_id: int                 # Auto-incrementing primary key
    uid: int                    # Owner user ID (CASCADE delete)
    name: str                   # Bot name (max 50 chars, unique per bot_id)
    dry_run: bool               # Simulation mode (default False)
    active: bool                # Currently running (default False)
    timestamp: datetime         # Creation timestamp (UTC)
    
    # Relationships
    user: User                          # Owner
    strategies: List[Strategy]          # Trading strategies
    bot_exchanges: List[BotExchange]    # Exchange accounts
    logs: List[BotLog]                  # Activity logs
    simulations: List[Simulation]       # Backtest results
    orders: List[Order]                 # Orders placed by bot
    dry_trades: List[DryTrade]          # Simulated trades

# Advanced Bot Repository Methods:
async with get_async_session() as session:
    bot_repo = BotRepository(session)
    
    # Complex bot creation with relationships
    bot_data = {
        "uid": user.uid,
        "name": "Scalping Bot V1",
        "dry_run": False,  # Live trading
        "active": True
    }
    bot = await bot_repo.add_bot(bot_data)
    
    # Associate exchanges with bot
    await bot_repo.add_exchange_to_bot(
        bot_id=bot.bot_id,
        exchange_data={
            "exchange_id": binance_exchange.ex_id,
            "trading_currency": "USDT"
        }
    )
    
    # Add data feeds to bot
    await bot_repo.add_feed_to_bot(
        bot_id=bot.bot_id,
        feed_data={
            "symbol_id": btc_usdt_symbol.id,
            "timeframe": "1m",
            "enabled": True
        }
    )
    
    # Get bot with full details (strategies, feeds, exchanges)
    full_bot = await bot_repo.get_bot_with_details(bot.bot_id)
    
    # Get trading currency for bot operations
    trading_currency = await bot_repo.get_trading_currency(
        bot_id=bot.bot_id,
        exchange_id=binance_exchange.ex_id
    )
    
    # Save bot activity log
    await bot_repo.save_bot_log({
        "bot_id": bot.bot_id,
        "message": "Strategy executed successfully",
        "timestamp": datetime.utcnow()
    })
```

### Exchange Model - User Exchange Accounts
```python
from fullon_orm import Exchange, ExchangeRepository

class Exchange(Base):
    """
    User exchange account with API credentials and configuration.
    
    Key Features:
    - Encrypted API credential storage
    - Exchange-specific parameter configuration
    - Balance and trading history tracking
    - Test/Sandbox mode support
    """
    
    # Core Attributes
    ex_id: int                  # Auto-incrementing primary key
    uid: int                    # Owner user ID
    cat_ex_id: int              # Exchange catalog ID (template)
    ex_name: str                # Exchange name (max 50 chars)
    account: str                # Account identifier (max 50 chars)
    api_key: str                # API key (encrypted, max 200 chars)
    api_secret: str             # API secret (encrypted, max 200 chars)
    passphrase: str             # API passphrase (encrypted, max 200 chars)
    sandbox: bool               # Test mode flag (default False)
    active: bool                # Account active status (default True)
    
    # Relationships
    user: User                          # Owner
    cat_exchange: CatExchange           # Exchange template/catalog
    bot_exchanges: List[BotExchange]    # Bots using this exchange
    orders: List[Order]                 # Orders placed on this exchange
    trades: List[Trade]                 # Trades executed
    balances: List[Balance]             # Account balances
    history: List[ExchangeHistory]      # Balance change history

# Exchange Repository with Caching:
async with get_async_session() as session:
    exchange_repo = ExchangeRepository(session)
    
    # Create exchange account
    exchange_data = {
        "uid": user.uid,
        "cat_ex_id": binance_catalog.cat_ex_id,
        "ex_name": "Binance Main",
        "account": "main_trading",
        "api_key": encrypt(api_key),
        "api_secret": encrypt(api_secret),
        "sandbox": False
    }
    exchange = await exchange_repo.create(exchange_data)
    
    # Get user exchanges (CACHED - 24 hour TTL)
    user_exchanges = await exchange_repo.get_exchanges_by_user(user.uid)
    
    # Get exchange parameters (CACHED)
    params = await exchange_repo.get_exchange_params(exchange.ex_id)
    
    # Get exchange catalog (CACHED)
    catalog = await exchange_repo.get_exchange_catalog()
    
    # Update exchange (invalidates cache)
    await exchange_repo.update(exchange.ex_id, {"active": False})
```

### Symbol Model - Trading Pair Management
```python
from fullon_orm import Symbol, SymbolRepository

class Symbol(Base):
    """
    Trading pair/symbol with exchange-specific configuration.
    
    Key Features:
    - Multi-exchange symbol support
    - Precision and decimal configuration
    - Volume and tick size management
    - Market status tracking
    """
    
    # Core Attributes
    id: int                     # Auto-incrementing primary key
    symbol: str                 # Trading pair (e.g., "BTC/USDT")
    exchange_id: int            # Exchange catalog ID
    ticker: str                 # Exchange-specific ticker
    decimals: int               # Price decimal places
    backtest: bool              # Available for backtesting
    
    # Relationships
    cat_exchange: CatExchange   # Exchange this symbol belongs to
    orders: List[Order]         # Orders for this symbol
    trades: List[Trade]         # Trades for this symbol
    ticks: List[Tick]           # Price tick data

# Symbol Repository - Heavily Cached:
async with get_async_session() as session:
    symbol_repo = SymbolRepository(session)
    
    # Get symbol by name and exchange (CACHED - 24 hour TTL)
    btc_usdt = await symbol_repo.get_by_symbol(
        symbol="BTC/USDT",
        cat_ex_id=binance_catalog.cat_ex_id
    )
    
    # Get all symbols for exchange (CACHED)
    binance_symbols = await symbol_repo.get_by_exchange_id(
        binance_catalog.cat_ex_id
    )
    
    # Get symbol ID for quick lookups (CACHED)
    symbol_id = await symbol_repo.get_id_by_symbol(
        "ETH/USDT", 
        binance_catalog.cat_ex_id
    )
    
    # Get decimal precision for price formatting (CACHED)
    decimals = await symbol_repo.get_decimals(btc_usdt.id)
    
    # Check if symbol exists (CACHED)
    exists = await symbol_repo.symbol_exists(
        "BTC/USDT", 
        binance_catalog.cat_ex_id
    )
    
    # Add new symbol (invalidates relevant caches)
    new_symbol = await symbol_repo.add_symbol({
        "symbol": "ADA/USDT",
        "exchange_id": binance_catalog.cat_ex_id,
        "ticker": "ADAUSDT",
        "decimals": 4,
        "backtest": True
    })
```

### Order & Trade Models - Execution Tracking
```python
from fullon_orm import Order, Trade, DryTrade, OrderRepository, TradeRepository

class Order(Base):
    """Order management with status tracking and execution details."""
    
    # Core Attributes
    order_id: int               # Auto-incrementing primary key
    ex_order_id: str            # Exchange-specific order ID
    bot_id: int                 # Bot that placed the order
    uid: int                    # User who owns the order
    ex_id: int                  # Exchange account used
    symbol_id: int              # Trading pair
    side: str                   # 'buy' or 'sell'
    size: float                 # Order quantity
    price: float                # Order price
    order_type: str             # 'market', 'limit', 'stop', etc.
    status: str                 # 'pending', 'filled', 'cancelled', etc.
    timestamp: datetime         # Order placement time
    
class Trade(Base):
    """Live trade execution with fees and settlement details."""
    
    # Core Attributes  
    trade_id: int               # Auto-incrementing primary key
    order_id: int               # Associated order
    ex_trade_id: str            # Exchange trade ID
    bot_id: int                 # Executing bot
    uid: int                    # Trade owner
    ex_id: int                  # Exchange account
    symbol_id: int              # Trading pair
    side: str                   # 'buy' or 'sell'
    size: float                 # Executed quantity
    price: float                # Execution price
    fee: float                  # Trading fee
    fee_currency: str           # Fee currency
    timestamp: datetime         # Execution time

class DryTrade(Base):
    """Simulated trade for backtesting and paper trading."""
    # Similar structure to Trade but for simulation mode

# Advanced Repository Usage:
async with get_async_session() as session:
    order_repo = OrderRepository(session)
    trade_repo = TradeRepository(session)
    
    # Create and track order
    order = await order_repo.create({
        "bot_id": scalping_bot.bot_id,
        "uid": user.uid,
        "ex_id": binance_exchange.ex_id,
        "symbol_id": btc_usdt.id,
        "side": "buy",
        "size": 0.001,
        "price": 45000.0,
        "order_type": "limit",
        "status": "pending"
    })
    
    # Update order status when filled
    await order_repo.update_status(
        order.order_id,
        "filled",
        ex_order_id="BINANCE123456"
    )
    
    # Create corresponding trade record
    trade = await trade_repo.create({
        "order_id": order.order_id,
        "ex_trade_id": "BINANCE_TRADE_789",
        "bot_id": order.bot_id,
        "uid": order.uid,
        "ex_id": order.ex_id,
        "symbol_id": order.symbol_id,
        "side": order.side,
        "size": order.size,
        "price": 45050.0,  # Actual execution price
        "fee": 0.45,       # Trading fee
        "fee_currency": "USDT"
    })
    
    # Get live trades with filtering
    live_trades = await trade_repo.get_live_trades(
        user_id=user.uid,
        symbol_id=btc_usdt.id,
        start_date=datetime.utcnow() - timedelta(days=7)
    )
    
    # Get dry run trades for backtesting analysis
    dry_trades = await trade_repo.get_dry_trades(
        bot_id=scalping_bot.bot_id,
        limit=1000
    )
```

---

## 🏛️ Repository Pattern Mastery

### BaseRepository - Foundation Pattern
```python
from fullon_orm.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession

class BaseRepository[T]:
    """
    Generic base repository with common CRUD operations.
    
    All specialized repositories inherit from this class.
    Provides transaction management, error handling, and basic operations.
    """
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
    
    # Core CRUD Operations
    async def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by primary key ID."""
        
    async def get_all(self) -> List[T]:
        """Get all entities of this type."""
        
    async def delete(self, id: int) -> None:
        """Delete entity by ID."""
        
    # Transaction Management
    async def commit(self) -> None:
        """Commit current transaction."""
        
    async def rollback(self) -> None:
        """Rollback current transaction."""
        
    async def flush(self) -> None:
        """Flush changes to database without commit."""
    
    # Error Handling
    def error_print(self, error: Exception, method: str, query: str = '') -> str:
        """Format error messages for consistent logging."""
        return f"Repository error in {method}: {error} | Query: {query}"

# Creating Custom Repositories:
class CustomRepository(BaseRepository[YourModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, YourModel)
    
    async def custom_query(self, param: str) -> List[YourModel]:
        """Add custom query methods specific to your model."""
        try:
            stmt = select(self.model).where(self.model.custom_field == param)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            error_msg = self.error_print(e, "custom_query", str(stmt))
            logger.error(error_msg)
            raise
```

### Advanced Repository Patterns

#### UserRepository - Authentication & Management
```python
from fullon_orm.repositories import UserRepository

class UserRepository(BaseRepository[User]):
    """
    Specialized user management with authentication and search capabilities.
    """
    
    # Authentication Methods
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address for login."""
        
    async def get_user_id(self, email: str) -> Optional[int]:
        """Quick user ID lookup by email."""
    
    # User Management
    async def add_user(self, user_data: dict) -> User:
        """Create new user with role validation."""
        
    async def modify_user(self, uid: int, updates: dict) -> User:
        """Update user information."""
        
    async def update_password(self, uid: int, new_password: str) -> None:
        """Update user password (expects pre-hashed)."""
        
    async def toggle_active(self, uid: int, active: bool) -> None:
        """Enable/disable user account."""
    
    # Search & Listing
    async def search(self, query: str) -> List[User]:
        """Search users by name, email, or other fields."""
        
    async def get_user_list(self, manager_id: Optional[int] = None) -> List[User]:
        """Get user list, optionally filtered by manager."""
        
    async def get_active_users(self) -> List[User]:
        """Get only active users."""

# Usage Patterns:
async with get_async_session() as session:
    user_repo = UserRepository(session)
    
    # Authentication flow
    user = await user_repo.get_by_email("user@example.com")
    if user and verify_password(password, user.password):
        if user.active:
            # User authenticated and active
            user_id = user.uid
            user_role = user.role  # RoleEnum.ADMIN or RoleEnum.USER
    
    # User management (ADMIN operations)
    new_user = await user_repo.add_user({
        "mail": "newuser@example.com",
        "password": hash_password("secure_password"),
        "role": "USER",
        "name": "John",
        "lastname": "Doe",
        "manager": admin_user.uid
    })
    
    # Search functionality
    search_results = await user_repo.search("john")  # Search by name
    active_users = await user_repo.get_active_users()
    managed_users = await user_repo.get_user_list(manager_id=admin_user.uid)
```

#### BotRepository - Complex Trading Bot Operations
```python
from fullon_orm.repositories import BotRepository

class BotRepository(BaseRepository[Bot]):
    """
    Advanced bot management with strategy, feed, and simulation support.
    """
    
    # Bot Lifecycle Management
    async def add_bot(self, bot_data: dict) -> Bot:
        """Create new bot with validation."""
        
    async def edit_bot(self, bot_id: int, updates: dict) -> Bot:
        """Update bot configuration."""
        
    async def delete_bot(self, bot_id: int) -> None:
        """Delete bot and cleanup relationships."""
    
    # Bot Configuration
    async def add_exchange_to_bot(self, bot_id: int, exchange_data: dict) -> BotExchange:
        """Associate exchange account with bot."""
        
    async def add_feed_to_bot(self, bot_id: int, feed_data: dict) -> Feed:
        """Add data feed to bot."""
        
    async def edit_feeds(self, bot_id: int, feeds_data: list) -> List[Feed]:
        """Update bot's data feeds configuration."""
    
    # Bot Querying
    async def get_bot_with_details(self, bot_id: int) -> Optional[Bot]:
        """Get bot with all relationships loaded (strategies, feeds, exchanges)."""
        
    async def get_bots_by_user(self, uid: int) -> List[Bot]:
        """Get all bots owned by user."""
        
    async def get_bot_list(self, uid: Optional[int] = None) -> List[Bot]:
        """Get bot list, optionally filtered by user."""
        
    async def get_bot_full_list(self) -> List[Bot]:
        """Get all bots with full details."""
    
    # Bot Analytics
    async def get_bot_params(self, bot_id: int) -> dict:
        """Get bot configuration parameters."""
        
    async def get_trading_currency(self, bot_id: int, exchange_id: int) -> Optional[str]:
        """Get trading currency for bot on specific exchange."""
        
    async def get_dry_margin(self, bot_id: int) -> float:
        """Get margin/balance for dry run bot."""
    
    # Logging & Monitoring
    async def save_bot_log(self, log_data: dict) -> BotLog:
        """Save bot activity log entry."""
        
    async def get_last_bot_log(self, bot_id: int) -> Optional[BotLog]:
        """Get most recent log entry for bot."""
        
    async def get_last_actions(self, bot_id: int, limit: int = 10) -> List[BotLog]:
        """Get recent bot actions/logs."""
    
    # Simulation Management
    async def save_simulation(self, simulation_data: dict) -> Simulation:
        """Save backtest/simulation results."""
        
    async def load_simulation(self, simulation_id: int) -> Optional[Simulation]:
        """Load simulation results."""
        
    async def load_simulations_catalog(self, bot_id: int) -> List[Simulation]:
        """Get all simulations for bot."""

# Advanced Bot Operations:
async with get_async_session() as session:
    bot_repo = BotRepository(session)
    
    # Create sophisticated trading bot
    bot = await bot_repo.add_bot({
        "uid": user.uid,
        "name": "Multi-Exchange Arbitrage Bot",
        "dry_run": False,
        "active": True
    })
    
    # Configure bot for multiple exchanges
    binance_config = await bot_repo.add_exchange_to_bot(bot.bot_id, {
        "exchange_id": binance_exchange.ex_id,
        "trading_currency": "USDT",
        "max_exposure": 10000.0
    })
    
    coinbase_config = await bot_repo.add_exchange_to_bot(bot.bot_id, {
        "exchange_id": coinbase_exchange.ex_id,
        "trading_currency": "USD",
        "max_exposure": 10000.0
    })
    
    # Add multiple data feeds
    feeds = [
        {"symbol_id": btc_usdt.id, "timeframe": "1m", "enabled": True},
        {"symbol_id": eth_usdt.id, "timeframe": "1m", "enabled": True},
        {"symbol_id": btc_usdt.id, "timeframe": "5m", "enabled": True}
    ]
    
    for feed_data in feeds:
        await bot_repo.add_feed_to_bot(bot.bot_id, feed_data)
    
    # Monitor bot activity
    recent_actions = await bot_repo.get_last_actions(bot.bot_id, limit=50)
    trading_currency = await bot_repo.get_trading_currency(
        bot.bot_id, 
        binance_exchange.ex_id
    )
    
    # Simulation and backtesting
    simulation_result = await bot_repo.save_simulation({
        "bot_id": bot.bot_id,
        "name": "Backtest 2024-01",
        "start_date": datetime(2024, 1, 1),
        "end_date": datetime(2024, 1, 31),
        "initial_balance": 10000.0,
        "final_balance": 11250.0,
        "total_trades": 156,
        "win_rate": 0.67,
        "sharpe_ratio": 1.43
    })
```

---

## 📊 Session Management & Transactions

### Connection Pool Configuration
```python
from fullon_orm import get_engine, get_async_session_maker, get_async_session

# Engine Configuration (automatically optimized)
"""
Default connection pool settings:
- pool_size=20 (concurrent connections)
- max_overflow=10 (additional connections under load)
- pool_recycle=3600 (recycle connections hourly)
- pool_pre_ping=True (connection health checks)
"""

# Session Management Patterns:

# Pattern 1: Context Manager (Recommended)
async with get_async_session() as session:
    user_repo = UserRepository(session)
    bot_repo = BotRepository(session)
    
    # Multiple operations in single transaction
    user = await user_repo.create(user_data)
    bot = await bot_repo.add_bot({"uid": user.uid, "name": "Test Bot"})
    
    # Automatic commit on success, rollback on exception
    await session.commit()

# Pattern 2: Manual Session Management
session_maker = get_async_session_maker()
async with session_maker() as session:
    try:
        # Database operations
        await session.commit()
    except Exception:
        await session.rollback()
        raise

# Pattern 3: Repository-Level Transaction Control
async with get_async_session() as session:
    user_repo = UserRepository(session)
    
    try:
        user = await user_repo.add_user(user_data)
        await user_repo.commit()
    except Exception as e:
        await user_repo.rollback()
        raise
```

### Advanced Transaction Patterns
```python
# Complex Multi-Repository Transactions
async def create_complete_trading_setup(user_data: dict, bot_data: dict, 
                                      exchange_data: dict) -> dict:
    """Create user, bot, and exchange in single transaction."""
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        bot_repo = BotRepository(session)
        exchange_repo = ExchangeRepository(session)
        
        try:
            # Step 1: Create user
            user = await user_repo.add_user(user_data)
            await session.flush()  # Get user.uid without committing
            
            # Step 2: Create exchange account
            exchange_data["uid"] = user.uid
            exchange = await exchange_repo.create(exchange_data)
            await session.flush()
            
            # Step 3: Create bot
            bot_data["uid"] = user.uid
            bot = await bot_repo.add_bot(bot_data)
            await session.flush()
            
            # Step 4: Link bot to exchange
            await bot_repo.add_exchange_to_bot(bot.bot_id, {
                "exchange_id": exchange.ex_id,
                "trading_currency": "USDT"
            })
            
            # Commit all changes atomically
            await session.commit()
            
            return {
                "user": user,
                "bot": bot,
                "exchange": exchange,
                "success": True
            }
            
        except Exception as e:
            await session.rollback()
            return {
                "error": str(e),
                "success": False
            }

# Batch Operations with Transaction Control
async def bulk_create_symbols(symbols_data: List[dict]) -> dict:
    """Create multiple symbols efficiently."""
    
    async with get_async_session() as session:
        symbol_repo = SymbolRepository(session)
        
        created_symbols = []
        failed_symbols = []
        
        try:
            for symbol_data in symbols_data:
                try:
                    symbol = await symbol_repo.add_symbol(symbol_data)
                    created_symbols.append(symbol)
                    
                    # Flush every 10 symbols to avoid memory buildup
                    if len(created_symbols) % 10 == 0:
                        await session.flush()
                        
                except Exception as e:
                    failed_symbols.append({
                        "data": symbol_data,
                        "error": str(e)
                    })
            
            # Commit all successful creations
            await session.commit()
            
            return {
                "created": len(created_symbols),
                "failed": len(failed_symbols),
                "failures": failed_symbols
            }
            
        except Exception as e:
            await session.rollback()
            raise
```

---

## 🚀 Caching Strategy

### Redis Cache Integration
```python
from fullon_orm.cache import cache_manager

"""
Fullon ORM uses dogpile.cache with Redis backend:
- Default TTL: 24 hours
- Automatic invalidation on CUD operations
- Graceful fallback to database when Redis unavailable
- Method-level cache decorators
"""

# Cache Configuration (via environment):
"""
CACHE_HOST=localhost
CACHE_PORT=6379
CACHE_DB=0          # Production: 0, Testing: 1
"""

# Cached Repository Methods:
class SymbolRepository(BaseRepository[Symbol]):
    """SymbolRepository with extensive caching."""
    
    @cache_manager.cache_on_symbol_methods
    async def get_by_symbol(self, symbol: str, cat_ex_id: int) -> Optional[Symbol]:
        """Cache key: symbol:{symbol}:{cat_ex_id}"""
        
    @cache_manager.cache_on_symbol_methods  
    async def get_by_exchange_id(self, cat_ex_id: int) -> List[Symbol]:
        """Cache key: symbols:exchange:{cat_ex_id}"""
        
    @cache_manager.cache_on_symbol_methods
    async def get_decimals(self, symbol_id: int) -> int:
        """Cache key: symbol:decimals:{symbol_id}"""
    
    # Cache invalidation on writes
    async def add_symbol(self, symbol_data: dict) -> Symbol:
        symbol = await self._create_symbol(symbol_data)
        # Automatically invalidates related caches
        cache_manager.invalidate_symbol_caches(symbol.exchange_id)
        return symbol

class ExchangeRepository(BaseRepository[Exchange]):
    """ExchangeRepository with user-specific caching."""
    
    @cache_manager.cache_on_exchange_methods
    async def get_exchanges_by_user(self, uid: int) -> List[Exchange]:
        """Cache key: user:exchanges:{uid}"""
        
    @cache_manager.cache_on_exchange_methods
    async def get_exchange_params(self, ex_id: int) -> dict:
        """Cache key: exchange:params:{ex_id}"""
        
    @cache_manager.cache_on_exchange_methods
    async def get_exchange_catalog(self) -> List[CatExchange]:
        """Cache key: exchange:catalog"""
    
    # Cache invalidation
    async def update(self, ex_id: int, updates: dict) -> Exchange:
        exchange = await self._update_exchange(ex_id, updates)
        cache_manager.invalidate_exchange_caches(exchange.uid)
        return exchange
```

### Custom Caching Patterns
```python
from fullon_orm.cache import cache_manager

# Manual Cache Management
async def get_user_trading_summary(uid: int) -> dict:
    """Get comprehensive user trading data with manual caching."""
    
    cache_key = f"user:trading_summary:{uid}"
    
    # Try cache first
    cached_data = await cache_manager.redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Generate data if not cached
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        bot_repo = BotRepository(session)
        trade_repo = TradeRepository(session)
        
        user = await user_repo.get_by_id(uid)
        bots = await bot_repo.get_bots_by_user(uid)
        recent_trades = await trade_repo.get_trades_by_user(uid, limit=100)
        
        summary = {
            "user": user.to_dict(),
            "total_bots": len(bots),
            "active_bots": len([b for b in bots if b.active]),
            "recent_trades_count": len(recent_trades),
            "total_volume": sum(t.size * t.price for t in recent_trades),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    # Cache for 1 hour
    await cache_manager.redis_client.setex(
        cache_key, 
        3600, 
        json.dumps(summary, default=str)
    )
    
    return summary

# Cache Warming Strategies
async def warm_symbol_cache(exchange_id: int) -> None:
    """Pre-populate symbol cache for exchange."""
    
    async with get_async_session() as session:
        symbol_repo = SymbolRepository(session)
        
        # This will populate cache
        symbols = await symbol_repo.get_by_exchange_id(exchange_id)
        
        # Pre-cache individual symbol lookups
        for symbol in symbols:
            await symbol_repo.get_by_symbol(symbol.symbol, symbol.exchange_id)
            await symbol_repo.get_decimals(symbol.id)
    
    logger.info(f"Warmed cache for {len(symbols)} symbols on exchange {exchange_id}")

# Cache Monitoring and Health
async def get_cache_health() -> dict:
    """Monitor cache performance and health."""
    
    try:
        # Test Redis connectivity
        await cache_manager.redis_client.ping()
        redis_status = "healthy"
        
        # Get cache statistics
        info = await cache_manager.redis_client.info()
        
        return {
            "redis_status": redis_status,
            "connected_clients": info.get("connected_clients", 0),
            "used_memory": info.get("used_memory_human", "unknown"),
            "cache_hits": info.get("keyspace_hits", 0),
            "cache_misses": info.get("keyspace_misses", 0),
            "uptime": info.get("uptime_in_seconds", 0)
        }
        
    except Exception as e:
        return {
            "redis_status": "unhealthy",
            "error": str(e)
        }
```

---

## ⚡ Performance Optimization

### UVLoop Integration
```python
from fullon_orm import run_with_uvloop, setup_uvloop, UVLoopManager

# Method 1: Automatic UVLoop Setup (Recommended)
@run_with_uvloop
async def main():
    """Automatically configures uvloop for 2x async performance."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        users = await user_repo.get_all()
    return users

# Method 2: Manual UVLoop Setup
async def manual_uvloop_setup():
    setup_uvloop()  # Configure uvloop policy
    
    # Your async operations here
    async with get_async_session() as session:
        # Database operations will benefit from uvloop
        pass

# Method 3: Context Manager
async def context_manager_uvloop():
    async with UVLoopManager():
        # All operations within this context use uvloop
        async with get_async_session() as session:
            # High-performance database operations
            pass
```

### Query Optimization Patterns
```python
# Efficient Relationship Loading
async def get_user_with_bots_optimized(uid: int) -> Optional[User]:
    """Load user with bots in single query using joinedload."""
    
    async with get_async_session() as session:
        stmt = (
            select(User)
            .options(joinedload(User.bots))
            .where(User.uid == uid)
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

# Batch Loading for Multiple Entities
async def get_bots_with_details_batch(bot_ids: List[int]) -> List[Bot]:
    """Efficiently load multiple bots with relationships."""
    
    async with get_async_session() as session:
        stmt = (
            select(Bot)
            .options(
                joinedload(Bot.user),
                joinedload(Bot.strategies),
                joinedload(Bot.bot_exchanges)
            )
            .where(Bot.bot_id.in_(bot_ids))
        )
        result = await session.execute(stmt)
        return result.unique().scalars().all()

# Pagination for Large Results
async def get_trades_paginated(user_id: int, page: int = 1, 
                             page_size: int = 100) -> dict:
    """Paginate large trade result sets."""
    
    async with get_async_session() as session:
        # Count total trades
        count_stmt = (
            select(func.count(Trade.trade_id))
            .where(Trade.uid == user_id)
        )
        total_result = await session.execute(count_stmt)
        total_trades = total_result.scalar()
        
        # Get paginated results
        offset = (page - 1) * page_size
        stmt = (
            select(Trade)
            .where(Trade.uid == user_id)
            .order_by(Trade.timestamp.desc())
            .limit(page_size)
            .offset(offset)
        )
        result = await session.execute(stmt)
        trades = result.scalars().all()
        
        return {
            "trades": trades,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_trades,
                "pages": math.ceil(total_trades / page_size)
            }
        }

# Aggregation Queries
async def get_user_trading_stats(uid: int) -> dict:
    """Get aggregated trading statistics efficiently."""
    
    async with get_async_session() as session:
        # Use single query for multiple aggregations
        stmt = (
            select(
                func.count(Trade.trade_id).label('total_trades'),
                func.sum(Trade.size * Trade.price).label('total_volume'),
                func.avg(Trade.price).label('avg_price'),
                func.sum(case(
                    (Trade.side == 'buy', Trade.size * Trade.price),
                    else_=0
                )).label('buy_volume'),
                func.sum(case(
                    (Trade.side == 'sell', Trade.size * Trade.price),
                    else_=0
                )).label('sell_volume')
            )
            .where(Trade.uid == uid)
        )
        
        result = await session.execute(stmt)
        row = result.first()
        
        return {
            "total_trades": row.total_trades or 0,
            "total_volume": float(row.total_volume or 0),
            "average_price": float(row.avg_price or 0),
            "buy_volume": float(row.buy_volume or 0),
            "sell_volume": float(row.sell_volume or 0),
            "net_volume": float((row.buy_volume or 0) - (row.sell_volume or 0))
        }
```

### Connection Pool Optimization
```python
# Production Database Configuration
from fullon_orm.database import init_db

# Custom engine configuration for high-load scenarios
async def configure_high_performance_engine():
    """Configure database engine for high-performance scenarios."""
    
    database_url = create_database_url()
    
    engine = create_async_engine(
        database_url,
        # Connection pool settings
        pool_size=30,           # Increase for high concurrency
        max_overflow=20,        # Additional connections under peak load
        pool_recycle=1800,      # Recycle connections every 30 minutes
        pool_pre_ping=True,     # Health check connections
        
        # Performance settings
        pool_reset_on_return='commit',  # Clean connections
        connect_args={
            "command_timeout": 60,      # Query timeout
            "server_settings": {
                "application_name": "fullon_cache_api",
                "jit": "off"            # Disable JIT for consistent performance
            }
        },
        
        # Logging (disable in production)
        echo=False,
        echo_pool=False
    )
    
    return engine

# Connection Health Monitoring
async def monitor_connection_health():
    """Monitor database connection pool health."""
    
    engine = get_engine()
    pool = engine.pool
    
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid()
    }
```

---

## 🎯 Advanced Usage Patterns

### Model Serialization & Dictionary Conversion
```python
# All fullon_orm models support dictionary conversion
from fullon_orm import User, Bot, Exchange

async with get_async_session() as session:
    user_repo = UserRepository(session)
    
    # Create from dictionary
    user_data = {
        "mail": "api@example.com",
        "password": hash_password("secure"),
        "role": "USER",
        "name": "API",
        "lastname": "User"
    }
    
    # Method 1: Repository create (recommended)
    user = await user_repo.add_user(user_data)
    
    # Method 2: Direct model instantiation
    user = User.from_dict(user_data)  # If method exists
    
    # Convert to dictionary for API responses
    user_dict = user.to_dict()
    # Result: JSON-serializable dictionary with all fields
    
    # Use in API responses
    return {
        "success": True,
        "user": user_dict,
        "created_at": user.timestamp.isoformat()
    }

# Batch serialization for API endpoints
async def get_users_for_api(manager_id: Optional[int] = None) -> List[dict]:
    """Get users formatted for API consumption."""
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        
        if manager_id:
            users = await user_repo.get_user_list(manager_id=manager_id)
        else:
            users = await user_repo.get_active_users()
        
        # Convert all to dictionaries
        return [user.to_dict() for user in users]
```

### Custom Types and PostgreSQL Features
```python
from fullon_orm.types import Double, double_precision, serial_primary_key

# Using Custom PostgreSQL Types
class CustomModel(Base):
    __tablename__ = "custom_table"
    
    # Serial primary key (auto-incrementing)
    id = serial_primary_key()
    
    # Double precision for financial data (no floating point errors)
    price = double_precision()
    volume = double_precision()
    
    # Nullable double precision
    optional_value = double_precision_nullable()

# Advanced PostgreSQL Features
from sqlalchemy import text

async def use_postgresql_features():
    """Demonstrate PostgreSQL-specific features."""
    
    async with get_async_session() as session:
        # Use PostgreSQL-specific aggregates
        stmt = text("""
            SELECT 
                symbol_id,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY price) as median_price,
                stddev(price) as price_volatility
            FROM trades 
            WHERE timestamp >= :start_date
            GROUP BY symbol_id
        """)
        
        result = await session.execute(stmt, {
            "start_date": datetime.utcnow() - timedelta(days=30)
        })
        
        return [dict(row) for row in result]

# UUID Support for External IDs
from sqlalchemy.dialects.postgresql import UUID
import uuid

class ModelWithUUID(Base):
    __tablename__ = "uuid_model"
    
    id = mapped_column(Integer, primary_key=True)
    external_uuid = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    
    # Use UUID for lookups
    @classmethod
    async def get_by_uuid(cls, session: AsyncSession, uuid_value: uuid.UUID):
        stmt = select(cls).where(cls.external_uuid == uuid_value)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
```

### Error Handling & Recovery Patterns
```python
from sqlalchemy.exc import IntegrityError, DisconnectionError
from asyncio import sleep

# Robust Error Handling
async def create_user_with_retry(user_data: dict, max_retries: int = 3) -> dict:
    """Create user with automatic retry on transient errors."""
    
    for attempt in range(max_retries):
        try:
            async with get_async_session() as session:
                user_repo = UserRepository(session)
                
                user = await user_repo.add_user(user_data)
                await session.commit()
                
                return {
                    "success": True,
                    "user": user.to_dict(),
                    "attempts": attempt + 1
                }
                
        except IntegrityError as e:
            # Handle unique constraint violations (don't retry)
            if "unique constraint" in str(e).lower():
                return {
                    "success": False,
                    "error": "Email already exists",
                    "type": "integrity_error"
                }
            raise
            
        except DisconnectionError as e:
            # Handle database connection errors (retry)
            if attempt < max_retries - 1:
                await sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "type": "connection_error",
                    "attempts": max_retries
                }
                
        except Exception as e:
            # Handle unexpected errors
            return {
                "success": False,
                "error": str(e),
                "type": "unknown_error",
                "attempts": attempt + 1
            }
    
    return {"success": False, "error": "Max retries exceeded"}

# Graceful Degradation with Cache Fallback
async def get_symbols_with_fallback(exchange_id: int) -> List[Symbol]:
    """Get symbols with graceful degradation if database unavailable."""
    
    try:
        # Try primary database query
        async with get_async_session() as session:
            symbol_repo = SymbolRepository(session)
            return await symbol_repo.get_by_exchange_id(exchange_id)
            
    except Exception as db_error:
        logger.warning(f"Database error: {db_error}, trying cache fallback")
        
        try:
            # Fallback to direct cache access
            cache_key = f"symbols:exchange:{exchange_id}"
            cached_data = await cache_manager.redis_client.get(cache_key)
            
            if cached_data:
                symbols_data = json.loads(cached_data)
                return [Symbol.from_dict(data) for data in symbols_data]
                
        except Exception as cache_error:
            logger.error(f"Cache fallback failed: {cache_error}")
        
        # Final fallback to empty list with logging
        logger.error(f"All fallbacks failed for exchange {exchange_id}")
        return []

# Transaction Rollback with Cleanup
async def complex_operation_with_cleanup(data: dict) -> dict:
    """Demonstrate complex transaction with cleanup on failure."""
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        bot_repo = BotRepository(session)
        exchange_repo = ExchangeRepository(session)
        
        created_entities = []
        
        try:
            # Step 1: Create user
            user = await user_repo.add_user(data["user"])
            created_entities.append(("user", user.uid))
            await session.flush()
            
            # Step 2: Create exchange
            exchange_data = data["exchange"]
            exchange_data["uid"] = user.uid
            exchange = await exchange_repo.create(exchange_data)
            created_entities.append(("exchange", exchange.ex_id))
            await session.flush()
            
            # Step 3: Create bot
            bot_data = data["bot"]
            bot_data["uid"] = user.uid
            bot = await bot_repo.add_bot(bot_data)
            created_entities.append(("bot", bot.bot_id))
            
            # Simulate potential failure point
            if data.get("simulate_error"):
                raise ValueError("Simulated error for testing")
            
            await session.commit()
            
            return {
                "success": True,
                "entities": created_entities,
                "user_id": user.uid
            }
            
        except Exception as e:
            await session.rollback()
            
            # Log what was attempted
            logger.error(f"Complex operation failed: {e}")
            logger.info(f"Rolled back entities: {created_entities}")
            
            return {
                "success": False,
                "error": str(e),
                "attempted_entities": created_entities
            }
```

---

## 🔌 Integration Strategies

### FastAPI Integration Patterns
```python
from fastapi import FastAPI, HTTPException, Depends
from fullon_orm import get_async_session, UserRepository, BotRepository

app = FastAPI()

# Dependency Injection Pattern
async def get_db_session():
    """FastAPI dependency for database sessions."""
    async with get_async_session() as session:
        yield session

async def get_user_repo(session = Depends(get_db_session)):
    """FastAPI dependency for UserRepository."""
    return UserRepository(session)

# API Endpoints with Repository Injection
@app.post("/users/")
async def create_user(
    user_data: UserCreateRequest,
    user_repo: UserRepository = Depends(get_user_repo)
):
    """Create new user via API."""
    try:
        user = await user_repo.add_user(user_data.dict())
        await user_repo.commit()
        
        return {
            "success": True,
            "user": user.to_dict()
        }
    except Exception as e:
        await user_repo.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}/bots")
async def get_user_bots(
    user_id: int,
    session = Depends(get_db_session)
):
    """Get user's bots with session dependency."""
    bot_repo = BotRepository(session)
    
    bots = await bot_repo.get_bots_by_user(user_id)
    return {
        "user_id": user_id,
        "bots": [bot.to_dict() for bot in bots]
    }

# Authentication Middleware Integration
from fastapi import Request, HTTPException

async def verify_user_token(request: Request, session = Depends(get_db_session)):
    """Verify JWT token and get user from database."""
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    try:
        # Decode JWT token (implement your JWT logic)
        user_email = decode_jwt_token(token)
        
        user_repo = UserRepository(session)
        user = await user_repo.get_by_email(user_email)
        
        if not user or not user.active:
            raise HTTPException(status_code=401, detail="Invalid user")
        
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/protected-endpoint")
async def protected_endpoint(current_user: User = Depends(verify_user_token)):
    """Example protected endpoint."""
    return {
        "message": "Access granted",
        "user": current_user.to_dict()
    }
```

### Background Task Integration
```python
import asyncio
from typing import List

# Background Data Processing
async def process_trades_background():
    """Background task to process pending trades."""
    
    while True:
        try:
            async with get_async_session() as session:
                trade_repo = TradeRepository(session)
                order_repo = OrderRepository(session)
                
                # Get pending orders
                pending_orders = await order_repo.get_pending_orders(limit=100)
                
                for order in pending_orders:
                    # Simulate trade processing
                    if should_fill_order(order):
                        trade = await trade_repo.create({
                            "order_id": order.order_id,
                            "bot_id": order.bot_id,
                            "uid": order.uid,
                            "ex_id": order.ex_id,
                            "symbol_id": order.symbol_id,
                            "side": order.side,
                            "size": order.size,
                            "price": get_market_price(order.symbol_id),
                            "fee": calculate_fee(order),
                            "fee_currency": "USDT"
                        })
                        
                        # Update order status
                        await order_repo.update_status(order.order_id, "filled")
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"Background trade processing error: {e}")
        
        # Wait before next iteration
        await asyncio.sleep(10)

# Batch Data Synchronization
async def sync_exchange_data(exchange_id: int) -> dict:
    """Synchronize data from external exchange API."""
    
    async with get_async_session() as session:
        symbol_repo = SymbolRepository(session)
        exchange_repo = ExchangeRepository(session)
        
        # Get exchange configuration
        exchange = await exchange_repo.get_by_id(exchange_id)
        if not exchange:
            return {"error": "Exchange not found"}
        
        # Fetch data from external API
        external_symbols = await fetch_exchange_symbols(exchange)
        
        sync_results = {
            "created": 0,
            "updated": 0,
            "errors": []
        }
        
        for ext_symbol in external_symbols:
            try:
                # Check if symbol exists
                existing = await symbol_repo.get_by_symbol(
                    ext_symbol["symbol"], 
                    exchange.cat_ex_id
                )
                
                if existing:
                    # Update existing symbol
                    await symbol_repo.update_symbol(existing.id, ext_symbol)
                    sync_results["updated"] += 1
                else:
                    # Create new symbol
                    ext_symbol["exchange_id"] = exchange.cat_ex_id
                    await symbol_repo.add_symbol(ext_symbol)
                    sync_results["created"] += 1
                    
            except Exception as e:
                sync_results["errors"].append({
                    "symbol": ext_symbol.get("symbol", "unknown"),
                    "error": str(e)
                })
        
        await session.commit()
        return sync_results

# Scheduled Tasks with APScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', minutes=5)
async def cache_warming_job():
    """Warm frequently accessed caches every 5 minutes."""
    
    try:
        # Warm symbol caches for active exchanges
        async with get_async_session() as session:
            exchange_repo = ExchangeRepository(session)
            active_exchanges = await exchange_repo.get_active_exchanges()
            
            for exchange in active_exchanges:
                await warm_symbol_cache(exchange.cat_ex_id)
        
        logger.info(f"Cache warming completed for {len(active_exchanges)} exchanges")
        
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")

@scheduler.scheduled_job('cron', hour=2, minute=0)  # Daily at 2 AM
async def daily_cleanup_job():
    """Daily cleanup of old data."""
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        async with get_async_session() as session:
            # Clean old logs
            stmt = delete(BotLog).where(BotLog.timestamp < cutoff_date)
            result = await session.execute(stmt)
            
            # Clean old simulations
            stmt = delete(Simulation).where(Simulation.timestamp < cutoff_date)
            result2 = await session.execute(stmt)
            
            await session.commit()
            
            logger.info(f"Daily cleanup: removed {result.rowcount} logs, {result2.rowcount} simulations")
            
    except Exception as e:
        logger.error(f"Daily cleanup failed: {e}")

# Start scheduler
scheduler.start()
```

### Monitoring & Health Checks
```python
# Database Health Monitoring
async def check_database_health() -> dict:
    """Comprehensive database health check."""
    
    health_status = {
        "database": "unknown",
        "cache": "unknown",
        "connection_pool": {},
        "query_performance": {},
        "errors": []
    }
    
    try:
        # Test database connectivity
        start_time = time.time()
        async with get_async_session() as session:
            await session.execute(text("SELECT 1"))
        
        db_latency = (time.time() - start_time) * 1000
        health_status["database"] = "healthy"
        health_status["query_performance"]["db_latency_ms"] = db_latency
        
    except Exception as e:
        health_status["database"] = "unhealthy"
        health_status["errors"].append(f"Database: {str(e)}")
    
    try:
        # Test cache connectivity
        start_time = time.time()
        await cache_manager.redis_client.ping()
        
        cache_latency = (time.time() - start_time) * 1000
        health_status["cache"] = "healthy"
        health_status["query_performance"]["cache_latency_ms"] = cache_latency
        
    except Exception as e:
        health_status["cache"] = "unhealthy"  
        health_status["errors"].append(f"Cache: {str(e)}")
    
    # Get connection pool statistics
    try:
        pool_stats = await monitor_connection_health()
        health_status["connection_pool"] = pool_stats
    except Exception as e:
        health_status["errors"].append(f"Connection pool: {str(e)}")
    
    return health_status

# Performance Metrics Collection
async def collect_performance_metrics(time_window: int = 300) -> dict:
    """Collect database performance metrics over time window."""
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(seconds=time_window)
    
    async with get_async_session() as session:
        # Query performance by table
        table_metrics = {}
        
        for table_name in ["users", "bots", "orders", "trades"]:
            try:
                # Count operations in time window
                if table_name == "users":
                    count_stmt = select(func.count(User.uid)).where(
                        User.timestamp >= start_time
                    )
                elif table_name == "bots":
                    count_stmt = select(func.count(Bot.bot_id)).where(
                        Bot.timestamp >= start_time
                    )
                # ... add other tables
                
                result = await session.execute(count_stmt)
                count = result.scalar()
                
                table_metrics[table_name] = {
                    "new_records": count,
                    "rate_per_minute": count / (time_window / 60)
                }
                
            except Exception as e:
                table_metrics[table_name] = {"error": str(e)}
    
    return {
        "time_window_seconds": time_window,
        "table_metrics": table_metrics,
        "collected_at": end_time.isoformat()
    }
```

---

## 🎓 Summary & Best Practices

### Key Takeaways
1. **Async-First Architecture**: Always use async patterns with uvloop for maximum performance
2. **Repository Pattern**: Use repositories for clean abstraction and testability
3. **Caching Strategy**: Leverage built-in Redis caching for SymbolRepository and ExchangeRepository
4. **Transaction Management**: Use context managers for automatic commit/rollback
5. **Error Handling**: Implement robust error handling with retry logic for transient errors
6. **Performance**: Optimize queries with proper joins and pagination for large datasets
7. **Monitoring**: Implement health checks and performance monitoring

### Production Checklist
- [ ] Configure connection pooling for expected load
- [ ] Set up Redis caching with appropriate TTL values
- [ ] Implement proper error handling and logging
- [ ] Add health check endpoints
- [ ] Configure uvloop for performance
- [ ] Set up monitoring and alerting
- [ ] Implement backup and recovery procedures
- [ ] Use environment variables for all configuration
- [ ] Set up database migrations with Alembic
- [ ] Implement proper security measures for API credentials

### Common Patterns
```python
# Standard Repository Usage Pattern
async def standard_operation(data: dict) -> dict:
    async with get_async_session() as session:
        repo = SomeRepository(session)
        
        try:
            result = await repo.some_operation(data)
            await session.commit()
            return {"success": True, "data": result.to_dict()}
        except Exception as e:
            await session.rollback()
            return {"success": False, "error": str(e)}

# Cached Query Pattern
@cache_manager.cache_on_symbol_methods
async def cached_query(self, param: str) -> List[Model]:
    # Query implementation
    pass

# Performance-Optimized Query Pattern
async def optimized_query() -> List[Model]:
    async with get_async_session() as session:
        stmt = (
            select(Model)
            .options(joinedload(Model.relationship))
            .where(Model.field == value)
            .limit(100)
        )
        result = await session.execute(stmt)
        return result.unique().scalars().all()
```

This expert manual provides comprehensive coverage of fullon_orm for advanced usage in production trading systems. Use it as a reference for implementing robust, high-performance database operations in your fullon_cache_api.

---

**📚 Created for fullon_cache_api integration - Complete ORM mastery for trading system development**