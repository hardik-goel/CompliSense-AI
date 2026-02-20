# [file name]: saas/app/auth.py (Fixed Authentication)
"""
Fixed Authentication system with proper session handling
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
import jwt
import datetime
from typing import Optional
import secrets
import json
from passlib.hash import bcrypt

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# In production, use environment variables
SECRET_KEY = "complisense-secret-key-2024"
ALGORITHM = "HS256"

# Temporary in-memory storage
users_db = {}
sessions_db = {}


class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    company: Optional[str] = None

    @validator("password")
    def validate_password_strength(cls, v: str) -> str:
        """Enforce basic password strength requirements."""
        # bcrypt only supports passwords up to 72 bytes reliably
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 characters (72 bytes) long.")
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "Password must contain at least one uppercase letter, one lowercase letter, and one digit."
            )
        return v


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    company: Optional[str]
    created_at: str
    tier: str


def create_jwt_token(user_id: str, email: str) -> str:
    """Create JWT token for user"""
    token_data = {
        "sub": user_id,
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)


def hash_password(plain_password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    return bcrypt.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a bcrypt hash.
    """
    try:
        return bcrypt.verify(plain_password, hashed_password)
    except Exception:
        return False


async def get_current_user(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current user from token - fixed version"""
    try:
        # Try to get token from Authorization header first
        token = credentials.credentials
    except:
        # Fall back to cookie if no header
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        # Find user in database
        user = next((u for u in users_db.values() if u["id"] == user_id), None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@router.post("/register", response_model=dict)
async def register(user_data: UserRegister, response: Response):
    """Register a new user - fixed with cookie setting"""
    if user_data.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

    # Create user
    user_id = f"user_{secrets.token_hex(8)}"
    user = {
        "id": user_id,
        "email": user_data.email,
        # Store only a hashed password
        "password_hash": hash_password(user_data.password),
        "full_name": user_data.full_name,
        "company": user_data.company,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "tier": "free"
    }

    users_db[user_data.email] = user

    # Generate JWT token
    token = create_jwt_token(user_id, user_data.email)

    # Set cookie for browser authentication
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=24 * 60 * 60,  # 24 hours
        expires=24 * 60 * 60,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse(**user)
    }


@router.post("/login", response_model=dict)
async def login(login_data: UserLogin, response: Response):
    """User login with cookie setting"""
    user = users_db.get(login_data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Backwards compatibility: if an old plaintext password field exists, allow it once
    stored_hash = user.get("password_hash")
    if stored_hash:
        valid = verify_password(login_data.password, stored_hash)
    else:
        # Fallback for any legacy in-memory data
        valid = login_data.password == user.get("password")

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Generate JWT token
    token = create_jwt_token(user["id"], user["email"])

    # Set cookie for browser authentication
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=24 * 60 * 60,
        expires=24 * 60 * 60,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse(**user)
    }


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing cookie"""
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(**current_user)