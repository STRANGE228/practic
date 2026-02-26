from sqlalchemy.orm import Session
from app.models.board import Board
from app.repositories.base import BaseRepository


class BoardRepository(BaseRepository[Board]):
    def __init__(self, db):
        super().__init__(db, Board)

    def get_board_with_tasks(self, board_id):
        return self.db.query(Board).filter(Board.id == board_id).first()

    def get_user_boards(self, user_id):
        return self.db.query(Board).filter(Board.owner_id == user_id).all()

    def create_board(self, name, description, owner_id):
        return self.create(
            name=name,
            description=description,
            owner_id=owner_id
        )
