from sqlalchemy.orm import Session
from app.models.board import Board
from app.repositories.base import BaseRepository
from typing import List, Optional


class BoardRepository(BaseRepository[Board]):
    def __init__(self, db: Session):
        super().__init__(db, Board)

    def get_user_boards(self, user_id: int):
        return self.db.query(Board).filter(Board.owner_id == user_id).all()

    def get_board_with_tasks(self, board_id: int):
        return self.db.query(Board).filter(Board.id == board_id).first()

    def create_board(self, name: str, description: str, owner_id: int):
        return self.create(
            name=name,
            description=description,
            owner_id=owner_id
        )