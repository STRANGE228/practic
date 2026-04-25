from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    column_id = Column(Integer, ForeignKey("columns.id", ondelete="CASCADE"), nullable=False)
    order = Column(Integer, default=0)
    due_date = Column(DateTime(timezone=True), nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    task_column = relationship("Column", back_populates="column_tasks")
    task_images = relationship("TaskImage", back_populates="image_task", cascade="all, delete-orphan")

    @property
    def is_overdue(self):
        #Проверка, просрочена ли задача
        if self.is_completed:
            return False
        if self.due_date and self.due_date < datetime.now():
            return True
        return False

    @property
    def status_display(self):
        #Отображение статуса задачи
        if self.is_completed:
            return "completed"
        if self.is_overdue:
            return "overdue"
        return "active"

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title})>"