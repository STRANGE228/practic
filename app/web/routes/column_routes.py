from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.repositories.column_repository import ColumnRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.board_repository import BoardRepository
from app.repositories.board_member_repository import BoardMemberRepository
from app.services.column_service import ColumnService
from app.models.user import User
from app.models.board_member import MemberRole

router = APIRouter(prefix="/columns", tags=["columns"])


def check_column_access(column_id: int, user_id: int, db: Session, require_edit: bool = False):
    # проверка доступа к колонке
    column_repo = ColumnRepository(db)
    column = column_repo.get(column_id)

    if not column:
        return None, "Колонка не найдена"

    board_repo = BoardRepository(db)
    board = board_repo.get(column.board_id)

    if not board:
        return None, "Доска не найдена"

    if board.owner_id == user_id:
        return column, "owner"
    member_repo = BoardMemberRepository(db)
    member = member_repo.db.query(member_repo.model).filter(
        member_repo.model.board_id == board.id,
        member_repo.model.user_id == user_id
    ).first()

    if not member:
        return None, "Доступ запрещен"

    if require_edit and member.role == MemberRole.VIEWER:
        return None, "Недостаточно прав для редактирования"

    return column, member.role.value


@router.post("/create")
async def create_column(
        request: Request,
        board_id: int = Form(...),
        name: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # создание колонки
    board_repo = BoardRepository(db)
    board = board_repo.get(board_id)

    if not board:
        raise HTTPException(status_code=404, detail="Доска не найдена")
    if board.owner_id != current_user.id:
        member_repo = BoardMemberRepository(db)
        member = member_repo.db.query(member_repo.model).filter(
            member_repo.model.board_id == board_id,
            member_repo.model.user_id == current_user.id
        ).first()

        if not member or member.role == MemberRole.VIEWER:
            raise HTTPException(status_code=403, detail="Недостаточно прав для создания колонки")

    column_repo = ColumnRepository(db)
    column_repo.create_column(name=name, board_id=board_id)

    return RedirectResponse(url=f"/boards/{board_id}", status_code=303)


@router.post("/{column_id}/update")
async def update_column(
        column_id: int,
        name: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # редактирование колонки
    column, access = check_column_access(column_id, current_user.id, db, require_edit=True)

    if not column:
        raise HTTPException(status_code=403 if "запрещен" in access else 404, detail=access)

    column_repo = ColumnRepository(db)
    column_repo.update_column(column_id, name)

    return RedirectResponse(url=f"/boards/{column.board_id}", status_code=303)


@router.post("/{column_id}/delete")
async def delete_column(
        column_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # удалить колонку
    column, access = check_column_access(column_id, current_user.id, db, require_edit=True)

    if not column:
        raise HTTPException(status_code=403 if "запрещен" in access else 404, detail=access)

    board_id = column.board_id
    column_repo = ColumnRepository(db)
    column_repo.delete(column)

    return RedirectResponse(url=f"/boards/{board_id}", status_code=303)