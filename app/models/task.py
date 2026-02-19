from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, default="")
    status = Column(String, default="todo")  # todo, in_progress, done
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связь с доской
    board = relationship("Board", back_populates="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"