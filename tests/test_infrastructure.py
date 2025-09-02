import asyncio
from unittest.mock import patch

import pytest


class TestBaseFastAPIWebSocketHandler:
    """Test suite for BaseFastAPIWebSocketHandler abstract base class."""

    def test_base_websocket_handler_is_abstract(self):
        """Test that BaseFastAPIWebSocketHandler cannot be instantiated directly."""
        from fullon_cache_api import BaseFastAPIWebSocketHandler

        with pytest.raises(TypeError):
            BaseFastAPIWebSocketHandler()

    def test_concrete_implementation_works(self):
        """Test that concrete implementations work correctly."""
        from fullon_cache_api import BaseFastAPIWebSocketHandler

        class ConcreteWebSocketHandler(BaseFastAPIWebSocketHandler):
            async def handle_message(self, websocket, message):
                return {"test": "data"}

            async def validate_params(self, params):
                return True

        handler = ConcreteWebSocketHandler()
        assert hasattr(handler, "logger")
        assert asyncio.iscoroutinefunction(handler.handle_message)
        assert asyncio.iscoroutinefunction(handler.validate_params)

        # Test logger exists and has component structure
        assert handler.logger is not None

    @pytest.mark.asyncio
    async def test_concrete_implementation_methods(self):
        """Test that concrete implementation methods work."""
        from fullon_cache_api import BaseFastAPIWebSocketHandler

        class ConcreteWebSocketHandler(BaseFastAPIWebSocketHandler):
            async def handle_message(self, websocket, message):
                return {"status": "success", "data": "test_data"}

            async def validate_params(self, params):
                return params is not None

        handler = ConcreteWebSocketHandler()
        result = await handler.handle_message(None, {"test": "message"})
        validation = await handler.validate_params({"test": "params"})

        assert result == {"status": "success", "data": "test_data"}
        assert validation is True


class TestBaseFastAPIWebSocketStream:
    """Test suite for BaseFastAPIWebSocketStream abstract base class."""

    def test_base_websocket_stream_is_abstract(self):
        """Test that BaseFastAPIWebSocketStream cannot be instantiated directly."""
        from fullon_cache_api import BaseFastAPIWebSocketStream

        with pytest.raises(TypeError):
            BaseFastAPIWebSocketStream()

    def test_concrete_stream_implementation_works(self):
        """Test that concrete stream implementations work correctly."""
        from fullon_cache_api import BaseFastAPIWebSocketStream

        class ConcreteWebSocketStream(BaseFastAPIWebSocketStream):
            async def stream_updates(self, websocket, params):
                for i in range(3):
                    yield {"update": i, "data": f"stream_data_{i}"}

        stream = ConcreteWebSocketStream()
        assert hasattr(stream, "logger")
        # stream_updates is an async generator, not a coroutine function
        import inspect

        assert inspect.ismethod(stream.stream_updates)

        # Test logger exists and has component structure
        assert stream.logger is not None

    @pytest.mark.asyncio
    async def test_concrete_stream_implementation_streaming(self):
        """Test that concrete stream implementation streaming works."""
        from fullon_cache_api import BaseFastAPIWebSocketStream

        class ConcreteWebSocketStream(BaseFastAPIWebSocketStream):
            async def stream_updates(self, websocket, params):
                for i in range(3):
                    yield {"update": i, "data": f"stream_data_{i}"}

        stream = ConcreteWebSocketStream()
        results = []
        async for update in stream.stream_updates(None, {"test": "params"}):
            results.append(update)

        assert len(results) == 3
        assert results[0] == {"update": 0, "data": "stream_data_0"}
        assert results[2] == {"update": 2, "data": "stream_data_2"}


class TestCacheHealthChecker:
    """Test suite for CacheHealthChecker utility class."""

    def test_health_checker_initialization(self):
        """Test health checker initializes correctly."""
        from fullon_cache_api import CacheHealthChecker

        checker = CacheHealthChecker()
        assert hasattr(checker, "logger")
        assert hasattr(checker, "check_cache_connectivity")

        # Test logger exists
        assert checker.logger is not None

    @pytest.mark.asyncio
    async def test_check_cache_connectivity_method_exists(self):
        """Test that check_cache_connectivity method exists and is async."""
        from fullon_cache_api import CacheHealthChecker

        checker = CacheHealthChecker()
        assert asyncio.iscoroutinefunction(checker.check_cache_connectivity)

    @pytest.mark.asyncio
    async def test_check_websocket_connectivity_method_exists(self):
        """Test that check_websocket_connectivity method exists and is async."""
        from fullon_cache_api import CacheHealthChecker

        checker = CacheHealthChecker()
        assert asyncio.iscoroutinefunction(checker.check_websocket_connectivity)

        # Test that it returns expected structure
        result = await checker.check_websocket_connectivity()
        assert isinstance(result, dict)
        assert "status" in result
        assert "framework" in result
        assert "transport" in result
        assert result["framework"] == "fastapi"
        assert result["transport"] == "websocket"


