"""
Account cache router for READ-ONLY account data API.

Provides secure access to cached account information including positions, 
balances, and account metadata with proper user data handling and validation.
"""

import time
from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from fullon_log import get_component_logger

from ..dependencies.cache import get_account_cache
from ..exceptions import (
    CacheNotFoundError,
    CacheServiceUnavailableError,
    CacheTimeoutError,
)
from ..models.responses import (
    AccountPositionsResponse,
    AccountBalancesResponse,
    AccountStatusResponse,
    AccountSummaryResponse,
    HealthResponse,
    Position,
    Balance,
)
from .base import validate_user_id, handle_cache_error, log_cache_operation
from .exceptions import InvalidParameterError

logger = get_component_logger("fullon.api.cache.accounts")
router = APIRouter(prefix="/accounts", tags=["Account Cache"])


@router.get("/{user_id}/positions", response_model=AccountPositionsResponse)
async def get_user_positions(
    user_id: str, cache_session: Any = Depends(get_account_cache)
) -> AccountPositionsResponse:
    """
    Get user account positions from cache.

    Retrieves all positions for the specified user from the account cache,
    including position details like size, PnL, and margin information.

    Args:
        user_id: User identifier
        cache_session: Account cache dependency injection

    Returns:
        AccountPositionsResponse with user positions

    Raises:
        HTTPException: 404 if user not found, 422 for validation errors,
                      503 for cache service issues, 408 for timeouts
    """
    # Validate and sanitize user ID
    try:
        user_id = validate_user_id(user_id)
    except InvalidParameterError as e:
        logger.warning("Invalid user ID format", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    async with log_cache_operation("get_user_positions", user_id=user_id):
        try:
            # Get positions from cache
            raw_positions = await cache_session.get_positions(user_id)

            if raw_positions is None:
                logger.info("User positions not found in cache", user_id=user_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} positions not found in cache",
                )

            # Convert raw position data to Position models
            positions = []
            for pos_data in raw_positions:
                position = Position(
                    symbol=pos_data.get("symbol", ""),
                    exchange=pos_data.get("exchange", ""),
                    side=pos_data.get("side", ""),
                    size=pos_data.get("size", 0.0),
                    entry_price=pos_data.get("entry_price", 0.0),
                    current_price=pos_data.get("current_price", 0.0),
                    unrealized_pnl=pos_data.get("unrealized_pnl", 0.0),
                    margin_used=pos_data.get("margin_used", 0.0),
                )
                positions.append(position)

            logger.info(
                "User positions retrieved successfully",
                user_id=user_id,
                positions_count=len(positions),
                cache_hit=True,
            )

            return AccountPositionsResponse(
                success=True,
                user_id=user_id,
                positions=positions,
                total_positions=len(positions),
                cached_at=datetime.utcnow(),
                timestamp=datetime.utcnow(),
            )

        except HTTPException:
            raise
        except TimeoutError as e:
            await handle_cache_error("get_user_positions", e, {"user_id": user_id})
        except Exception as e:
            await handle_cache_error("get_user_positions", e, {"user_id": user_id})


