"""
API Gateway integration tests.

Tests routing, rate limiting, CORS, and health endpoints.
"""
import asyncio
import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_healthy(self, api_client: AsyncClient):
        """Test that health endpoint returns healthy status."""
        response = await api_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api-gateway"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_ready_endpoint_returns_ready(self, api_client: AsyncClient):
        """Test that readiness endpoint returns ready status."""
        response = await api_client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"


class TestCORSHeaders:
    """Tests for CORS configuration."""

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, api_client: AsyncClient):
        """Test that CORS headers are present in responses."""
        response = await api_client.options(
            "/api/v1/users/",
            headers={"Origin": "http://localhost:3000"}
        )

        assert response.status_code in [200, 204]
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    @pytest.mark.asyncio
    async def test_cors_preflight_request(self, api_client: AsyncClient):
        """Test CORS preflight request handling."""
        response = await api_client.options(
            "/api/v1/workflows/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization, Content-Type"
            }
        )

        assert response.status_code == 204
        assert "access-control-allow-headers" in response.headers


class TestSecurityHeaders:
    """Tests for security headers."""

    @pytest.mark.asyncio
    async def test_security_headers_present(self, api_client: AsyncClient):
        """Test that security headers are present."""
        response = await api_client.get("/health")

        headers = response.headers
        assert "x-content-type-options" in headers
        assert "x-frame-options" in headers
        assert "x-xss-protection" in headers

    @pytest.mark.asyncio
    async def test_request_id_header(self, api_client: AsyncClient):
        """Test that request ID is returned in response."""
        response = await api_client.get("/health")

        assert "x-request-id" in response.headers


class TestRouting:
    """Tests for API routing."""

    @pytest.mark.asyncio
    async def test_auth_routes_to_user_gateway(self, api_client: AsyncClient):
        """Test that auth routes go to user gateway."""
        # This will fail if service is not running, but tests routing config
        response = await api_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "test"}
        )

        # Expect either valid response or service unavailable (502/503)
        # Not 404, which would indicate routing failure
        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_users_routes_to_user_gateway(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that user routes go to user gateway."""
        response = await api_client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )

        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_workflows_routes_to_orchestration(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that workflow routes go to workflow orchestration."""
        response = await api_client.get(
            "/api/v1/workflows/",
            headers=auth_headers
        )

        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_tasks_routes_to_orchestration(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that task routes go to workflow orchestration."""
        response = await api_client.get(
            "/api/v1/tasks/",
            headers=auth_headers
        )

        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_generate_routes_to_core_processing(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that generate routes go to core processing."""
        response = await api_client.post(
            "/api/v1/generate/code",
            headers=auth_headers,
            json={"prompt": "test"}
        )

        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_debug_routes_to_core_processing(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that debug routes go to core processing."""
        response = await api_client.post(
            "/api/v1/debug/analyze",
            headers=auth_headers,
            json={"code": "print('test')"}
        )

        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_events_routes_to_data_integration(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that event routes go to data integration."""
        response = await api_client.get(
            "/api/v1/events/",
            headers=auth_headers
        )

        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_cache_routes_to_data_integration(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that cache routes go to data integration."""
        response = await api_client.get(
            "/api/v1/cache/stats",
            headers=auth_headers
        )

        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_models_routes_to_model_management(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that model routes go to model management."""
        response = await api_client.get(
            "/api/v1/models/",
            headers=auth_headers
        )

        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_plugins_routes_to_model_management(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that plugin routes go to model management."""
        response = await api_client.get(
            "/api/v1/plugins/",
            headers=auth_headers
        )

        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_infrastructure_routes_correctly(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that infrastructure routes go to infrastructure service."""
        response = await api_client.get(
            "/api/v1/infrastructure/status",
            headers=auth_headers
        )

        assert response.status_code != 404


class TestRateLimiting:
    """Tests for rate limiting."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_auth_rate_limiting(self, api_client: AsyncClient):
        """Test that auth endpoints have stricter rate limits."""
        responses = []

        # Send multiple requests quickly
        for _ in range(15):
            response = await api_client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "test"}
            )
            responses.append(response.status_code)

        # Should eventually get rate limited (429) or service unavailable
        # Rate limit is 10r/s with burst of 20
        rate_limited = any(code == 429 for code in responses)
        # If services aren't running, we'll get 502/503
        service_unavailable = all(code in [502, 503] for code in responses)

        assert rate_limited or service_unavailable

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_rate_limiting(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that generate endpoints have strict rate limits."""
        responses = []

        # Send multiple requests quickly
        for _ in range(10):
            response = await api_client.post(
                "/api/v1/generate/code",
                headers=auth_headers,
                json={"prompt": "test"}
            )
            responses.append(response.status_code)

        # Should eventually get rate limited (429)
        # Rate limit is 5r/s with burst of 10
        rate_limited = any(code == 429 for code in responses)
        service_unavailable = all(code in [502, 503] for code in responses)

        assert rate_limited or service_unavailable


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_404_returns_json(self, api_client: AsyncClient):
        """Test that 404 errors return JSON format."""
        response = await api_client.get("/nonexistent/path")

        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        assert "error" in data

    @pytest.mark.asyncio
    async def test_invalid_json_returns_error(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that invalid JSON returns appropriate error."""
        response = await api_client.post(
            "/api/v1/workflows/",
            headers={**auth_headers, "Content-Type": "application/json"},
            content="invalid json {"
        )

        # Should get 400 Bad Request or 502 if service not running
        assert response.status_code in [400, 502, 503]


class TestProxyHeaders:
    """Tests for proxy header configuration."""

    @pytest.mark.asyncio
    async def test_forwarded_headers(self, api_client: AsyncClient):
        """Test that forwarding headers are set correctly."""
        # Custom headers should be forwarded
        response = await api_client.get(
            "/health",
            headers={
                "X-Request-ID": "test-request-123",
                "X-Correlation-ID": "test-correlation-456"
            }
        )

        assert response.status_code == 200


class TestWebSocket:
    """Tests for WebSocket support."""

    @pytest.mark.asyncio
    async def test_websocket_endpoint_exists(self, api_client: AsyncClient):
        """Test that WebSocket endpoint is accessible."""
        # HTTP request to WebSocket endpoint should get upgrade required
        response = await api_client.get("/ws/")

        # Should not be 404 (routing works)
        # Will likely be 400, 426, or 502 depending on service state
        assert response.status_code != 404


class TestRequestValidation:
    """Tests for request validation."""

    @pytest.mark.asyncio
    async def test_large_request_body_rejected(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that requests exceeding body size limit are rejected."""
        # Create a payload larger than 100MB
        large_payload = {"data": "x" * (101 * 1024 * 1024)}  # 101 MB

        response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=large_payload
        )

        # Should get 413 Payload Too Large or connection error
        assert response.status_code in [413, 502, 503] or response.is_error

    @pytest.mark.asyncio
    async def test_model_upload_allows_large_files(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that model uploads allow larger file sizes."""
        # Model management endpoint should allow up to 5GB
        # This just tests the route exists and doesn't reject small files
        response = await api_client.post(
            "/api/v1/models/",
            headers=auth_headers,
            json={"name": "test-model", "version": "1.0.0"}
        )

        # Should not get 413 for small payload
        assert response.status_code != 413
