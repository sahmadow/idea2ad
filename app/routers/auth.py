from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel, EmailStr, Field
from prisma import Prisma
from app.db import get_db
from app.auth.password import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.auth.dependencies import get_current_user
from app.auth.cookies import COOKIE_NAME, get_cookie_settings
from prisma.models import User
import logging

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    created_at: str

    class Config:
        from_attributes = True


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    response: Response,
    db: Prisma = Depends(get_db)
):
    """Register new user account"""
    # Check if email exists
    existing = await db.user.find_unique(where={"email": request.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    try:
        user = await db.user.create(
            data={
                "email": request.email,
                "password_hash": hash_password(request.password),
                "name": request.name,
            }
        )
        logger.info(f"User registered: {user.email}")
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

    # Create token and set httpOnly cookie
    token = create_access_token(user.id)
    cookie_settings = get_cookie_settings()
    response.set_cookie(value=token, **cookie_settings)

    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: Prisma = Depends(get_db)
):
    """Login with email and password"""
    user = await db.user.find_unique(where={"email": request.email})

    if not user or user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    logger.info(f"User logged in: {user.email}")

    # Create token and set httpOnly cookie
    token = create_access_token(user.id)
    cookie_settings = get_cookie_settings()
    response.set_cookie(value=token, **cookie_settings)

    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        created_at=current_user.created_at.isoformat()
    )


@router.post("/logout")
async def logout(response: Response):
    """Clear auth cookie"""
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"message": "Logged out"}
