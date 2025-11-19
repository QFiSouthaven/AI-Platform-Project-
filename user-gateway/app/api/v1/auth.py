"""
Authentication endpoints for User Gateway.

Provides login, registration, and token refresh endpoints.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import (
    User,
    UserCreate,
    UserResponse,
    Token,
    LoginRequest,
    RefreshTokenRequest,
)
from app.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.auth.oauth2 import get_current_active_user
from app.kafka.publisher import get_kafka_publisher

logger = logging.getLogger(__name__)

router = APIRouter()

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.PASSWORD_HASH_ROUNDS,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> User | None:
    """
    Authenticate a user by email and password.

    Args:
        db: Database session.
        email: User email.
        password: Plain text password.

    Returns:
        User if authentication succeeds, None otherwise.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None

    return user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Register a new user account.

    Args:
        user_data: User registration data.
        db: Database session.

    Returns:
        UserResponse: Created user data.

    Raises:
        HTTPException: If email or username already exists.
    """
    # Check if email exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EMAIL_EXISTS",
                "message": "A user with this email already exists",
            },
        )

    # Check if username exists
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "USERNAME_EXISTS",
                "message": "A user with this username already exists",
            },
        )

    # Create user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        roles=["user"],
        scopes=["users:read"],
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    # Publish user created event
    kafka_publisher = get_kafka_publisher()
    await kafka_publisher.publish_event(
        topic="gateway.user.created",
        event_type="user.created",
        data={
            "user_id": str(db_user.id),
            "email": db_user.email,
            "username": db_user.username,
        },
    )

    logger.info(f"User registered: {db_user.email}")

    return {
        "id": str(db_user.id),
        "email": db_user.email,
        "username": db_user.username,
        "full_name": db_user.full_name,
        "is_active": db_user.is_active,
        "is_verified": db_user.is_verified,
        "roles": db_user.roles,
        "profile_image": db_user.profile_image,
        "bio": db_user.bio,
        "created_at": db_user.created_at,
        "updated_at": db_user.updated_at,
    }


@router.post(
    "/login",
    response_model=Token,
    summary="Login and get access token",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Authenticate user and return JWT tokens.

    Uses OAuth2 password flow for authentication.

    Args:
        form_data: OAuth2 password request form with username (email) and password.
        db: Database session.

    Returns:
        Token: Access and refresh tokens.

    Raises:
        HTTPException: If authentication fails.
    """
    # Authenticate user (username field contains email)
    user = await authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Incorrect email or password",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "USER_INACTIVE",
                "message": "User account is deactivated",
            },
        )

    # Create tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "scopes": user.scopes,
    }

    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Publish login event
    kafka_publisher = get_kafka_publisher()
    await kafka_publisher.publish_event(
        topic="gateway.user.logged_in",
        event_type="user.logged_in",
        data={
            "user_id": str(user.id),
            "email": user.email,
        },
    )

    logger.info(f"User logged in: {user.email}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
)
async def refresh_token(
    token_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Refresh the access token using a refresh token.

    Args:
        token_request: Refresh token request.
        db: Database session.

    Returns:
        Token: New access and refresh tokens.

    Raises:
        HTTPException: If refresh token is invalid.
    """
    # Verify refresh token
    payload = verify_token(token_request.refresh_token, token_type="refresh")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Invalid or expired refresh token",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Invalid token payload",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "USER_NOT_FOUND",
                "message": "User not found",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "USER_INACTIVE",
                "message": "User account is deactivated",
            },
        )

    # Create new tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "scopes": user.scopes,
    }

    access_token = create_access_token(data=token_data)
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    logger.info(f"Token refreshed for user: {user.email}")

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout user",
)
async def logout(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Logout the current user.

    Note: In a production system, you would add the token to a blacklist
    or use short-lived tokens with refresh token rotation.

    Args:
        current_user: The currently authenticated user.

    Returns:
        dict: Logout confirmation message.
    """
    # Publish logout event
    kafka_publisher = get_kafka_publisher()
    await kafka_publisher.publish_event(
        topic="gateway.user.logged_out",
        event_type="user.logged_out",
        data={
            "user_id": str(current_user.id),
            "email": current_user.email,
        },
    )

    logger.info(f"User logged out: {current_user.email}")

    return {
        "status": "success",
        "message": "Successfully logged out",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Get the current authenticated user's information.

    Args:
        current_user: The currently authenticated user.

    Returns:
        UserResponse: Current user data.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "roles": current_user.roles,
        "profile_image": current_user.profile_image,
        "bio": current_user.bio,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
    }