@router.get("/{user_id}/balances", response_model=AccountBalancesResponse)
async def get_user_balances(
    user_id: str, cache_session: Any = Depends(get_account_cache)
) -> AccountBalancesResponse:
    """
    Get user account balances from cache.

    Retrieves all currency balances for the specified user from the account cache,
    including available, used, and total amounts for each currency.

    Args:
        user_id: User identifier
        cache_session: Account cache dependency injection

    Returns:
        AccountBalancesResponse with user balances

    Raises:
        HTTPException: 404 if user not found, 422 for validation errors,
                      503 for cache service issues, 408 for timeouts
    """
    # Validate and sanitize user ID
    try:
        user_id = validate_user_id(user_id)
    except InvalidParameterError as e:
        logger.warning("Invalid user ID format", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    async with log_cache_operation("get_user_balances", user_id=user_id):
        try:
            # Get balances from cache
            raw_balances = await cache_session.get_balance(user_id)

            if raw_balances is None:
                logger.info("User balances not found in cache", user_id=user_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} balances not found in cache",
                )

            # Convert raw balance data to Balance models
            balances = []
            total_balance_usd = 0.0

            for balance_data in raw_balances:
                balance = Balance(
                    currency=balance_data.get("currency", ""),
                    available=balance_data.get("available", 0.0),
                    used=balance_data.get("used", 0.0),
                    total=balance_data.get("total", 0.0),
                )
                balances.append(balance)

                # Calculate USD equivalent (simplified - would need price conversion in real implementation)
                if balance_data.get("currency") == "USDT":
                    total_balance_usd += balance_data.get("total", 0.0)
                elif balance_data.get("currency") == "BTC":
                    # Simplified: use 50000 as BTC price
                    total_balance_usd += balance_data.get("total", 0.0) * 50000
                elif balance_data.get("currency") == "ETH":
                    # Simplified: use 3000 as ETH price
                    total_balance_usd += balance_data.get("total", 0.0) * 3000

            logger.info(
                "User balances retrieved successfully",
                user_id=user_id,
                balance_currencies=len(balances),
                total_balance_usd=total_balance_usd,
                cache_hit=True,
            )

            return AccountBalancesResponse(
                success=True,
                user_id=user_id,
                balances=balances,
                total_balance_usd=total_balance_usd,
                cached_at=datetime.utcnow(),
                timestamp=datetime.utcnow(),
            )

        except HTTPException:
            raise
        except TimeoutError as e:
            await handle_cache_error("get_user_balances", e, {"user_id": user_id})
        except Exception as e:
            await handle_cache_error("get_user_balances", e, {"user_id": user_id})


@router.get("/{user_id}/status", response_model=AccountStatusResponse)
async def get_account_status(
    user_id: str, cache_session: Any = Depends(get_account_cache)
) -> AccountStatusResponse:
    """
    Get account status and metadata from cache.

    Retrieves comprehensive account status information including position count,
    total balance, activity status, and margin levels.

    Args:
        user_id: User identifier
        cache_session: Account cache dependency injection

    Returns:
        AccountStatusResponse with account status data

    Raises:
        HTTPException: 404 if user not found, 422 for validation errors,
                      503 for cache service issues, 408 for timeouts
    """
    # Validate and sanitize user ID
    try:
        user_id = validate_user_id(user_id)
    except InvalidParameterError as e:
        logger.warning("Invalid user ID format", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    async with log_cache_operation("get_account_status", user_id=user_id):
        try:
            # Get positions and balances to calculate status
            raw_positions = await cache_session.get_positions(user_id)
            raw_balances = await cache_session.get_balance(user_id)

            if raw_positions is None and raw_balances is None:
                logger.info("User account data not found in cache", user_id=user_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} account data not found in cache",
                )

            # Calculate status metrics
            total_positions = len(raw_positions) if raw_positions else 0
            total_balance_usd = 0.0
            margin_level = None

            if raw_balances:
                for balance_data in raw_balances:
                    if balance_data.get("currency") == "USDT":
                        total_balance_usd += balance_data.get("total", 0.0)
                    elif balance_data.get("currency") == "BTC":
                        total_balance_usd += balance_data.get("total", 0.0) * 50000
                    elif balance_data.get("currency") == "ETH":
                        total_balance_usd += balance_data.get("total", 0.0) * 3000

            # Calculate margin level if positions exist
            if raw_positions:
                total_margin_used = sum(
                    pos.get("margin_used", 0.0) for pos in raw_positions
                )
                if total_margin_used > 0:
                    margin_level = (total_balance_usd / total_margin_used) * 100

            # Determine account status
            account_status = (
                "active" if total_positions > 0 or total_balance_usd > 0 else "inactive"
            )

            logger.info(
                "Account status retrieved successfully",
                user_id=user_id,
                status=account_status,
                total_positions=total_positions,
                total_balance_usd=total_balance_usd,
                cache_hit=True,
            )

            return AccountStatusResponse(
                success=True,
                user_id=user_id,
                status=account_status,
                last_activity=datetime.utcnow(),  # Would be from cache in real implementation
                total_positions=total_positions,
                total_balance_usd=total_balance_usd,
                margin_level=margin_level,
                cached_at=datetime.utcnow(),
                timestamp=datetime.utcnow(),
            )

        except HTTPException:
            raise
        except TimeoutError as e:
            await handle_cache_error("get_account_status", e, {"user_id": user_id})
        except Exception as e:
            await handle_cache_error("get_account_status", e, {"user_id": user_id})