class TestExceptions:
    """Test suite for custom exception classes."""

    def test_cache_not_found_error(self):
        """Test CacheNotFoundError exception."""
        from fullon_cache_api import CacheNotFoundError

        # Test default message
        error = CacheNotFoundError()
        assert error.error_code == "CACHE_MISS"
        assert "not found" in error.message.lower()

        # Test custom message
        custom_error = CacheNotFoundError("Custom not found message")
        assert custom_error.error_code == "CACHE_MISS"
        assert custom_error.message == "Custom not found message"

    def test_cache_service_unavailable_error(self):
        """Test CacheServiceUnavailableError exception."""
        from fullon_cache_api import CacheServiceUnavailableError

        # Test default message
        error = CacheServiceUnavailableError()
        assert error.error_code == "CACHE_UNAVAILABLE"
        assert "unavailable" in error.message.lower()

        # Test custom message
        custom_error = CacheServiceUnavailableError("Redis is down")
        assert custom_error.error_code == "CACHE_UNAVAILABLE"
        assert custom_error.message == "Redis is down"

    def test_cache_timeout_error(self):
        """Test CacheTimeoutError exception."""
        from fullon_cache_api import CacheTimeoutError

        # Test default message
        error = CacheTimeoutError()
        assert error.error_code == "TIMEOUT"
        assert "timeout" in error.message.lower()

        # Test custom message
        custom_error = CacheTimeoutError("Operation took too long")
        assert custom_error.error_code == "TIMEOUT"
        assert custom_error.message == "Operation took too long"

    def test_websocket_connection_error(self):
        """Test FastAPIWebSocketConnectionError exception."""
        from fullon_cache_api import FastAPIWebSocketConnectionError

        # Test default message
        error = FastAPIWebSocketConnectionError()
        assert error.error_code == "WEBSOCKET_CONNECTION_ERROR"
        assert (
            "websocket" in error.message.lower()
            or "connection" in error.message.lower()
        )

        # Test custom message
        custom_error = FastAPIWebSocketConnectionError("WebSocket failed to connect")
        assert custom_error.error_code == "WEBSOCKET_CONNECTION_ERROR"
        assert custom_error.message == "WebSocket failed to connect"

    def test_cache_websocket_exception_base_class(self):
        """Test CacheFastAPIWebSocketException base class."""
        from fullon_cache_api import CacheFastAPIWebSocketException

        # Test that it's based on Exception
        assert issubclass(CacheFastAPIWebSocketException, Exception)

        # Test instantiation
        error = CacheFastAPIWebSocketException("Test error", "TEST_CODE")
        assert error.message == "Test error"
        assert error.error_code == "TEST_CODE"

    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from CacheFastAPIWebSocketException."""
        from fullon_cache_api import (
            CacheFastAPIWebSocketException,
            CacheNotFoundError,
            CacheServiceUnavailableError,
            CacheTimeoutError,
            FastAPIWebSocketConnectionError,
        )

        assert issubclass(CacheNotFoundError, CacheFastAPIWebSocketException)
        assert issubclass(CacheServiceUnavailableError, CacheFastAPIWebSocketException)
        assert issubclass(CacheTimeoutError, CacheFastAPIWebSocketException)
        assert issubclass(
            FastAPIWebSocketConnectionError, CacheFastAPIWebSocketException
        )


class TestTypes:
    """Test suite for type definitions."""

    def test_type_definitions_exist(self):
        """Test that all expected type definitions exist."""
        # Import typing utilities to verify types

        from fullon_cache_api import (
            CacheData,
            CacheResult,
            FastAPIWebSocketMessage,
            FastAPIWebSocketResponse,
            HealthStatus,
        )

        # These should be type aliases or classes, not None
        assert CacheData is not None
        assert CacheResult is not None
        assert HealthStatus is not None
        assert FastAPIWebSocketMessage is not None
        assert FastAPIWebSocketResponse is not None

    def test_type_annotations_work(self):
        """Test that type annotations work with our custom types."""
        from fullon_cache_api import (
            CacheData,
            CacheResult,
            FastAPIWebSocketMessage,
            HealthStatus,
        )

        # Test function annotations work
        def test_func(data: CacheData) -> CacheResult:
            return data

        def test_health_func(status: HealthStatus) -> HealthStatus:
            return {"status": "healthy"}

        def test_websocket_func(message: FastAPIWebSocketMessage) -> dict:
            return {"received": True}

        # Should not raise any errors
        assert callable(test_func)
        assert callable(test_health_func)
        assert callable(test_websocket_func)

    def test_pydantic_models_work(self):
        """Test that Pydantic models work correctly."""
        from fullon_cache_api import FastAPIWebSocketMessage, FastAPIWebSocketResponse

        # Test FastAPIWebSocketMessage
        message = FastAPIWebSocketMessage(operation="test", params={"key": "value"})
        assert message.operation == "test"
        assert message.params == {"key": "value"}
        assert message.request_id is None

        # Test FastAPIWebSocketResponse
        response = FastAPIWebSocketResponse(success=True, result={"data": "test"})
        assert response.success is True
        assert response.result == {"data": "test"}
        assert response.error is None


class TestImports:
    """Test suite for package imports and exports."""

    def test_version_import(self):
        """Test version is correctly imported."""
        from fullon_cache_api import __version__

        assert __version__ == "0.1.0"

    def test_all_expected_imports_available(self):
        """Test all expected infrastructure imports are available."""
        import fullon_cache_api

        # Check base classes
        assert hasattr(fullon_cache_api, "BaseFastAPIWebSocketHandler")
        assert hasattr(fullon_cache_api, "BaseFastAPIWebSocketStream")
        assert hasattr(fullon_cache_api, "CacheHealthChecker")

        # Check types
        assert hasattr(fullon_cache_api, "CacheData")
        assert hasattr(fullon_cache_api, "CacheResult")
        assert hasattr(fullon_cache_api, "HealthStatus")
        assert hasattr(fullon_cache_api, "FastAPIWebSocketMessage")
        assert hasattr(fullon_cache_api, "FastAPIWebSocketResponse")

        # Check exceptions
        assert hasattr(fullon_cache_api, "CacheFastAPIWebSocketException")
        assert hasattr(fullon_cache_api, "CacheNotFoundError")
        assert hasattr(fullon_cache_api, "CacheServiceUnavailableError")
        assert hasattr(fullon_cache_api, "CacheTimeoutError")
        assert hasattr(fullon_cache_api, "FastAPIWebSocketConnectionError")

    def test_all_exports_in_all_list(self):
        """Test that __all__ list contains all expected exports."""
        import fullon_cache_api

        expected_exports = [
            "__version__",
            "BaseFastAPIWebSocketHandler",
            "BaseFastAPIWebSocketStream",
            "CacheHealthChecker",
            "FastAPIWebSocketMessage",
            "FastAPIWebSocketRequest",
            "FastAPIWebSocketResponse",
            "FastAPIStreamMessage",
            "FastAPIWebSocketAPIResponse",
            "CacheData",
            "CacheResult",
            "CacheKey",
            "HealthStatus",
            "Timestamp",
            "CacheFastAPIWebSocketException",
            "CacheNotFoundError",
            "CacheServiceUnavailableError",
            "CacheTimeoutError",
            "FastAPIWebSocketConnectionError",
        ]

        for export in expected_exports:
            assert export in fullon_cache_api.__all__

    def test_module_imports_cleanly(self):
        """Test that the module can be imported without errors."""
        import fullon_cache_api

        assert fullon_cache_api.__name__ == "fullon_cache_api"

    def test_no_unexpected_imports(self):
        """Test that we don't have any unexpected imports in the public API."""
        import fullon_cache_api

        # Get all public attributes (not starting with _)
        public_attrs = [
            name for name in dir(fullon_cache_api) if not name.startswith("_")
        ]

        # They should all be in __all__
        for attr in public_attrs:
            if attr not in [
                "annotations",
                "base",
                "types",
                "exceptions",
                "models",
                "handlers",  # May be exposed when other tests import main.py
                "main",  # May be exposed when other tests import main.py
                "routers",  # May be exposed when other tests import main.py
            ]:  # Skip internal modules and special attributes
                assert attr in fullon_cache_api.__all__, f"'{attr}' not in __all__"


