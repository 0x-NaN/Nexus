"""
routers/auth.py — Authentication routes.
Register, login, token refresh, logout, get current user.
"""
from datetime import datetime, timezone
import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database import database
from app.models import (
    UserOut, UserCreate, UserLogin, Token, TokenRefresh, TokenPayload
)
from app.services.auth import (
    hash_password, verify_password, create_token_pair,
    decode_token, verify_refresh_token
)

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> TokenPayload:
    """Dependency to get current user from access token."""
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> str:
    """Dependency to get current user ID from access token."""
    payload = await get_current_user(credentials)
    return payload.sub


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user."""
    # Check if email already exists
    existing = await database.fetch_one(
        "SELECT id FROM users WHERE email = :email",
        {"email": user_data.email.lower()}
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password and create user
    hashed_pw = hash_password(user_data.password)
    user_id = f"usr_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"

    await database.execute(
        """
        INSERT INTO users (id, email, password_hash, full_name, is_active, created_at)
        VALUES (:id, :email, :password_hash, :full_name, true, NOW())
        """,
        {
            "id": user_id,
            "email": user_data.email.lower(),
            "password_hash": hash_password(user_data.password),
            "full_name": user_data.full_name,
        }
    )

    # Create tokens
    access_token, refresh_token = create_token_pair(user_id, user_data.email.lower())
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login and get access + refresh tokens."""
    user = await database.fetch_one(
        "SELECT id, email, password_hash FROM users WHERE email = :email",
        {"email": credentials.email.lower()}
    )
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token, refresh_token = create_token_pair(user["id"], user["email"])
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh):
    """Refresh access token using refresh token."""
    payload = verify_refresh_token(token_data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Create new token pair
    access_token, refresh_token = create_token_pair(payload.sub, payload.email)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout():
    """Logout - client should discard tokens."""
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
async def get_current_user_info(current_user: TokenPayload = Depends(get_current_user)):
    """Get current user profile."""
    user = await database.fetch_one(
        "SELECT id, email, full_name, is_active, created_at FROM users WHERE id = :id",
        {"id": current_user.sub}
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserOut(**user)