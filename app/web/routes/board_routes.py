from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.board_repository import BoardRepository
from app.repositories.task_repository import TaskRepository
from app.services.board_service import BoardService

router = APIRouter(prefix="/boards", tags=["boards"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def list_boards(request: Request, db: Session = Depends(get_db)):
    """Список всех досок"""
    board_repo = BoardRepository(db)
    boards = board_repo.get_all()

    return templates.TemplateResponse(
        "boards/list.html",
        {
            "request": request,
            "boards": boards,
            "title": "Все доски"
        }
    )


@router.get("/new")
async def new_board_form(request: Request):
    """Форма создания новой доски"""
    return templates.TemplateResponse(
        "boards/form.html",
        {
            "request": request,
            "title": "Создать доску"
        }
    )


@router.post("/new")
async def create_board(
        request: Request,
        name: str = Form(...),
        description: str = Form(""),
        db: Session = Depends(get_db)
):
    board_repo = BoardRepository(db)
    board = board_repo.create(name=name, description=description)

    return RedirectResponse(url=f"/boards/{board.id}", status_code=303)


@router.get("/{board_id}")
async def view_board(
        request: Request,
        board_id: int,
        db: Session = Depends(get_db)
):
    """Просмотр конкретной доски"""
    board_repo = BoardRepository(db)
    task_repo = TaskRepository(db)

    board_service = BoardService(board_repo, task_repo)
    board_data = board_service.get_board_with_grouped_tasks(board_id)

    if not board_data:
        raise HTTPException(status_code=404, detail="Board not found")

    return templates.TemplateResponse(
        "boards/detail.html",
        {
            "request": request,
            "board": board_data["board"],
            "columns": board_data["columns"],
            "title": board_data["board"].name
        }
    )


@router.post("/{board_id}/delete")
async def delete_board(board_id: int, db: Session = Depends(get_db)):
    board_repo = BoardRepository(db)
    board = board_repo.get(board_id)

    if board:
        board_repo.delete(board)

    return RedirectResponse(url="/", status_code=303)