from app.models import Board
from app.repositories.board_repository import BoardRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.column_repository import ColumnRepository
from app.repositories.board_member_repository import BoardMemberRepository
from app.models.board_member import MemberRole
from typing import Dict, Any, List


class BoardService:
    def __init__(self, board_repo: BoardRepository, task_repo: TaskRepository = None,
                 column_repo: ColumnRepository = None, member_repo: BoardMemberRepository = None):
        self.board_repo = board_repo
        self.task_repo = task_repo
        self.column_repo = column_repo
        self.member_repo = member_repo

    def create_board(self, name: str, description: str, owner_id: int):
        # создает новую доску
        if not name or not name.strip():
            raise ValueError("Название доски не может быть пустым")

        return self.board_repo.create_board(
            name=name.strip(),
            description=description,
            owner_id=owner_id
        )

    def get_user_accessible_boards(self, user_id: int):
        # все доски доступные пользователю
        owned_boards = self.board_repo.get_user_boards(user_id)

        member_boards = []
        if self.member_repo:
            memberships = self.member_repo.get_user_boards(user_id)
            for m in memberships:
                if m.member_board:
                    member_boards.append(m.member_board)
        all_boards = {b.id: b for b in owned_boards}
        for b in member_boards:
            if b.id not in all_boards:
                all_boards[b.id] = b

        return list(all_boards.values())

    def get_board_with_details(self, board_id: int, user_id: int):
        # возвращает всю доску с колонками и задачами
        board = self.board_repo.get(board_id)
        if not board:
            return None

        has_access = (board.owner_id == user_id)

        if not has_access and self.member_repo:
            member = self.member_repo.db.query(self.member_repo.model).filter(
                self.member_repo.model.board_id == board_id,
                self.member_repo.model.user_id == user_id
            ).first()
            has_access = member is not None

        if not has_access:
            return None
        columns = []
        if self.column_repo:
            columns = self.column_repo.get_board_columns(board_id)

        columns_data = []
        for column in columns:
            tasks = []
            if self.task_repo:
                tasks = self.task_repo.get_by_column(column.id)
            columns_data.append({
                "column": column,
                "tasks": tasks
            })
        members = []
        if self.member_repo:
            board_members = self.member_repo.get_board_members(board_id)
            for member in board_members:
                if member.member_user:
                    members.append({
                        "id": member.member_user.id,
                        "username": member.member_user.username,
                        "email": member.member_user.email,
                        "role": member.role.value,
                        "is_owner": member.member_user.id == board.owner_id
                    })
        owner_in_members = any(m["id"] == board.owner_id for m in members)
        if not owner_in_members and board.board_owner:
            members.insert(0, {
                "id": board.board_owner.id,
                "username": board.board_owner.username,
                "email": board.board_owner.email,
                "role": "owner",
                "is_owner": True
            })

        return {
            "board": board,
            "columns": columns_data,
            "members": members,
            "user_role": self._get_user_role(board, user_id)
        }

    def _get_user_role(self, board, user_id: int):
        # роль участника доски
        if board.owner_id == user_id:
            return "owner"

        if self.member_repo:
            member = self.member_repo.db.query(self.member_repo.model).filter(
                self.member_repo.model.board_id == board.id,
                self.member_repo.model.user_id == user_id
            ).first()

            if member:
                return member.role.value

        return None

    def add_member(self, board_id: int, user_id: int, invited_by: int, role: str = "viewer"):
        # добавление учасника к доске
        if not self.member_repo:
            raise ValueError("Member repository not initialized")

        role_enum = MemberRole.EDITOR if role == "editor" else MemberRole.VIEWER
        existing = self.member_repo.db.query(self.member_repo.model).filter(
            self.member_repo.model.board_id == board_id,
            self.member_repo.model.user_id == user_id
        ).first()

        if existing:
            return {"success": False, "error": "Пользователь уже является участником"}

        member = self.member_repo.add_member(board_id, user_id, role_enum, invited_by)

        return {
            "success": True,
            "member": {
                "id": member.member_user.id,
                "username": member.member_user.username,
                "email": member.member_user.email,
                "role": member.role.value
            }
        }

    def remove_member(self, board_id: int, user_id: int):
        # удалить пользователя с доски
        if not self.member_repo:
            return False

        return self.member_repo.remove_member(board_id, user_id)

    def update_board(self, board_id: int, name: str, description: str):
        # обновление названия и описание доски
        board = self.board_repo.get(board_id)
        if not board:
            raise ValueError(f"Доска с id {board_id} не найдена")

        return self.board_repo.update(board, name=name, description=description)

    def delete_board(self, board_id: int):
        # удаление доски
        board = self.board_repo.get(board_id)
        if not board:
            return False

        self.board_repo.delete(board)
        return True