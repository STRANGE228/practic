from app.repositories.board_repository import BoardRepository
from app.repositories.task_repository import TaskRepository
from typing import Dict, Any


class BoardService:
    def __init__(self, board_repo: BoardRepository, task_repo: TaskRepository):
        self.board_repo = board_repo
        self.task_repo = task_repo

    def get_board_with_tasks(self, board_id: int) -> Dict[str, Any]:
        board = self.board_repo.get(board_id)
        if not board:
            return None

        tasks = self.task_repo.get_by_board(board_id)

        columns = {
            "todo": [t for t in tasks if t.status == "todo"],
            "in_progress": [t for t in tasks if t.status == "in_progress"],
            "done": [t for t in tasks if t.status == "done"]
        }

        for status in columns:
            columns[status].sort(key=lambda t: t.order)

        return {
            "board": board,
            "columns": columns
        }

    def create_board(self, name: str, description: str, owner_id: int):
        return self.board_repo.create_board(
            name=name,
            description=description,
            owner_id=owner_id
        )

    def get_user_boards(self, user_id: int):
        return self.board_repo.get_user_boards(user_id)