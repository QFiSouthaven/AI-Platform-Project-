"""
User CRUD routes for User Gateway.

Provides endpoints for user management operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Security, status
from passlib.context import CryptContext
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import (
    User,
    UserResponse,
    UserUpdate,
    UserPasswordUpdate,
    UserList,
)
from app.auth.oauth2 import (
    get_current_active_user,
    get_current_superuser,
)
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


@router.get(
    "/",
    response_model=UserList,
    summary="List all users",
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email or username"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, Any]:
    """
    List all users with pagination and filtering.

    Requires superuser privileges.

    Args:
        page: Page number (1-indexed).
        page_size: Number of items per page.
        search: Optional search term for email or username.
        is_active: Optional filter by active status.
        db: Database session.
        current_user: Current authenticated superuser.

    Returns:
        UserList: Paginated list of users.
    """
    # Build query
    query = select(User)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(search_term),
                User.username.ilike(search_term),
            )
        )

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())

    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return {
        "users": [
            {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "roles": user.roles,
                "profile_image": user.profile_image,
                "bio": user.bio,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
            for user in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Get a user by their ID.

    Users can only view their own profile unless they are superusers.

    Args:
        user_id: User UUID.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        UserResponse: User data.

    Raises:
        HTTPException: If user not found or access denied.
    """
    # Check access permissions
    if str(current_user.id) != str(user_id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ACCESS_DENIED",
                "message": "You can only view your own profile",
            },
        )

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "USER_NOT_FOUND",
                "message": f"User with ID {user_id} not found",
            },
        )

    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "roles": user.roles,
        "profile_image": user.profile_image,
        "bio": user.bio,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Update user information.

    Users can only update their own profile unless they are superusers.

    Args:
        user_id: User UUID.
        user_update: User update data.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        UserResponse: Updated user data.

    Raises:
        HTTPException: If user not found, access denied, or validation fails.
    """
    # Check access permissions
    if str(current_user.id) != str(user_id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ACCESS_DENIED",
                "message": "You can only update your own profile",
            },
        )

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "USER_NOT_FOUND",
                "message": f"User with ID {user_id} not found",
            },
        )

    # Check for duplicate email
    if user_update.email and user_update.email != user.email:
        result = await db.execute(
            select(User).where(User.email == user_update.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "EMAIL_EXISTS",
                    "message": "A user with this email already exists",
                },
            )

    # Check for duplicate username
    if user_update.username and user_update.username != user.username:
        result = await db.execute(
            select(User).where(User.username == user_update.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "USERNAME_EXISTS",
                    "message": "A user with this username already exists",
                },
            )

    # Update user fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(user)

    # Publish user updated event
    kafka_publisher = get_kafka_publisher()
    await kafka_publisher.publish_event(
        topic="gateway.user.updated",
        event_type="user.updated",
        data={
            "user_id": str(user.id),
            "email": user.email,
            "updated_fields": list(update_data.keys()),
        },
    )

    logger.info(f"User updated: {user.email}")

    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "roles": user.roles,
        "profile_image": user.profile_image,
        "bio": user.bio,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


@router.patch(
    "/{user_id}/password",
    status_code=status.HTTP_200_OK,
    summary="Update user password",
)
async def update_password(
    user_id: UUID,
    password_update: UserPasswordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Update user password.

    Users can only update their own password.

    Args:
        user_id: User UUID.
        password_update: Password update data.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: If user not found, access denied, or current password is wrong.
    """
    # Check access permissions
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ACCESS_DENIED",
                "message": "You can only update your own password",
            },
        )

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "USER_NOT_FOUND",
                "message": f"User with ID {user_id} not found",
            },
        )

    # Verify current password
    if not verify_password(password_update.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PASSWORD",
                "message": "Current password is incorrect",
            },
        )

    # Update password
    user.hashed_password = get_password_hash(password_update.new_password)
    user.updated_at = datetime.utcnow()

    await db.commit()

    # Publish password changed event
    kafka_publisher = get_kafka_publisher()
    await kafka_publisher.publish_event(
        topic="gateway.user.password_changed",
        event_type="user.password_changed",
        data={
            "user_id": str(user.id),
            "email": user.email,
        },
    )

    logger.info(f"Password updated for user: {user.email}")

    return {
        "status": "success",
        "message": "Password updated successfully",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete user",
)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, Any]:
    """
    Delete a user.

    Requires superuser privileges.

    Args:
        user_id: User UUID.
        db: Database session.
        current_user: Current authenticated superuser.

    Returns:
        dict: Deletion confirmation.

    Raises:
        HTTPException: If user not found.
    """
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "USER_NOT_FOUND",
                "message": f"User with ID {user_id} not found",
            },
        )

    # Don't allow deleting yourself
    if str(current_user.id) == str(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CANNOT_DELETE_SELF",
                "message": "You cannot delete your own account",
            },
        )

    email = user.email

    # Delete user
    await db.delete(user)
    await db.commit()

    # Publish user deleted event
    kafka_publisher = get_kafka_publisher()
    await kafka_publisher.publish_event(
        topic="gateway.user.deleted",
        event_type="user.deleted",
        data={
            "user_id": str(user_id),
            "email": email,
        },
    )

    logger.info(f"User deleted: {email}")

    return {
        "status": "success",
        "message": f"User {user_id} deleted successfully",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post(
    "/{user_id}/activate",
    status_code=status.HTTP_200_OK,
    summary="Activate user account",
)
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, Any]:
    """
    Activate a user account.

    Requires superuser privileges.

    Args:
        user_id: User UUID.
        db: Database session.
        current_user: Current authenticated superuser.

    Returns:
        dict: Activation confirmation.

    Raises:
        HTTPException: If user not found.
    """
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "USER_NOT_FOUND",
                "message": f"User with ID {user_id} not found",
            },
        )

    user.is_active = True
    user.updated_at = datetime.utcnow()

    await db.commit()

    # Publish user activated event
    kafka_publisher = get_kafka_publisher()
    await kafka_publisher.publish_event(
        topic="gateway.user.activated",
        event_type="user.activated",
        data={
            "user_id": str(user.id),
            "email": user.email,
        },
    )

    logger.info(f"User activated: {user.email}")

    return {
        "status": "success",
        "message": f"User {user_id} activated successfully",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post(
    "/{user_id}/deactivate",
    status_code=status.HTTP_200_OK,
    summary="Deactivate user account",
)
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, Any]:
    """
    Deactivate a user account.

    Requires superuser privileges.

    Args:
        user_id: User UUID.
        db: Database session.
        current_user: Current authenticated superuser.

    Returns:
        dict: Deactivation confirmation.

    Raises:
        HTTPException: If user not found.
    """
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "USER_NOT_FOUND",
                "message": f"User with ID {user_id} not found",
            },
        )

    # Don't allow deactivating yourself
    if str(current_user.id) == str(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CANNOT_DEACTIVATE_SELF",
                "message": "You cannot deactivate your own account",
            },
        )

    user.is_active = False
    user.updated_at = datetime.utcnow()

    await db.commit()

    # Publish user deactivated event
    kafka_publisher = get_kafka_publisher()
    await kafka_publisher.publish_event(
        topic="gateway.user.deactivated",
        event_type="user.deactivated",
        data={
            "user_id": str(user.id),
            "email": user.email,
        },
    )

    logger.info(f"User deactivated: {user.email}")

    return {
        "status": "success",
        "message": f"User {user_id} deactivated successfully",
        "timestamp": datetime.utcnow().isoformat(),
    }
