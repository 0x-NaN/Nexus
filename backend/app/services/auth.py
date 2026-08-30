"""
services/auth.py — Authentication service.
Password hashing with bcrypt, JWT token creation/validation.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import os

from jose import jwt, JWTError
from passlib.context import CryptContext
from passlib.hash import bcrypt

from app.models import TokenPayload


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, email: str) -> str:
    """Create a short-lived access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str, email: str) -> str:
    """Create a long-lived refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenPayload]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None


def create_token_pair(user_id: str, email: str) -> tuple[str, str]:
    """Create both access and refresh tokens."""
    access = create_access_token(user_id, email)
    refresh = create_refresh_token(user_id, email)
    return access, refresh


def verify_refresh_token(refresh_token: str) -> Optional[TokenPayload]:
    """Validate a refresh token and return its payload."""
    payload = decode_token(refresh_token)
    if payload and payload.type == "refresh":
        return payload
    return None