from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.repositories.column_repository import ColumnRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.board_repository import BoardRepository
from app.services.column_service import ColumnService
from app.models.user import User

router = APIRouter(prefix="/columns", tags=["columns"])


@router.post("/create")
async def create_column(
        request: Request,
        board_id: int = Form(...),
        name: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    board_repo = BoardRepository(db)
    board = board_repo.get(board_id)

    if not board or board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    column_repo = ColumnRepository(db)
    task_repo = TaskRepository(db)
    column_service = ColumnService(column_repo, task_repo)

    try:
        column_service.create_column(name, board_id)
        return RedirectResponse(url=f"/boards/{board_id}", status_code=303)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{column_id}/update")
async def update_column(
        column_id: int,
        request: Request,
        name: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    column_repo = ColumnRepository(db)
    task_repo = TaskRepository(db)
    board_repo = BoardRepository(db)
    column_service = ColumnService(column_repo, task_repo)

    column = column_repo.get(column_id)
    if not column:
        raise HTTPException(status_code=404, detail="Колонка не найдена")

    board = board_repo.get(column.board_id)
    if not board or board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        column_service.update_column(column_id, name)
        return RedirectResponse(url=f"/boards/{column.board_id}", status_code=303)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{column_id}/delete")
async def delete_column(
        column_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    column_repo = ColumnRepository(db)
    task_repo = TaskRepository(db)
    board_repo = BoardRepository(db)
    column_service = ColumnService(column_repo, task_repo)

    column = column_repo.get(column_id)
    if not column:
        raise HTTPException(status_code=404, detail="Колонка не найдена")

    board = board_repo.get(column.board_id)
    if not board or board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    board_id = column.board_id
    column_service.delete_column(column_id)

    return RedirectResponse(url=f"/boards/{board_id}", status_code=303)


@router.post("/reorder")
async def reorder_columns(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Некорректный JSON"}
        )

    board_id = data.get("board_id")
    column_orders = data.get("column_orders", [])

    if not board_id:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Не указан board_id"}
        )

    board_repo = BoardRepository(db)
    board = board_repo.get(board_id)

    if not board or board.owner_id != current_user.id:
        return JSONResponse(
            status_code=403,
            content={"success": False, "error": "Доступ запрещен"}
        )

    column_repo = ColumnRepository(db)
    column_repo.reorder_columns(board_id, column_orders)

    return JSONResponse({"success": True})