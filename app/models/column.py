from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Column(Base):
    __tablename__ = "columns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    order = Column(Integer, default=0)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    column_board = relationship("Board", back_populates="board_columns")
    column_tasks = relationship("Task", back_populates="task_column", cascade="all, delete-orphan",
                                order_by="Task.order")

    def __repr__(self):
        return f"<Column(id={self.id}, name={self.name}, board_id={self.board_id})>"