"""
Input validators and sanitizers for User Gateway.

Provides validation and sanitization functions for user input.
"""

import html
import re
from typing import Optional


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate.

    Returns:
        bool: True if email is valid, False otherwise.
    """
    if not email:
        return False

    # RFC 5322 compliant email regex (simplified)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> dict:
    """
    Validate password strength and return detailed feedback.

    Args:
        password: Password to validate.

    Returns:
        dict: Validation result with 'valid' bool and 'errors' list.
    """
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if len(password) > 100:
        errors.append("Password must be no more than 100 characters long")

    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        errors.append("Password must contain at least one special character")

    # Check for common weak patterns
    common_patterns = [
        r'(.)\1{2,}',  # Same character repeated 3+ times
        r'(012|123|234|345|456|567|678|789)',  # Sequential numbers
        r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # Sequential letters
    ]

    for pattern in common_patterns:
        if re.search(pattern, password.lower()):
            errors.append("Password contains common weak patterns")
            break

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "strength": calculate_password_strength(password) if len(errors) == 0 else 0,
    }


def calculate_password_strength(password: str) -> int:
    """
    Calculate password strength score (0-100).

    Args:
        password: Password to evaluate.

    Returns:
        int: Strength score from 0 to 100.
    """
    score = 0

    # Length scoring
    length = len(password)
    if length >= 8:
        score += 20
    if length >= 12:
        score += 10
    if length >= 16:
        score += 10

    # Character variety scoring
    if any(c.isupper() for c in password):
        score += 15
    if any(c.islower() for c in password):
        score += 15
    if any(c.isdigit() for c in password):
        score += 15
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        score += 15

    return min(score, 100)


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize a string input by escaping HTML and trimming whitespace.

    Args:
        value: String to sanitize.
        max_length: Optional maximum length to truncate to.

    Returns:
        str: Sanitized string.
    """
    if not value:
        return ""

    # Strip whitespace
    sanitized = value.strip()

    # Escape HTML entities to prevent XSS
    sanitized = html.escape(sanitized)

    # Remove any null bytes
    sanitized = sanitized.replace('\x00', '')

    # Truncate if max_length specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def validate_username(username: str) -> dict:
    """
    Validate username format and return detailed feedback.

    Args:
        username: Username to validate.

    Returns:
        dict: Validation result with 'valid' bool and 'errors' list.
    """
    errors = []

    if not username:
        errors.append("Username is required")
        return {"valid": False, "errors": errors}

    if len(username) < 3:
        errors.append("Username must be at least 3 characters long")

    if len(username) > 100:
        errors.append("Username must be no more than 100 characters long")

    # Check for valid characters
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        errors.append(
            "Username can only contain alphanumeric characters, underscores, and hyphens"
        )

    # Check if starts with digit
    if username and username[0].isdigit():
        errors.append("Username cannot start with a digit")

    # Check for reserved usernames
    reserved = [
        "admin", "administrator", "root", "system", "api",
        "login", "logout", "register", "user", "users",
        "profile", "settings", "help", "support", "null",
        "undefined", "anonymous", "guest", "test",
    ]
    if username.lower() in reserved:
        errors.append("This username is reserved and cannot be used")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def validate_uuid(value: str) -> bool:
    """
    Validate UUID format.

    Args:
        value: String to validate as UUID.

    Returns:
        bool: True if valid UUID format, False otherwise.
    """
    if not value:
        return False

    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, value.lower()))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing potentially dangerous characters.

    Args:
        filename: Filename to sanitize.

    Returns:
        str: Sanitized filename.
    """
    if not filename:
        return ""

    # Remove path separators
    sanitized = filename.replace('/', '').replace('\\', '')

    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')

    # Remove other potentially dangerous characters
    sanitized = re.sub(r'[<>:"|?*]', '', sanitized)

    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        max_name_len = 255 - len(ext) - 1 if ext else 255
        sanitized = f"{name[:max_name_len]}.{ext}" if ext else name[:255]

    return sanitized


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate.

    Returns:
        bool: True if valid URL format, False otherwise.
    """
    if not url:
        return False

    pattern = (
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$'
    )
    return bool(re.match(pattern, url, re.IGNORECASE))


def normalize_email(email: str) -> str:
    """
    Normalize email address to lowercase and strip whitespace.

    Args:
        email: Email to normalize.

    Returns:
        str: Normalized email address.
    """
    if not email:
        return ""

    return email.strip().lower()
