from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.repositories.board_repository import BoardRepository
from app.repositories.task_repository import TaskRepository
from app.services.board_service import BoardService
from app.models.user import User

router = APIRouter(prefix="/boards", tags=["boards"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/user/{user_id}")
async def user_boards(
        request, user_id, db = Depends(get_db), current_user = Depends(get_current_active_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    board_repo = BoardRepository(db)
    boards = board_repo.get_user_boards(user_id)

    return templates.TemplateResponse(
        "boards/my_boards.html",
        {
            "request": request,
            "user": current_user,
            "boards": boards
        }
    )


@router.get("/new")
async def new_board_form(request, current_user = Depends(get_current_active_user)):
    return templates.TemplateResponse(
        "boards/board_form.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.post("/new")
async def create_board(request, name = Form(...), description = Form(""), db = Depends(get_db), current_user = Depends(get_current_active_user)):
    board_repo = BoardRepository(db)
    task_repo = TaskRepository(db)
    board_service = BoardService(board_repo, task_repo)

    board = board_service.create_board(
        name=name,
        description=description,
        owner_id=current_user.id
    )

    return RedirectResponse(url=f"/boards/{board.id}", status_code=303)


@router.get("/{board_id}")
async def view_board(request, board_id, db = Depends(get_db), current_user = Depends(get_current_active_user)):
    board_repo = BoardRepository(db)
    task_repo = TaskRepository(db)
    board_service = BoardService(board_repo, task_repo)

    board_data = board_service.get_board_with_tasks(board_id)

    if not board_data:
        raise HTTPException(status_code=404, detail="Доска не найдена")

    if board_data["board"].owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    return templates.TemplateResponse(
        "boards/board_detail.html",
        {
            "request": request,
            "user": current_user,
            "board": board_data["board"],
            "columns": board_data["columns"]
        }
    )


@router.get("/{board_id}/edit")
async def edit_board_form(request, board_id, db = Depends(get_db), current_user = Depends(get_current_active_user)):
    board_repo = BoardRepository(db)
    board = board_repo.get(board_id)

    if not board:
        raise HTTPException(status_code=404, detail="Доска не найдена")

    if board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    return templates.TemplateResponse(
        "boards/board_form.html",
        {
            "request": request,
            "user": current_user,
            "board": board,
            "edit": True
        }
    )


@router.post("/{board_id}/edit")
async def update_board(request, board_id, name = Form(...), description = Form(""), db = Depends(get_db), current_user = Depends(get_current_active_user)):
    board_repo = BoardRepository(db)
    board = board_repo.get(board_id)

    if not board:
        raise HTTPException(status_code=404, detail="Доска не найдена")

    if board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    board_repo.update(board, name=name, description=description)

    return RedirectResponse(url=f"/boards/{board_id}", status_code=303)


@router.post("/{board_id}/delete")
async def delete_board(board_id, db = Depends(get_db), current_user = Depends(get_current_active_user)):
    board_repo = BoardRepository(db)
    board = board_repo.get(board_id)

    if not board:
        raise HTTPException(status_code=404, detail="Доска не найдена")

    if board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    board_repo.delete(board)

    return RedirectResponse(url=f"/boards/user/{current_user.id}", status_code=303)