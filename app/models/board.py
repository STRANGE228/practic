from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Board(Base):
    __tablename__ = "boards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    board_owner = relationship("User", foreign_keys=[owner_id], back_populates="user_owned_boards")
    board_columns = relationship("Column", back_populates="column_board", cascade="all, delete-orphan",
                                 order_by="Column.order")
    board_members = relationship("BoardMember", back_populates="member_board", cascade="all, delete-orphan")
    board_invitations = relationship("Invitation", back_populates="invitation_board", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Board(id={self.id}, name={self.name})>"