@router.get("/summary", response_model=AccountSummaryResponse)
async def get_accounts_summary(
    cache_session: Any = Depends(get_account_cache),
) -> AccountSummaryResponse:
    """
    Get accounts cache summary and statistics.

    Retrieves overall statistics about cached account data including
    user counts, position totals, and system health metrics.

    Args:
        cache_session: Account cache dependency injection

    Returns:
        AccountSummaryResponse with cache summary statistics

    Raises:
        HTTPException: 503 for cache service issues, 408 for timeouts
    """
    async with log_cache_operation("get_accounts_summary"):
        try:
            # Get summary data from cache
            summary_data = await cache_session.get_summary()

            if summary_data is None:
                # Return default summary if none available
                summary_data = {
                    "total_users": 0,
                    "active_users": 0,
                    "total_positions": 0,
                    "total_balance_usd": 0.0,
                }

            logger.info(
                "Account summary retrieved successfully",
                total_users=summary_data.get("total_users", 0),
                active_users=summary_data.get("active_users", 0),
                total_positions=summary_data.get("total_positions", 0),
                cache_hit=True,
            )

            return AccountSummaryResponse(
                success=True,
                total_users=summary_data.get("total_users", 0),
                active_users=summary_data.get("active_users", 0),
                total_positions=summary_data.get("total_positions", 0),
                total_balance_usd=summary_data.get("total_balance_usd", 0.0),
                cache_health="healthy",
                last_updated=datetime.utcnow(),
                timestamp=datetime.utcnow(),
            )

        except TimeoutError as e:
            await handle_cache_error("get_accounts_summary", e)
        except Exception as e:
            await handle_cache_error("get_accounts_summary", e)


@router.get("/health", response_model=HealthResponse)
async def accounts_cache_health(
    cache_session: Any = Depends(get_account_cache),
) -> HealthResponse:
    """
    Check accounts cache health status.

    Performs health checks on the account cache service including
    connectivity, responsiveness, and basic functionality tests.

    Args:
        cache_session: Account cache dependency injection

    Returns:
        HealthResponse with cache health information

    Raises:
        HTTPException: 503 for cache service issues
    """
    async with log_cache_operation("accounts_cache_health"):
        try:
            # Test cache connectivity
            ping_result = await cache_session.ping()
            test_result = await cache_session.test()

            redis_connected = ping_result == "pong" and test_result is True

            logger.info(
                "Account cache health check completed",
                ping_result=ping_result,
                test_result=test_result,
                redis_connected=redis_connected,
                status="healthy" if redis_connected else "unhealthy",
            )

            return HealthResponse(
                success=True,
                service="fullon_cache_api_accounts",
                status="healthy" if redis_connected else "unhealthy",
                version="0.1.0",
                cache_status={
                    "redis_connected": "yes" if redis_connected else "no",
                    "ping_result": str(ping_result),
                    "test_result": str(test_result),
                },
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(
                "Account cache health check failed",
                error=str(e),
                error_type=type(e).__name__,
            )

            return HealthResponse(
                success=False,
                service="fullon_cache_api_accounts",
                status="unhealthy",
                version="0.1.0",
                cache_status={"redis_connected": "no", "error": str(e)},
                timestamp=datetime.utcnow(),
            )
