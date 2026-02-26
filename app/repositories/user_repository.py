from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.base import BaseRepository
from typing import Optional


class UserRepository(BaseRepository[User]):
    def __init__(self, db):
        super().__init__(db, User)

    def get_by_email(self, email):
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, email, username, hashed_password):
        return self.create(
            email=email,
            username=username,
            hashed_password=hashed_password
        )