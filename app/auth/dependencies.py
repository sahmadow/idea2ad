from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prisma.models import User
from app.auth.jwt import decode_token
from app.db import get_db
from prisma import Prisma

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Prisma = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    user_id = decode_token(credentials.credentials)

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
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: Prisma = Depends(get_db)
) -> User | None:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None

    user_id = decode_token(credentials.credentials)
    if not user_id:
        return None

    user = await db.user.find_unique(where={"id": user_id})
    if not user or user.deleted_at:
        return None

    return user
