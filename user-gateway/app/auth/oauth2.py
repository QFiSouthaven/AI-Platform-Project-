"""
OAuth2 authentication for User Gateway.

Provides OAuth2 password bearer authentication and user retrieval.
"""

import logging
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User, TokenData
from app.auth.jwt_handler import verify_token

logger = logging.getLogger(__name__)

# OAuth2 scheme with scopes
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=settings.OAUTH2_TOKEN_URL,
    scopes={
        "users:read": "Read user information",
        "users:write": "Create and update users",
        "users:delete": "Delete users",
        "admin": "Full administrative access",
    },
)


async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from the JWT token.

    Args:
        security_scopes: Required security scopes for the endpoint.
        token: JWT access token from the Authorization header.
        db: Database session.

    Returns:
        User: The authenticated user.

    Raises:
        HTTPException: If authentication fails or user is not found.
    """
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "INVALID_CREDENTIALS",
            "message": "Could not validate credentials",
        },
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        # Verify and decode token
        payload = verify_token(token, token_type="access")
        if payload is None:
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        token_scopes: List[str] = payload.get("scopes", [])
        token_data = TokenData(
            user_id=user_id,
            email=payload.get("email"),
            scopes=token_scopes,
        )

    except JWTError as e:
        logger.error(f"JWT error: {str(e)}")
        raise credentials_exception

    # Check required scopes
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_PERMISSIONS",
                    "message": f"Not enough permissions. Required scope: {scope}",
                },
                headers={"WWW-Authenticate": authenticate_value},
            )

    # Get user from database
    result = await db.execute(
        select(User).where(User.id == token_data.user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning(f"User not found for ID: {token_data.user_id}")
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user.

    Args:
        current_user: User from get_current_user dependency.

    Returns:
        User: The active authenticated user.

    Raises:
        HTTPException: If user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "USER_INACTIVE",
                "message": "User account is deactivated",
            },
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get the current superuser.

    Args:
        current_user: User from get_current_active_user dependency.

    Returns:
        User: The authenticated superuser.

    Raises:
        HTTPException: If user is not a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "NOT_SUPERUSER",
                "message": "User does not have superuser privileges",
            },
        )
    return current_user


def check_permissions(required_roles: List[str]):
    """
    Dependency factory for checking user roles.

    Args:
        required_roles: List of roles required to access the endpoint.

    Returns:
        Callable: Dependency function that checks user roles.
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """
        Check if user has required roles.

        Args:
            current_user: The authenticated user.

        Returns:
            User: The authenticated user if they have required roles.

        Raises:
            HTTPException: If user doesn't have required roles.
        """
        if not any(role in current_user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_ROLES",
                    "message": f"User does not have required roles: {required_roles}",
                },
            )
        return current_user

    return role_checker
