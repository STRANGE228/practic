from sqlalchemy.orm import Session, joinedload
from app.models.task import Task
from app.repositories.base import BaseRepository
from typing import List, Optional
from datetime import datetime


class TaskRepository(BaseRepository[Task]):
    def __init__(self, db: Session):
        super().__init__(db, Task)

    def get_by_column(self, column_id):
        # Получение всех задач колонки
        return self.db.query(Task).filter(Task.column_id == column_id).order_by(Task.order).all()

    def get_with_images(self, task_id):
        # Получение задачи с изображениями
        return self.db.query(Task).options(joinedload(Task.task_images)).filter(Task.id == task_id).first()

    def create_task(self, title, description, column_id, due_date = None):
        # Создание новой задачи с дедлайном
        max_order = self.db.query(Task).filter(Task.column_id == column_id).count()

        return self.create(
            title=title,
            description=description,
            column_id=column_id,
            order=max_order,
            due_date=due_date,
            is_completed=False
        )

    def move_task(self, task_id, new_column_id, new_order):
        # Перемещение задачи между колонками
        task = self.get(task_id)
        if task:
            task.column_id = new_column_id
            task.order = new_order
            self.db.commit()
            self.db.refresh(task)
        return task

    def reorder_tasks(self, column_id, task_orders):
        # Переупорядочивание задач внутри колонки
        tasks = self.db.query(Task).filter(Task.column_id == column_id).all()

        for task in tasks:
            if task.id in task_orders:
                task.order = task_orders.index(task.id)

        self.db.commit()

    def update_task_status(self, task_id, is_completed):
        # Обновление статуса завершения задачи
        task = self.get(task_id)
        if task:
            task.is_completed = is_completed
            self.db.commit()
            self.db.refresh(task)
        return task

    def get_overdue_tasks(self, user_id = None):
        # Получение просроченных задач
        query = self.db.query(Task).filter(
            Task.due_date < datetime.now(),
            Task.is_completed == False
        )
        return query.all()