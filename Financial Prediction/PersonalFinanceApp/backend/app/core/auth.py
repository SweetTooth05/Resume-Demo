"""
Authentication utilities.

Provides JWT token creation/validation and FastAPI dependency functions for
obtaining the current authenticated user.
"""

import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt as _bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User


def _prehash(password: str) -> str:
    """SHA-256 + base64-encode password so bcrypt always receives ≤44 bytes.

    bcrypt's hard limit is 72 bytes. Pre-hashing through SHA-256 and
    base64-encoding produces a fixed 44-character ASCII string, preserving
    the full entropy of arbitrarily long passwords without hitting the limit.
    """
    return base64.b64encode(
        hashlib.sha256(password.encode("utf-8")).digest()
    ).decode("utf-8")

# ---------------------------------------------------------------------------
# Bearer-token extraction
# ---------------------------------------------------------------------------
security = HTTPBearer()

# ---------------------------------------------------------------------------
# Reusable 401 exception (avoids creating a new object on every request)
# ---------------------------------------------------------------------------
_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Parameters
    ----------
    data:
        Payload to embed in the token.  Must include a ``sub`` key whose value
        is a string representation of the user ID.
    expires_delta:
        Optional lifetime override.  Defaults to ``ACCESS_TOKEN_EXPIRE_MINUTES``
        from settings.

    Returns
    -------
    str
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True when *plain_password* matches *hashed_password*."""
    return _bcrypt.checkpw(
        _prehash(plain_password).encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    return _bcrypt.hashpw(
        _prehash(password).encode("utf-8"),
        _bcrypt.gensalt(),
    ).decode("utf-8")


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency — decode the Bearer token and return the User row.

    Raises HTTP 401 on any token or user lookup failure.
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        # ``sub`` is stored as a string in the token (JWT spec recommendation)
        raw_sub: Optional[str] = payload.get("sub")
        if raw_sub is None:
            raise _CREDENTIALS_EXCEPTION
        user_id = int(raw_sub)
    except (JWTError, ValueError):
        raise _CREDENTIALS_EXCEPTION

    user: Optional[User] = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise _CREDENTIALS_EXCEPTION

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency — extend ``get_current_user`` to reject inactive users.

    Raises HTTP 403 (not 400) to clearly distinguish authorisation failures
    from bad-request errors.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return current_user
