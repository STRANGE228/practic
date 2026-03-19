from sqlalchemy.orm import Session, joinedload
from app.models.task import Task
from app.repositories.base import BaseRepository
from typing import List, Optional


class TaskRepository(BaseRepository[Task]):
    def __init__(self, db: Session):
        super().__init__(db, Task)

    def get_by_column(self, column_id):
        return self.db.query(Task).filter(Task.column_id == column_id).order_by(Task.order).all()

    def get_with_images(self, task_id):
        return self.db.query(Task).options(joinedload(Task.images)).filter(Task.id == task_id).first()

    def create_task(self, title, description, column_id):
        max_order = self.db.query(Task).filter(Task.column_id == column_id).count()

        return self.create(
            title=title,
            description=description,
            column_id=column_id,
            order=max_order
        )

    def move_task(self, task_id, new_column_id, new_order):
        task = self.get(task_id)
        if task:
            task.column_id = new_column_id
            task.order = new_order
            self.db.commit()
            self.db.refresh(task)
        return task

    def reorder_tasks(self, column_id, task_orders):
        tasks = self.db.query(Task).filter(Task.column_id == column_id).all()

        for task in tasks:
            if task.id in task_orders:
                task.order = task_orders.index(task.id)

        self.db.commit()