from app.repositories.task_repository import TaskRepository
from typing import Optional


class TaskService:
    def __init__(self, task_repo):
        self.task_repo = task_repo

    def create_task(self, board_id, title, description = ""):
        if not title:
            raise ValueError("Title is required")

        task = self.task_repo.create(
            title=title,
            description=description,
            status="todo",
            board_id=board_id
        )
        return task

    def move_task(self, task_id, new_status):
        valid_statuses = ["todo", "in_progress", "done"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")

        task = self.task_repo.update_status(task_id, new_status)
        if not task:
            raise ValueError(f"Task with id {task_id} not found")

        return task

    def reorder_column(self, board_id, status, task_orders):
        self.task_repo.reorder_tasks(board_id, status, task_orders)