from sqlalchemy.orm import Session
from app.models.board_member import BoardMember, MemberRole
from app.repositories.base import BaseRepository
from typing import List, Optional


class BoardMemberRepository(BaseRepository[BoardMember]):
    def __init__(self, db: Session):
        super().__init__(db, BoardMember)

    def get_board_members(self, board_id: int) -> List[BoardMember]:
        return self.db.query(BoardMember).filter(BoardMember.board_id == board_id).all()

    def get_user_boards(self, user_id: int) -> List[BoardMember]:
        return self.db.query(BoardMember).filter(BoardMember.user_id == user_id).all()

    def add_member(self, board_id: int, user_id: int, role: MemberRole, invited_by: int) -> BoardMember:
        return self.create(
            board_id=board_id,
            user_id=user_id,
            role=role,
            invited_by=invited_by
        )

    def remove_member(self, board_id: int, user_id: int) -> bool:
        member = self.db.query(BoardMember).filter(
            BoardMember.board_id == board_id,
            BoardMember.user_id == user_id
        ).first()

        if member:
            self.delete(member)
            return True
        return False

    def update_role(self, board_id: int, user_id: int, role: MemberRole) -> Optional[BoardMember]:
        member = self.db.query(BoardMember).filter(
            BoardMember.board_id == board_id,
            BoardMember.user_id == user_id
        ).first()

        if member:
            member.role = role
            self.db.commit()
            self.db.refresh(member)
        return member