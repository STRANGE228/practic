from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.repositories.board_repository import BoardRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.column_repository import ColumnRepository
from app.repositories.board_member_repository import BoardMemberRepository
from app.services.board_service import BoardService
from app.models.user import User
from app.models.board_member import MemberRole

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/boards", tags=["boards"])


@router.get("/new")
async def new_board_form(
        request: Request,
        current_user: User = Depends(get_current_active_user)
):
    # страница создания доски
    return templates.TemplateResponse(
        "boards/board_form.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.post("/new")
async def create_board(
        request: Request,
        name: str = Form(...),
        description: str = Form(""),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # создание доски
    board_repo = BoardRepository(db)
    task_repo = TaskRepository(db)
    column_repo = ColumnRepository(db)
    member_repo = BoardMemberRepository(db)

    board_service = BoardService(board_repo, task_repo, column_repo, member_repo)

    try:
        board = board_service.create_board(
            name=name,
            description=description,
            owner_id=current_user.id
        )
        return RedirectResponse(url=f"/boards/{board.id}", status_code=303)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}")
async def user_boards(
        request: Request,
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # все доски пользователя
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    board_repo = BoardRepository(db)
    task_repo = TaskRepository(db)
    column_repo = ColumnRepository(db)
    member_repo = BoardMemberRepository(db)

    board_service = BoardService(board_repo, task_repo, column_repo, member_repo)
    boards = board_service.get_user_accessible_boards(user_id)

    return templates.TemplateResponse(
        "boards/my_boards.html",
        {
            "request": request,
            "user": current_user,
            "boards": boards
        }
    )


@router.get("/{board_id}/edit")
async def edit_board_form(
        request: Request,
        board_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # форма редактирования доски
    board_repo = BoardRepository(db)
    board = board_repo.get(board_id)

    if not board:
        raise HTTPException(status_code=404, detail="Доска не найдена")

    if board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Только владелец может редактировать доску")

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
async def update_board(
        request: Request,
        board_id: int,
        name: str = Form(...),
        description: str = Form(""),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # сохраняет изменения доски
    board_repo = BoardRepository(db)
    board = board_repo.get(board_id)

    if not board:
        raise HTTPException(status_code=404, detail="Доска не найдена")

    if board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Только владелец может редактировать доску")

    board_repo.update(board, name=name, description=description)

    return RedirectResponse(url=f"/boards/{board_id}", status_code=303)


@router.post("/{board_id}/delete")
async def delete_board(
        request: Request,
        board_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # удаление доски
    board_repo = BoardRepository(db)
    board = board_repo.get(board_id)

    if not board:
        raise HTTPException(status_code=404, detail="Доска не найдена")

    if board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Только владелец может удалить доску")

    board_repo.delete(board)

    return RedirectResponse(url=f"/boards/user/{current_user.id}", status_code=303)


@router.get("/{board_id}")
async def view_board(
        request: Request,
        board_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # показывает страницу доски с колонками и задачами
    board_repo = BoardRepository(db)
    task_repo = TaskRepository(db)
    column_repo = ColumnRepository(db)
    member_repo = BoardMemberRepository(db)

    board_service = BoardService(board_repo, task_repo, column_repo, member_repo)
    board_data = board_service.get_board_with_details(board_id, current_user.id)

    if not board_data:
        raise HTTPException(status_code=404, detail="Доска не найдена или доступ запрещен")

    return templates.TemplateResponse(
        "boards/board_detail.html",
        {
            "request": request,
            "user": current_user,
            "board": board_data["board"],
            "columns": board_data["columns"],
            "members": board_data["members"],
            "user_role": board_data["user_role"]
        }
    )