from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from jose import JWTError
from app.core.database import get_db
from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)


async def get_token_from_cookie(request: Request) -> str | None:
    """Получение токена из cookie"""
    token = request.cookies.get("access_token")
    if token:
        logger.debug(f"Found token in cookie: {token[:20]}...")
        if token.startswith("Bearer "):
            return token[7:]  # Убираем "Bearer "
        return token
    logger.debug("No token in cookie")
    return None


async def get_current_user(
        request: Request,
        db: Session = Depends(get_db)
):
    """Получение текущего пользователя по токену из cookie"""
    token = await get_token_from_cookie(request)

    if not token:
        return None

    payload = decode_access_token(token)
    if payload is None:
        logger.warning("Failed to decode token")
        return None

    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("No user_id in token")
        return None

    try:
        user_id = int(user_id)
    except ValueError:
        logger.warning(f"Invalid user_id in token: {user_id}")
        return None

    user_repo = UserRepository(db)
    user = user_repo.get(user_id)

    if user:
        logger.debug(f"Found user: {user.email}")
    else:
        logger.warning(f"User not found for id: {user_id}")

    return user


async def get_current_active_user(
        current_user=Depends(get_current_user)
):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user