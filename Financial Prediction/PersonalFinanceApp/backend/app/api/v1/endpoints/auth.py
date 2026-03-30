"""Authentication endpoints — register, login, and Google Sign-In."""

import logging
import re
import secrets
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from app.core.auth import (
    create_access_token,
    get_current_active_user,
    get_password_hash,
    verify_password,
)
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import GoogleSignInRequest, Token, UserCreate, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def _unique_username_from_email(email: str, db: Session) -> str:
    """Derive a valid unique username from the email local part."""
    local = (email.split("@")[0] if "@" in email else email).lower()
    base = re.sub(r"[^a-z0-9_-]", "_", local).strip("_") or "user"
    if len(base) < 3:
        base = (base + "usr")[:3]
    base = base[:80]
    candidate = base
    n = 0
    while db.query(User).filter(User.username == candidate).first():
        n += 1
        suffix = str(n)
        candidate = f"{base[: 100 - len(suffix)]}{suffix}"
    return candidate


def _verify_google_id_token(raw_token: str) -> dict[str, Any]:
    """Validate JWT from Google Identity Services; return decoded claims."""
    client_id = (settings.GOOGLE_OAUTH_CLIENT_ID or "").strip()
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured on this server.",
        )
    try:
        return google_id_token.verify_oauth2_token(
            raw_token,
            google_requests.Request(),
            client_id,
        )
    except ValueError as e:
        logger.info("Google ID token verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token.",
        ) from e


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> Token:
    """Create a new user account and return a JWT access token."""
    existing = (
        db.query(User)
        .filter((User.email == user_in.email) | (User.username == user_in.username))
        .first()
    )
    if existing:
        field = "email" if existing.email == user_in.email else "username"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A user with this {field} already exists.",
        )
    user = User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return Token(access_token=create_access_token({"sub": str(user.id)}))


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate with username (or email) and password; return JWT."""
    user = (
        db.query(User)
        .filter(
            (User.username == form_data.username) | (User.email == form_data.username)
        )
        .first()
    )
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return Token(access_token=create_access_token({"sub": str(user.id)}))


@router.post("/google", response_model=Token, summary="Sign in or register with Google")
def google_sign_in(body: GoogleSignInRequest, db: Session = Depends(get_db)) -> Token:
    """
    Accepts the Google **credential** JWT from the GIS button, verifies it,
    then logs in an existing user (by ``google_sub`` or linked email) or
    creates a new account.
    """
    claims = _verify_google_id_token(body.id_token)
    sub: Optional[str] = claims.get("sub")
    email: Optional[str] = claims.get("email")
    raw_verified = claims.get("email_verified", False)
    if isinstance(raw_verified, str):
        email_verified = raw_verified.lower() in ("true", "1", "yes")
    else:
        email_verified = bool(raw_verified)
    name = claims.get("name")

    if not sub or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token is missing required claims.",
        )
    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google email is not verified.",
        )

    user = db.query(User).filter(User.google_sub == sub).first()
    if user is None:
        user = db.query(User).filter(User.email == email).first()
        if user is not None:
            if user.google_sub is not None and user.google_sub != sub:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This email is already linked to another account.",
                )
            user.google_sub = sub
            if name and not (user.full_name or "").strip():
                user.full_name = name
            db.commit()
            db.refresh(user)

    if user is None:
        username = _unique_username_from_email(email, db)
        random_secret = secrets.token_urlsafe(48)
        user = User(
            email=email,
            username=username,
            full_name=name if isinstance(name, str) else None,
            hashed_password=get_password_hash(random_secret),
            google_sub=sub,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    return Token(access_token=create_access_token({"sub": str(user.id)}))


@router.get("/config", summary="Public auth configuration")
def get_auth_config() -> dict:
    """Return public auth configuration so the frontend can initialise Google OAuth."""
    google_configured = bool((settings.GOOGLE_OAUTH_CLIENT_ID or "").strip())
    return {
        "google_oauth_enabled": google_configured,
        "google_client_id": settings.GOOGLE_OAUTH_CLIENT_ID.strip() if google_configured else None,
    }


@router.get("/me", response_model=UserResponse, summary="Current user profile")
def read_me(current_user: User = Depends(get_current_active_user)) -> User:
    """Return the authenticated user's profile (requires Bearer token)."""
    return current_user
