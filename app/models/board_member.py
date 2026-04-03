from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class MemberRole(enum.Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class BoardMember(Base):
    __tablename__ = "board_members"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(MemberRole), default=MemberRole.VIEWER)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    member_board = relationship("Board", back_populates="board_members")
    member_user = relationship("User", foreign_keys=[user_id], back_populates="user_board_memberships")
    inviter_user = relationship("User", foreign_keys=[invited_by], back_populates="user_sent_invitations")

    def __repr__(self):
        return f"<BoardMember(board_id={self.board_id}, user_id={self.user_id}, role={self.role})>"