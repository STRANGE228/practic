from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.repositories.task_repository import TaskRepository
from app.repositories.board_repository import BoardRepository
from app.services.task_service import TaskService
from app.models.user import User

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/create")
async def create_task(request, board_id = Form(...), title = Form(...), description = Form(""), db = Depends(get_db), current_user = Depends(get_current_active_user)):
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
async def move_task(task_id, request, db = Depends(get_db), current_user = Depends(get_current_active_user)):
    data = await request.json()
    new_status = data.get("status")
    new_order = data.get("order", 0)

    task_repo = TaskRepository(db)
    board_repo = BoardRepository(db)
    task_service = TaskService(task_repo)

    task = task_repo.get(task_id)
    if not task:
        return JSONResponse(
            status_code=404
        )

    board = board_repo.get(task.board_id)
    if not board or board.owner_id != current_user.id:
        return JSONResponse(
            status_code=403
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
        )


@router.post("/{task_id}/reorder")
async def reorder_column(request, db = Depends(get_db), current_user = Depends(get_current_active_user)):
    data = await request.json()
    board_id = data.get("board_id")
    status = data.get("status")
    task_orders = data.get("task_orders", [])

    board_repo = BoardRepository(db)
    board = board_repo.get(board_id)

    if not board or board.owner_id != current_user.id:
        return JSONResponse(
            status_code=403
        )

    task_repo = TaskRepository(db)
    task_service = TaskService(task_repo)

    try:
        task_service.reorder_column(board_id, status, task_orders)
        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse(
            status_code=400
        )


@router.post("/{task_id}/delete")
async def delete_task(task_id, db = Depends(get_db), current_user = Depends(get_current_active_user)):
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