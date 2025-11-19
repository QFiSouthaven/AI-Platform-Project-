"""
JWT token handler for User Gateway.

Provides functions for creating and verifying JWT tokens.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token.
        expires_delta: Optional custom expiration time.

    Returns:
        str: Encoded JWT token.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Data to encode in the token.
        expires_delta: Optional custom expiration time.

    Returns:
        str: Encoded JWT refresh token.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify.
        token_type: Expected token type ("access" or "refresh").

    Returns:
        Optional[Dict[str, Any]]: Decoded token payload if valid, None otherwise.

    Raises:
        JWTError: If token verification fails.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

        # Verify token type
        if payload.get("type") != token_type:
            logger.warning(
                f"Invalid token type: expected {token_type}, got {payload.get('type')}"
            )
            return None

        # Check if token is expired
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            logger.warning("Token has expired")
            return None

        return payload

    except JWTError as e:
        logger.error(f"JWT verification error: {str(e)}")
        raise


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a JWT token without verification.

    Useful for debugging or extracting data from expired tokens.

    Args:
        token: JWT token to decode.

    Returns:
        Optional[Dict[str, Any]]: Decoded token payload, or None if decoding fails.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False},
        )
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Get the expiration time of a token.

    Args:
        token: JWT token to check.

    Returns:
        Optional[datetime]: Expiration datetime, or None if not found.
    """
    payload = decode_token(token)
    if payload and "exp" in payload:
        return datetime.utcfromtimestamp(payload["exp"])
    return None
