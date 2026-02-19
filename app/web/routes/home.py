from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.board_repository import BoardRepository

router = APIRouter(tags=["home"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def home_page(request: Request, db: Session = Depends(get_db)):
    """Главная страница со списком досок"""
    board_repo = BoardRepository(db)
    boards = board_repo.get_all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "boards": boards,
            "title": "Мои доски"
        }
    )