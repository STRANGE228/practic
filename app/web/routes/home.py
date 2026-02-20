from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user
from app.repositories.board_repository import BoardRepository
from app.models.user import User

router = APIRouter(tags=["home"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def home_page(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "user": current_user,
            "title": "Kanban Board"
        }
    )


@router.get("/my-boards")
async def my_boards(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    board_repo = BoardRepository(db)

    boards = board_repo.get_all()

    return templates.TemplateResponse(
        "boards/my_boards.html",
        {
            "request": request,
            "user": current_user,
            "boards": boards,
            "title": "Мои доски"
        }
    )

@router.get("/debug/cookies")
async def debug_cookies(request: Request):
    """Отладка cookie"""
    cookies = dict(request.cookies)
    return JSONResponse({
        "cookies": cookies,
        "has_token": "access_token" in cookies
    })