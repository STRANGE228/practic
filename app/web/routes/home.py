from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.core.auth import get_current_user

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["home"])


@router.get("/")
async def home_page(
        request: Request,
        current_user=Depends(get_current_user)
):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/my-boards")
async def my_boards_redirect(
        request: Request,
        current_user=Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    return RedirectResponse(url=f"/boards/user/{current_user.id}", status_code=303)