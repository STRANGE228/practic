from app.repositories.column_repository import ColumnRepository
from app.repositories.task_repository import TaskRepository
from typing import Dict, Any, List


class ColumnService:
    def __init__(self, column_repo: ColumnRepository, task_repo: TaskRepository):
        self.column_repo = column_repo
        self.task_repo = task_repo

    def get_board_with_columns(self, board_id):
        columns = self.column_repo.get_board_columns(board_id)

        result = []
        for column in columns:
            tasks = self.task_repo.get_by_column(column.id)
            result.append({
                "column": column,
                "tasks": tasks
            })

        return {
            "board_id": board_id,
            "columns": result
        }

    def create_column(self, name, board_id):
        if not name or not name.strip():
            raise ValueError("Название колонки не может быть пустым")

        return self.column_repo.create_column(name.strip(), board_id)

    def update_column(self, column_id, name):
        if not name or not name.strip():
            raise ValueError("Название колонки не может быть пустым")

        column = self.column_repo.update_column(column_id, name.strip())
        if not column:
            raise ValueError(f"Колонка с id {column_id} не найдена")

        return column

    def delete_column(self, column_id):
        column = self.column_repo.get(column_id)
        if not column:
            raise ValueError(f"Колонка с id {column_id} не найдена")

        self.column_repo.delete(column)