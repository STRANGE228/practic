from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    email = Column(String, nullable=True)
    role = Column(String, default="viewer")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    invitation_board = relationship("Board", back_populates="board_invitations")
    inviter = relationship("User", foreign_keys=[invited_by], back_populates="user_created_invitations")

    def __repr__(self):
        return f"<Invitation(token={self.token}, board_id={self.board_id})>"