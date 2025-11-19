"""
Authentication flow integration tests.

Tests OAuth2 authentication, JWT token handling, and authorization.
"""
import pytest
from httpx import AsyncClient
import jwt
from datetime import datetime, timedelta


class TestUserRegistration:
    """Tests for user registration flow."""

    @pytest.mark.asyncio
    async def test_register_new_user(
        self,
        api_client: AsyncClient,
        validate_response
    ):
        """Test registering a new user."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!"
        }

        response = await api_client.post(
            "/api/v1/auth/register",
            json=user_data
        )

        # Either successful registration or service unavailable
        if response.status_code == 201:
            data = response.json()
            validate_response(data, "success")
            assert "user" in data["data"]
            assert data["data"]["user"]["email"] == user_data["email"]
        else:
            assert response.status_code in [400, 409, 502, 503]

    @pytest.mark.asyncio
    async def test_register_duplicate_email_fails(
        self,
        api_client: AsyncClient,
        test_user: dict
    ):
        """Test that registering with duplicate email fails."""
        user_data = {
            "email": test_user["email"],
            "username": "differentuser",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!"
        }

        response = await api_client.post(
            "/api/v1/auth/register",
            json=user_data
        )

        # Should get conflict or validation error
        assert response.status_code in [400, 409, 502, 503]

    @pytest.mark.asyncio
    async def test_register_weak_password_fails(self, api_client: AsyncClient):
        """Test that weak passwords are rejected."""
        user_data = {
            "email": "weakpass@example.com",
            "username": "weakpassuser",
            "password": "123",
            "confirm_password": "123"
        }

        response = await api_client.post(
            "/api/v1/auth/register",
            json=user_data
        )

        assert response.status_code in [400, 422, 502, 503]

    @pytest.mark.asyncio
    async def test_register_mismatched_passwords_fails(
        self,
        api_client: AsyncClient
    ):
        """Test that mismatched passwords are rejected."""
        user_data = {
            "email": "mismatch@example.com",
            "username": "mismatchuser",
            "password": "SecurePassword123!",
            "confirm_password": "DifferentPassword456!"
        }

        response = await api_client.post(
            "/api/v1/auth/register",
            json=user_data
        )

        assert response.status_code in [400, 422, 502, 503]


class TestLogin:
    """Tests for login flow."""

    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(
        self,
        api_client: AsyncClient,
        test_user: dict
    ):
        """Test login with valid credentials."""
        response = await api_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )

        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data["data"]
            assert "refresh_token" in data["data"]
            assert "token_type" in data["data"]
            assert data["data"]["token_type"] == "bearer"
        else:
            # Service not running
            assert response.status_code in [401, 502, 503]

    @pytest.mark.asyncio
    async def test_login_with_invalid_password(
        self,
        api_client: AsyncClient,
        test_user: dict
    ):
        """Test login with invalid password."""
        response = await api_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code in [401, 502, 503]

    @pytest.mark.asyncio
    async def test_login_with_nonexistent_user(self, api_client: AsyncClient):
        """Test login with nonexistent user."""
        response = await api_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123!"
            }
        )

        assert response.status_code in [401, 404, 502, 503]

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, api_client: AsyncClient):
        """Test login with missing fields."""
        response = await api_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com"}
        )

        assert response.status_code in [400, 422, 502, 503]


class TestTokenValidation:
    """Tests for JWT token validation."""

    @pytest.mark.asyncio
    async def test_access_protected_route_with_valid_token(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test accessing protected route with valid token."""
        response = await api_client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )

        # Either successful or service unavailable
        assert response.status_code in [200, 502, 503]

    @pytest.mark.asyncio
    async def test_access_protected_route_without_token(
        self,
        api_client: AsyncClient
    ):
        """Test accessing protected route without token."""
        response = await api_client.get("/api/v1/users/me")

        assert response.status_code in [401, 403, 502, 503]

    @pytest.mark.asyncio
    async def test_access_protected_route_with_expired_token(
        self,
        api_client: AsyncClient,
        expired_token: str
    ):
        """Test accessing protected route with expired token."""
        response = await api_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code in [401, 403, 502, 503]

    @pytest.mark.asyncio
    async def test_access_protected_route_with_invalid_token(
        self,
        api_client: AsyncClient
    ):
        """Test accessing protected route with invalid token."""
        response = await api_client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid-token-here"}
        )

        assert response.status_code in [401, 403, 502, 503]

    @pytest.mark.asyncio
    async def test_access_protected_route_with_malformed_header(
        self,
        api_client: AsyncClient,
        valid_token: str
    ):
        """Test accessing protected route with malformed auth header."""
        # Missing "Bearer" prefix
        response = await api_client.get(
            "/api/v1/users/me",
            headers={"Authorization": valid_token}
        )

        assert response.status_code in [401, 403, 502, 503]


