# [file name]: saas/app/auth.py
"""
Authentication system for SaaS dashboard
Handles user registration, login, and session management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
import datetime
from typing import Optional

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# In production, use environment variables
SECRET_KEY = "complisense-secret-key-2024"  # Change this in production!
ALGORITHM = "HS256"

# Temporary in-memory storage (replace with database)
users_db = {}
sessions_db = {}


class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    company: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    company: Optional[str]
    created_at: str


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    if user_data.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

    # In production, hash the password!
    user_id = f"user_{len(users_db) + 1}"
    user = {
        "id": user_id,
        "email": user_data.email,
        "password": user_data.password,  # Hash this in production!
        "full_name": user_data.full_name,
        "company": user_data.company,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "tier": "free"  # Default to free tier
    }

    users_db[user_data.email] = user

    return UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        company=user["company"],
        created_at=user["created_at"]
    )


@router.post("/login")
async def login(login_data: UserLogin):
    """User login and token generation"""
    user = users_db.get(login_data.email)

    if not user or user["password"] != login_data.password:  # Compare hashed passwords in production
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Generate JWT token
    token_data = {
        "sub": user["id"],
        "email": user["email"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    # Store session
    sessions_db[token] = {
        "user_id": user["id"],
        "email": user["email"],
        "login_time": datetime.datetime.utcnow().isoformat()
    }

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            company=user["company"],
            created_at=user["created_at"]
        )
    }


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user from token"""
    token = credentials.credentials

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


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        company=current_user["company"],
        created_at=current_user["created_at"]
    )