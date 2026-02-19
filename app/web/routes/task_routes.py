from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/")
async def create_task(
        request: Request,
        board_id: int = Form(...),
        title: str = Form(...),
        description: str = Form(""),
        db: Session = Depends(get_db)
):
    """Создать новую задачу"""
    task_repo = TaskRepository(db)
    task_service = TaskService(task_repo)

    try:
        task = task_service.create_task(board_id, title, description)
        return RedirectResponse(url=f"/boards/{board_id}", status_code=303)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/move")
async def move_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    """Переместить задачу (API для Drag & Drop)"""
    data = await request.json()
    new_status = data.get("status")

    task_repo = TaskRepository(db)
    task_service = TaskService(task_repo)

    try:
        task = task_service.move_task(task_id, new_status)
        return JSONResponse({
            "success": True,
            "task_id": task.id,
            "new_status": task.status
        })
    except ValueError as e:
        return JSONResponse(
            status_code=400,
        )


@router.post("/{task_id}/delete")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Удалить задачу"""
    task_repo = TaskRepository(db)
    task = task_repo.get(task_id)

    if task:
        board_id = task.board_id
        task_repo.delete(task)
        return RedirectResponse(url=f"/boards/{board_id}", status_code=303)

    raise HTTPException(status_code=404, detail="Task not found")