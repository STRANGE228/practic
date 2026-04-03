from sqlalchemy.orm import Session
from app.models.board import Board
from app.repositories.base import BaseRepository
from typing import List, Optional


class BoardRepository(BaseRepository[Board]):
    def __init__(self, db: Session):
        super().__init__(db, Board)

    def get_user_boards(self, user_id: int) -> List[Board]:
        return self.db.query(Board).filter(Board.owner_id == user_id).all()

    def get_board_with_owner(self, board_id: int) -> Optional[Board]:
        return self.db.query(Board).filter(Board.id == board_id).first()

    def create_board(self, name: str, description: str, owner_id: int) -> Board:
        return self.create(
            name=name,
            description=description,
            owner_id=owner_id
        )

    def update_board(self, board_id: int, name: str, description: str) -> Optional[Board]:
        board = self.get(board_id)
        if board:
            board.name = name
            board.description = description
            self.db.commit()
            self.db.refresh(board)
        return board