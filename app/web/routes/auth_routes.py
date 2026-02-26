from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.core.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
async def login_page(request, current_user = Depends(get_current_user)):
    # Если пользователь уже авторизован, отправляем на доски
    if current_user:
        return RedirectResponse(url="/my-boards", status_code=303)

    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "title": "Вход"}
    )


@router.post("/login")
async def login(request, email = Form(...), password = Form(...), db = Depends(get_db)):
    logger.info(f"Login attempt for email: {email}")

    user_repo = UserRepository(db)
    user_service = UserService(user_repo)

    user = user_service.authenticate_user(email, password)

    if not user:
        logger.warning(f"Failed login for email: {email}")
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "title": "Вход",
                "error": "Неверный email или пароль"
            },
            status_code=400
        )

    # Создаем токен
    token = user_service.create_user_token(user.id)
    logger.info(f"Created token for user: {user.email}")

    # Устанавливаем куку с токеном
    response = RedirectResponse(url="/my-boards", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        expires=60 * 60 * 24 * 7,
        samesite="lax",
        path="/"
    )

    logger.info(f"Set cookie for user: {user.email}")
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
        {"request": request, "title": "Регистрация"}
    )


@router.post("/register")
async def register(request, email = Form(...), username = Form(...), password = Form(...), confirm_password = Form(...), db = Depends(get_db)):
    logger.info(f"Registration attempt for email: {email}")

    if password != confirm_password:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "title": "Регистрация",
                "error": "Пароли не совпадают",
                "email": email,
                "username": username
            },
            status_code=400
        )

    user_repo = UserRepository(db)
    user_service = UserService(user_repo)

    try:
        # Создаем пользователя
        user = user_service.register_user(
            email=email,
            username=username,
            password=password
        )

        logger.info(f"User created successfully: {email}")

        # Сразу создаем токен и логиним
        token = user_service.create_user_token(user.id)

        response = RedirectResponse(url="/my-boards", status_code=303)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {token}",
            httponly=True,
            max_age=60 * 60 * 24 * 7,
            expires=60 * 60 * 24 * 7,
            samesite="lax",
            path="/"
        )

        logger.info(f"Auto-login after registration for: {email}")
        return response

    except HTTPException as e:
        logger.warning(f"Registration failed for {email}: {e.detail}")
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "title": "Регистрация",
                "error": e.detail,
                "email": email,
                "username": username
            },
            status_code=400
        )


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token", path="/")
    return response
