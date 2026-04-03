from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    user_owned_boards = relationship("Board", foreign_keys="Board.owner_id", back_populates="board_owner")
    user_board_memberships = relationship("BoardMember", foreign_keys="BoardMember.user_id",
                                          back_populates="member_user")
    user_sent_invitations = relationship("BoardMember", foreign_keys="BoardMember.invited_by",
                                         back_populates="inviter_user")
    user_created_invitations = relationship("Invitation", foreign_keys="Invitation.invited_by",
                                            back_populates="inviter")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"