class TestLoggingIntegration:
    """Test suite for fullon_log integration."""

    @patch("fullon_cache_api.base.get_component_logger")
    def test_base_websocket_handler_logging(self, mock_get_logger):
        """Test that BaseFastAPIWebSocketHandler uses fullon_log correctly."""
        from fullon_cache_api import BaseFastAPIWebSocketHandler

        class ConcreteWebSocketHandler(BaseFastAPIWebSocketHandler):
            async def handle_message(self, websocket, message):
                return {"test": "data"}

            async def validate_params(self, params):
                return True

        ConcreteWebSocketHandler()

        # Verify get_component_logger was called with correct component
        mock_get_logger.assert_called_with("fullon.api.cache.websocket")

    @patch("fullon_cache_api.base.get_component_logger")
    def test_base_websocket_stream_logging(self, mock_get_logger):
        """Test that BaseFastAPIWebSocketStream uses fullon_log correctly."""
        from fullon_cache_api import BaseFastAPIWebSocketStream

        class ConcreteWebSocketStream(BaseFastAPIWebSocketStream):
            async def stream_updates(self, websocket, params):
                yield {"test": "data"}

        ConcreteWebSocketStream()

        # Verify get_component_logger was called with correct component
        mock_get_logger.assert_called_with("fullon.api.cache.websocket.stream")

    @patch("fullon_cache_api.base.get_component_logger")
    def test_cache_health_checker_logging(self, mock_get_logger):
        """Test that CacheHealthChecker uses fullon_log correctly."""
        from fullon_cache_api import CacheHealthChecker

        CacheHealthChecker()

        # Verify get_component_logger was called with correct component
        mock_get_logger.assert_called_with("fullon.api.cache.health")


