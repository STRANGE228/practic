from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.core.auth import get_current_user

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login_page(
        request: Request,
        current_user=Depends(get_current_user)
):
    if current_user:
        return RedirectResponse(url="/my-boards", status_code=303)

    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.post("/login")
async def login(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)

    user = user_service.authenticate_user(email, password)

    if not user:
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": "Неверный email или пароль"
            },
            status_code=400
        )

    token = user_service.create_user_token(user.id)

    response = RedirectResponse(url="/my-boards", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
        path="/"
    )

    return response


@router.get("/register")
async def register_page(
        request: Request,
        current_user=Depends(get_current_user)
):
    if current_user:
        return RedirectResponse(url="/my-boards", status_code=303)

    return templates.TemplateResponse(
        "auth/register.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.post("/register")
async def register(
        request: Request,
        email: str = Form(...),
        username: str = Form(...),
        password: str = Form(...),
        confirm_password: str = Form(...),
        db: Session = Depends(get_db)
):
    if password != confirm_password:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "error": "Пароли не совпадают",
                "email": email,
                "username": username
            },
            status_code=400
        )

    user_repo = UserRepository(db)
    user_service = UserService(user_repo)

    try:
        user = user_service.register_user(
            email=email,
            username=username,
            password=password
        )

        token = user_service.create_user_token(user.id)

        response = RedirectResponse(url="/my-boards", status_code=303)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {token}",
            httponly=True,
            max_age=60 * 60 * 24 * 7,
            samesite="lax",
            path="/"
        )

        return response

    except HTTPException as e:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "error": e.detail,
                "email": email,
                "username": username
            },
            status_code=400
        )


@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token", path="/")
    return response