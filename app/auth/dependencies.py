from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from prisma.models import User
from app.auth.jwt import decode_token
from app.auth.cookies import COOKIE_NAME
from app.db import get_db
from prisma import Prisma

# Bearer token support (auto_error=False for fallback to cookie)
security = HTTPBearer(auto_error=False)


def get_token_from_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """Extract token from cookie (preferred) or Authorization header (fallback)"""
    # 1. Try httpOnly cookie first (more secure)
    cookie_token = request.cookies.get(COOKIE_NAME)
    if cookie_token:
        return cookie_token

    # 2. Fallback to Bearer header (for API clients/testing)
    if credentials:
        return credentials.credentials

    return None


async def get_current_user(
    token: Optional[str] = Depends(get_token_from_request),
    db: Prisma = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await db.user.find_unique(where={"id": user_id})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(get_token_from_request),
    db: Prisma = Depends(get_db)
) -> User | None:
    """Get current user if authenticated, None otherwise"""
    if not token:
        return None

    user_id = decode_token(token)
    if not user_id:
        return None

    user = await db.user.find_unique(where={"id": user_id})
    if not user or user.deleted_at:
        return None

    return user
