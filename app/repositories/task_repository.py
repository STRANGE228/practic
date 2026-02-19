from sqlalchemy.orm import Session
from app.models.task import Task
from app.repositories.base import BaseRepository
from typing import List, Optional


class TaskRepository(BaseRepository[Task]):
    def __init__(self, db: Session):
        super().__init__(db, Task)

    def get_by_board(self, board_id: int, skip: int = 0, limit: int = 100) -> List[Task]:
        return self.db.query(Task).filter(
            Task.board_id == board_id
        ).offset(skip).limit(limit).all()

    def get_by_status(self, board_id: int, status: str) -> List[Task]:
        return self.db.query(Task).filter(
            Task.board_id == board_id,
            Task.status == status
        ).all()

    def update_status(self, task_id: int, new_status: str) -> Optional[Task]:
        task = self.get(task_id)
        if task:
            task.status = new_status
            self.db.commit()
            self.db.refresh(task)
        return task