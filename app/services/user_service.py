from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, get_password_hash, create_access_token
from fastapi import HTTPException, status
from datetime import timedelta
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register_user(self, email: str, username: str, password: str):
        try:
            if self.user_repo.get_by_email(email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Этот email уже зарегистрирован"
                )

            hashed_password = get_password_hash(password)

            user = self.user_repo.create_user(
                email=email,
                username=username,
                hashed_password=hashed_password
            )

            logger.info(f"User registered successfully: {email}")
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при регистрации"
            )

    def authenticate_user(self, email: str, password: str):
        try:
            user = self.user_repo.get_by_email(email)

            if not user:
                return None

            if not verify_password(password, user.hashed_password):
                return None

            return user

        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None

    def create_user_token(self, user_id: int) -> str:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user_id)},
            expires_delta=access_token_expires
        )
        return access_token