from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.base import BaseRepository
from typing import Optional, List


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username(self, username: str) -> List[User]:
        return self.db.query(User).filter(User.username == username).all()

    def create_user(self, email: str, username: str, hashed_password: str):
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user