from sqlalchemy.orm import Session
from app.models.board import Board
from app.repositories.base import BaseRepository


class BoardRepository(BaseRepository[Board]):
    def __init__(self, db: Session):
        super().__init__(db, Board)

    def get_with_tasks(self, board_id: int):
        return self.db.query(Board).filter(Board.id == board_id).first()