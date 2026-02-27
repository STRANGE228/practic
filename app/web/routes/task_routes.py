from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.repositories.task_repository import TaskRepository
from app.repositories.board_repository import BoardRepository
from app.services.task_service import TaskService
from app.models.user import User
from typing import Optional

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/create")
async def create_task(
        request: Request,
        board_id: int = Form(...),
        title: str = Form(...),
        description: str = Form(""),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    board_repo = BoardRepository(db)
    board = board_repo.get(board_id)

    if not board or board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    task_repo = TaskRepository(db)
    task_service = TaskService(task_repo)

    try:
        task_service.create_task(title, description, board_id)
        return RedirectResponse(url=f"/boards/{board_id}", status_code=303)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/move")
async def move_task(
        task_id: int,
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

    new_status = data.get("status")
    new_order = data.get("order", 0)

    if not new_status:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Не указан статус"}
        )

    task_repo = TaskRepository(db)
    board_repo = BoardRepository(db)
    task_service = TaskService(task_repo)

    task = task_repo.get(task_id)
    if not task:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Задача не найдена"}
        )

    board = board_repo.get(task.board_id)
    if not board or board.owner_id != current_user.id:
        return JSONResponse(
            status_code=403,
            content={"success": False, "error": "Доступ запрещен"}
        )

    try:
        task = task_service.move_task(task_id, new_status, new_order)
        return JSONResponse({
            "success": True,
            "task_id": task.id,
            "new_status": task.status,
            "new_order": task.order
        })
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )


@router.post("/reorder")
async def reorder_column(
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
    status = data.get("status")
    task_orders = data.get("task_orders", [])

    if not board_id or not status:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Не указаны board_id или status"}
        )

    board_repo = BoardRepository(db)
    board = board_repo.get(board_id)

    if not board or board.owner_id != current_user.id:
        return JSONResponse(
            status_code=403,
            content={"success": False, "error": "Доступ запрещен"}
        )

    task_repo = TaskRepository(db)
    task_service = TaskService(task_repo)

    try:
        task_service.reorder_column(board_id, status, task_orders)
        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )


@router.post("/{task_id}/delete")
async def delete_task(
        task_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    task_repo = TaskRepository(db)
    board_repo = BoardRepository(db)

    task = task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    board = board_repo.get(task.board_id)
    if not board or board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    board_id = task.board_id
    task_repo.delete(task)

    return RedirectResponse(url=f"/boards/{board_id}", status_code=303)


@router.post("/{task_id}/update")
async def update_task(
        task_id: int,
        request: Request,
        title: str = Form(...),
        description: str = Form(""),
        status: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    task_repo = TaskRepository(db)
    board_repo = BoardRepository(db)

    task = task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    board = board_repo.get(task.board_id)
    if not board or board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    task_repo.update(task, title=title, description=description, status=status)

    return RedirectResponse(url=f"/boards/{task.board_id}", status_code=303)