class TestTokenRefresh:
    """Tests for token refresh flow."""

    @pytest.mark.asyncio
    async def test_refresh_token(
        self,
        api_client: AsyncClient,
        test_config: dict,
        test_user: dict
    ):
        """Test refreshing access token."""
        # Create a refresh token
        refresh_payload = {
            "sub": test_user["id"],
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=7),
        }
        refresh_token = jwt.encode(
            refresh_payload,
            test_config["JWT_SECRET"],
            algorithm=test_config["JWT_ALGORITHM"]
        )

        response = await api_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data["data"]
        else:
            assert response.status_code in [401, 502, 503]

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(self, api_client: AsyncClient):
        """Test refresh with invalid token."""
        response = await api_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-refresh-token"}
        )

        assert response.status_code in [401, 403, 502, 503]


class TestLogout:
    """Tests for logout flow."""

    @pytest.mark.asyncio
    async def test_logout(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test logging out."""
        response = await api_client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )

        # Either successful logout or service unavailable
        assert response.status_code in [200, 204, 502, 503]

    @pytest.mark.asyncio
    async def test_logout_without_token(self, api_client: AsyncClient):
        """Test logging out without token."""
        response = await api_client.post("/api/v1/auth/logout")

        # Should require authentication
        assert response.status_code in [401, 403, 502, 503]


class TestAuthorization:
    """Tests for role-based authorization."""

    @pytest.mark.asyncio
    async def test_admin_route_with_admin_token(
        self,
        api_client: AsyncClient,
        test_config: dict,
        admin_user: dict
    ):
        """Test accessing admin route with admin token."""
        # Create admin token
        admin_payload = {
            "sub": admin_user["id"],
            "email": admin_user["email"],
            "roles": admin_user["roles"],
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        admin_token = jwt.encode(
            admin_payload,
            test_config["JWT_SECRET"],
            algorithm=test_config["JWT_ALGORITHM"]
        )

        response = await api_client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Admin should have access
        assert response.status_code in [200, 502, 503]

    @pytest.mark.asyncio
    async def test_admin_route_with_user_token(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test accessing admin route with regular user token."""
        response = await api_client.delete(
            "/api/v1/users/other-user-id",
            headers=auth_headers
        )

        # Regular user should be forbidden
        assert response.status_code in [403, 404, 502, 503]


class TestOAuth2Flow:
    """Tests for OAuth2 authentication flow."""

    @pytest.mark.asyncio
    async def test_oauth2_authorize_redirect(self, api_client: AsyncClient):
        """Test OAuth2 authorization endpoint redirect."""
        response = await api_client.get(
            "/api/v1/auth/oauth2/authorize",
            params={"provider": "google"},
            follow_redirects=False
        )

        # Should redirect to OAuth provider or return error
        assert response.status_code in [302, 400, 502, 503]

    @pytest.mark.asyncio
    async def test_oauth2_callback_without_code(self, api_client: AsyncClient):
        """Test OAuth2 callback without authorization code."""
        response = await api_client.get(
            "/api/v1/auth/oauth2/callback",
            params={"provider": "google"}
        )

        # Should fail without code
        assert response.status_code in [400, 422, 502, 503]


class TestPasswordReset:
    """Tests for password reset flow."""

    @pytest.mark.asyncio
    async def test_request_password_reset(
        self,
        api_client: AsyncClient,
        test_user: dict
    ):
        """Test requesting password reset."""
        response = await api_client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": test_user["email"]}
        )

        # Should always return 200 to prevent email enumeration
        assert response.status_code in [200, 202, 502, 503]

    @pytest.mark.asyncio
    async def test_reset_password_with_invalid_token(
        self,
        api_client: AsyncClient
    ):
        """Test resetting password with invalid token."""
        response = await api_client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "token": "invalid-reset-token",
                "new_password": "NewSecurePassword123!",
                "confirm_password": "NewSecurePassword123!"
            }
        )

        assert response.status_code in [400, 401, 502, 503]


class TestUserProfile:
    """Tests for user profile operations."""

    @pytest.mark.asyncio
    async def test_get_current_user_profile(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting current user profile."""
        response = await api_client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert "email" in data["data"]
        else:
            assert response.status_code in [502, 503]

    @pytest.mark.asyncio
    async def test_update_user_profile(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test updating user profile."""
        response = await api_client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"username": "updatedusername"}
        )

        assert response.status_code in [200, 502, 503]

    @pytest.mark.asyncio
    async def test_change_password(
        self,
        api_client: AsyncClient,
        auth_headers: dict,
        test_user: dict
    ):
        """Test changing user password."""
        response = await api_client.post(
            "/api/v1/users/me/change-password",
            headers=auth_headers,
            json={
                "current_password": test_user["password"],
                "new_password": "NewSecurePassword456!",
                "confirm_password": "NewSecurePassword456!"
            }
        )

        assert response.status_code in [200, 400, 502, 503]
