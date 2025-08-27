from fastapi import HTTPException
from fullon_log import get_component_logger
from fullon_orm import SymbolRepository, UserRepository, get_async_session

from ..exceptions import CacheNotFoundError

logger = get_component_logger("fullon.api.cache.validation")


async def validate_exchange_symbol(exchange: str, symbol: str) -> tuple[str, str]:
    """Validate exchange and symbol exist in the database."""
    logger.debug("Validating exchange and symbol", exchange=exchange, symbol=symbol)

    try:
        async with get_async_session() as session:
            symbol_repo = SymbolRepository(session)

            # Check if symbol exists for this exchange
            db_symbol = await symbol_repo.get_by_symbol(symbol, exchange)
            if not db_symbol:
                logger.warning(
                    "Symbol not found in database", exchange=exchange, symbol=symbol
                )
                raise CacheNotFoundError(
                    f"Symbol {symbol} not found on exchange {exchange}"
                )

            logger.debug(
                "Exchange and symbol validated successfully",
                exchange=exchange,
                symbol=symbol,
                symbol_id=db_symbol.id,
            )
            return exchange, symbol

    except Exception as e:
        if isinstance(e, CacheNotFoundError):
            raise
        logger.error(
            "Database validation failed", exchange=exchange, symbol=symbol, error=str(e)
        )
        raise HTTPException(
            status_code=500, detail="Validation service unavailable"
        ) from e


async def validate_user_exists(user_id: int) -> int:
    """Validate user exists in the database."""
    logger.debug("Validating user exists", user_id=user_id)

    try:
        async with get_async_session() as session:
            user_repo = UserRepository(session)

            user = await user_repo.get_by_id(user_id)
            if not user:
                logger.warning("User not found in database", user_id=user_id)
                raise CacheNotFoundError(f"User {user_id} not found")

            if not user.active:
                logger.warning("User is inactive", user_id=user_id)
                raise HTTPException(status_code=403, detail="User account is inactive")

            logger.debug(
                "User validated successfully", user_id=user_id, user_name=user.name
            )
            return user_id

    except Exception as e:
        if isinstance(e, CacheNotFoundError | HTTPException):
            raise
        logger.error("User validation failed", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500, detail="User validation service unavailable"
        ) from e


async def validate_bot_exists(bot_id: int) -> int:
    """Validate bot exists and is accessible."""
    logger.debug("Validating bot exists", bot_id=bot_id)

    try:
        async with get_async_session() as session:
            from fullon_orm.repositories import BotRepository

            bot_repo = BotRepository(session)

            bot = await bot_repo.get_by_id(bot_id)
            if not bot:
                logger.warning("Bot not found in database", bot_id=bot_id)
                raise CacheNotFoundError(f"Bot {bot_id} not found")

            logger.debug("Bot validated successfully", bot_id=bot_id, bot_name=bot.name)
            return bot_id

    except Exception as e:
        if isinstance(e, CacheNotFoundError):
            raise
        logger.error("Bot validation failed", bot_id=bot_id, error=str(e))
        raise HTTPException(
            status_code=500, detail="Bot validation service unavailable"
        ) from e
