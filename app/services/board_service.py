from app.repositories.board_repository import BoardRepository
from app.repositories.task_repository import TaskRepository
from typing import Dict, List


class BoardService:
    def __init__(self, board_repo: BoardRepository, task_repo: TaskRepository):
        self.board_repo = board_repo
        self.task_repo = task_repo

    def get_board_with_grouped_tasks(self, board_id: int):
        board = self.board_repo.get(board_id)
        if not board:
            return None

        tasks = self.task_repo.get_by_board(board_id)

        # Группируем задачи по статусам
        columns = {
            "todo": [t for t in tasks if t.status == "todo"],
            "in_progress": [t for t in tasks if t.status == "in_progress"],
            "done": [t for t in tasks if t.status == "done"]
        }

        return {
            "board": board,
            "columns": columns
        }