class TestLRRSCompliance:
    """Test suite for LRRS (Little, Responsible, Reusable, Separate) compliance."""

    def test_little_principle(self):
        """Test that components follow the Little principle - single purpose."""
        from fullon_cache_api import (
            BaseFastAPIWebSocketHandler,
            BaseFastAPIWebSocketStream,
            CacheHealthChecker,
        )

        # BaseFastAPIWebSocketHandler should only provide abstract WebSocket message handling
        handler_methods = [
            method
            for method in dir(BaseFastAPIWebSocketHandler)
            if not method.startswith("_")
        ]
        assert "handle_message" in handler_methods
        assert "validate_params" in handler_methods
        # Should be minimal - just the essentials

        # BaseFastAPIWebSocketStream should only provide abstract WebSocket streaming
        stream_methods = [
            method
            for method in dir(BaseFastAPIWebSocketStream)
            if not method.startswith("_")
        ]
        assert "stream_updates" in stream_methods

        # CacheHealthChecker should only handle health checks
        health_methods = [
            method for method in dir(CacheHealthChecker) if not method.startswith("_")
        ]
        assert "check_cache_connectivity" in health_methods
        assert "check_websocket_connectivity" in health_methods

    def test_responsible_principle(self):
        """Test that each component has one clear responsibility."""
        from fullon_cache_api import (
            BaseFastAPIWebSocketHandler,
            BaseFastAPIWebSocketStream,
            CacheHealthChecker,
            CacheNotFoundError,
            CacheServiceUnavailableError,
            CacheTimeoutError,
            FastAPIWebSocketConnectionError,
        )

        # Each class should have a clear single responsibility
        assert (
            BaseFastAPIWebSocketHandler.__doc__
            and "WebSocket message handlers" in BaseFastAPIWebSocketHandler.__doc__
        )
        assert (
            BaseFastAPIWebSocketStream.__doc__
            and "WebSocket streaming" in BaseFastAPIWebSocketStream.__doc__
        )
        assert CacheHealthChecker.__doc__ and "Health" in CacheHealthChecker.__doc__
        assert CacheNotFoundError.__doc__ and "not found" in CacheNotFoundError.__doc__
        assert (
            CacheServiceUnavailableError.__doc__
            and "unavailable" in CacheServiceUnavailableError.__doc__
        )
        assert CacheTimeoutError.__doc__ and (
            "timeout" in CacheTimeoutError.__doc__
            or "times out" in CacheTimeoutError.__doc__
        )
        assert (
            FastAPIWebSocketConnectionError.__doc__
            and "WebSocket connection" in FastAPIWebSocketConnectionError.__doc__
        )

    def test_reusable_principle(self):
        """Test that components are designed for reuse."""
        from fullon_cache_api import BaseFastAPIWebSocketHandler

        # Should be able to create multiple concrete implementations
        class WebSocketHandler1(BaseFastAPIWebSocketHandler):
            async def handle_message(self, websocket, message):
                return {"handler": "1"}

            async def validate_params(self, params):
                return True

        class WebSocketHandler2(BaseFastAPIWebSocketHandler):
            async def handle_message(self, websocket, message):
                return {"handler": "2"}

            async def validate_params(self, params):
                return params is not None

        handler1 = WebSocketHandler1()
        handler2 = WebSocketHandler2()

        # Both should work independently
        assert hasattr(handler1, "logger")
        assert hasattr(handler2, "logger")
        assert handler1 is not handler2

    def test_separate_principle(self):
        """Test that components are properly separated and loosely coupled."""
        # Test that we can import components independently
        from fullon_cache_api.base import BaseFastAPIWebSocketHandler
        from fullon_cache_api.exceptions import CacheNotFoundError
        from fullon_cache_api.types import CacheData

        # They should work without depending on each other
        assert BaseFastAPIWebSocketHandler is not None
        assert CacheNotFoundError is not None
        assert CacheData is not None
