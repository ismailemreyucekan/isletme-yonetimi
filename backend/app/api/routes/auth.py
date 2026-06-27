"""Auth uçları: kayıt, giriş, token yenileme, profil."""

from __future__ import annotations

import jwt
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentRestaurant, CurrentUser, DbSession
from app.core.security import decode_token
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.schemas.restaurant import RestaurantOut
from app.schemas.user import UserOut
from app.services import auth_service
from app.services.auth_service import AuthError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: DbSession) -> AuthResponse:
    """Yeni işletme + owner hesabı oluşturur ve token döner."""
    try:
        owner = await auth_service.register_restaurant(db, data)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    tokens = auth_service.issue_tokens(owner)
    return AuthResponse(**tokens.model_dump(), user=UserOut.model_validate(owner))


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: DbSession) -> AuthResponse:
    try:
        user = await auth_service.authenticate(db, data.email, data.password)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    tokens = auth_service.issue_tokens(user)
    return AuthResponse(**tokens.model_dump(), user=UserOut.model_validate(user))


@router.post("/refresh", response_model=TokenPair)
async def refresh(data: RefreshRequest, db: DbSession) -> TokenPair:
    try:
        payload = decode_token(data.refresh_token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz token"
        ) from exc

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz token türü"
        )

    try:
        user = await auth_service.get_user_for_refresh(
            db, payload.get("sub", ""), payload.get("rid", "")
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    return auth_service.issue_tokens(user)


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.get("/me/restaurant", response_model=RestaurantOut)
async def my_restaurant(restaurant: CurrentRestaurant) -> RestaurantOut:
    return RestaurantOut.model_validate(restaurant)
