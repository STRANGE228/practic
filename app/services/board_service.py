from app.repositories.board_repository import BoardRepository
from app.repositories.task_repository import TaskRepository
from typing import Dict, List


class BoardService:
    def __init__(self, board_repo, task_repo):
        self.board_repo = board_repo
        self.task_repo = task_repo

    def get_board_with_tasks(self, board_id):
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

    def create_board(self, name, description, owner_id):
        return self.board_repo.create_board(
            name=name,
            description=description,
            owner_id=owner_id
        )