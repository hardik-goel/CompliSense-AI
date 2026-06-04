from __future__ import annotations

import datetime as dt
import logging
import secrets
from typing import Any

import bcrypt
import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, field_validator

from saas.app.config import settings
from saas.app.database import get_collection, serialize_document

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

SECRET_KEY = settings.jwt_secret
ALGORITHM = settings.jwt_algorithm


class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    company: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 characters long.")
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        has_upper = any(char.isupper() for char in value)
        has_lower = any(char.islower() for char in value)
        has_digit = any(char.isdigit() for char in value)
        if not (has_upper and has_lower and has_digit):
            raise ValueError("Password must contain at least one uppercase letter, one lowercase letter, and one digit.")
        return value


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    company: str | None = None
    created_at: str
    tier: str


def users_collection():
    return get_collection("users")


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_jwt_token(user_id: str, email: str) -> str:
    now = dt.datetime.utcnow()
    token_data = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + dt.timedelta(hours=settings.jwt_expiration_hours),
    }
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)


def decode_jwt_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def _sanitize_user(user: dict[str, Any]) -> dict[str, Any]:
    clean = serialize_document(user)
    clean.pop("password_hash", None)
    return clean


def _find_user_by_id(user_id: str) -> dict[str, Any] | None:
    user = users_collection().find_one({"id": user_id})
    return _sanitize_user(user) if user else None


def _get_token_from_request(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
    access_token: str | None,
) -> str | None:
    if isinstance(credentials, HTTPAuthorizationCredentials) and credentials.credentials:
        return credentials.credentials
    if access_token:
        return access_token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return None


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    access_token: str | None = Cookie(default=None),
) -> dict[str, Any] | None:
    cached_user = getattr(request.state, "current_user", None)
    if cached_user is not None:
        return cached_user

    token = _get_token_from_request(request, credentials, access_token)
    if not token:
        return None

    try:
        payload = decode_jwt_token(token)
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("JWT missing subject claim")
            return None
        user = _find_user_by_id(user_id)
        if not user:
            logger.warning("JWT resolved to unknown user_id=%s", user_id)
            return None
        request.state.current_user = user
        return user
    except jwt.ExpiredSignatureError:
        logger.warning("Expired JWT received from %s", request.client.host if request.client else "unknown")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT received from %s", request.client.host if request.client else "unknown")
        return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    access_token: str | None = Cookie(default=None),
) -> dict[str, Any]:
    user = await get_current_user_optional(request, credentials, access_token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def _set_auth_cookie(response: Response, token: str) -> None:
    cookie_args = {
        "key": "access_token",
        "value": token,
        "httponly": True,
        "secure": settings.secure_cookies or settings.is_production,
        "samesite": "lax",
        "max_age": settings.jwt_expiration_hours * 3600,
        "expires": settings.jwt_expiration_hours * 3600,
        "path": "/",
    }
    if settings.cookie_domain:
        cookie_args["domain"] = settings.cookie_domain
    response.set_cookie(**cookie_args)


@router.post("/register", response_model=dict)
async def register(user_data: UserRegister, response: Response):
    email = _normalize_email(user_data.email)
    if users_collection().find_one({"email": email}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    user = {
        "id": f"user_{secrets.token_hex(8)}",
        "email": email,
        "password_hash": hash_password(user_data.password),
        "full_name": user_data.full_name.strip(),
        "company": user_data.company.strip() if user_data.company else None,
        "created_at": dt.datetime.utcnow(),
        "tier": "free",
    }
    users_collection().insert_one(user)

    token = create_jwt_token(user["id"], user["email"])
    _set_auth_cookie(response, token)
    logger.info("Registered user email=%s", email)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse(**_sanitize_user(user)),
    }


@router.post("/login", response_model=dict)
async def login(login_data: UserLogin, response: Response):
    email = _normalize_email(login_data.email)
    user = users_collection().find_one({"email": email})
    if not user:
        logger.warning("Login failed for unknown email=%s", email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    password_hash = user.get("password_hash")
    if not password_hash or not verify_password(login_data.password, password_hash):
        logger.warning("Login failed for email=%s", email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    clean_user = _sanitize_user(user)
    token = create_jwt_token(clean_user["id"], clean_user["email"])
    _set_auth_cookie(response, token)
    logger.info("Login successful for email=%s", email)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse(**clean_user),
    }


@router.post("/logout")
async def logout(response: Response):
    delete_args = {
        "key": "access_token",
        "path": "/",
        "secure": settings.secure_cookies or settings.is_production,
        "httponly": True,
        "samesite": "lax",
    }
    if settings.cookie_domain:
        delete_args["domain"] = settings.cookie_domain
    response.delete_cookie(**delete_args)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict[str, Any] = Depends(get_current_user)):
    return UserResponse(**current_user)
