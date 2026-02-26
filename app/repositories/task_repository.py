from sqlalchemy.orm import Session
from app.models.task import Task
from app.repositories.base import BaseRepository
from typing import List, Optional


class TaskRepository(BaseRepository[Task]):
    def __init__(self, db):
        super().__init__(db, Task)

    def get_board_tasks(self, board_id):
        return self.db.query(Task).filter(Task.board_id == board_id).order_by(Task.order).all()

    def get_tasks_by_status(self, board_id, status):
        return self.db.query(Task).filter(
            Task.board_id == board_id,
            Task.status == status
        ).order_by(Task.order).all()

    def create_task(self, title, description, board_id, status = "todo"):
        max_order = self.db.query(Task).filter(
            Task.board_id == board_id,
            Task.status == status
        ).count()

        return self.create(
            title=title,
            description=description,
            status=status,
            order=max_order,
            board_id=board_id
        )

    def update_task_status(self, task_id, new_status, new_order):
        task = self.get(task_id)
        if task:
            task.status = new_status
            task.order = new_order
            self.db.commit()
            self.db.refresh(task)
        return task

    def reorder_tasks(self, board_id, status, task_orders):
        tasks = self.db.query(Task).filter(
            Task.board_id == board_id,
            Task.status == status
        ).all()

        for task in tasks:
            if task.id in task_orders:
                task.order = task_orders.index(task.id)

        self.db.commit()