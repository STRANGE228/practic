from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.repositories.board_member_repository import BoardMemberRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.task_image_repository import TaskImageRepository
from app.repositories.column_repository import ColumnRepository
from app.repositories.board_repository import BoardRepository
from app.services.task_service import TaskService
from app.models.user import User
from typing import List, Optional
import os
import uuid

UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/create")
async def create_task(
        request: Request,
        column_id: int = Form(...),
        title: str = Form(...),
        description: str = Form(""),
        images: List[UploadFile] = File(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    column_repo = ColumnRepository(db)
    board_repo = BoardRepository(db)

    column = column_repo.get(column_id)
    if not column:
        raise HTTPException(status_code=404, detail="Колонка не найдена")

    board = board_repo.get(column.board_id)
    if not board or board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    task_repo = TaskRepository(db)
    image_repo = TaskImageRepository(db)
    task_service = TaskService(task_repo, image_repo)

    try:
        task = task_service.create_task(title, description, column_id)

        if images and images[0].filename:
            for image in images:
                if image and image.filename:
                    try:
                        content = await image.read()
                        if content:
                            ext = os.path.splitext(image.filename)[1]
                            filename = f"{uuid.uuid4()}{ext}"
                            file_path = os.path.join(UPLOAD_DIR, filename)

                            with open(file_path, "wb") as f:
                                f.write(content)

                            task_service.add_image_to_task(
                                task.id,
                                image.filename,
                                f"/static/uploads/{filename}",
                                len(content)
                            )
                    except Exception as e:
                        print(f"Error saving image: {e}")
                        continue

        return RedirectResponse(url=f"/boards/{board.id}", status_code=303)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{task_id}")
async def get_task_json(
        task_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    task_repo = TaskRepository(db)
    task = task_repo.get_with_images(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    column_repo = ColumnRepository(db)
    column = column_repo.get(task.column_id)
    if not column:
        raise HTTPException(status_code=404, detail="Колонка не найдена")

    board_repo = BoardRepository(db)
    board = board_repo.get(column.board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Доска не найдена")

    if board.owner_id != current_user.id:
        from app.repositories.board_member_repository import BoardMemberRepository
        member_repo = BoardMemberRepository(db)
        member = member_repo.db.query(member_repo.model).filter(
            member_repo.model.board_id == board.id,
            member_repo.model.user_id == current_user.id
        ).first()

        if not member:
            raise HTTPException(status_code=403, detail="Доступ запрещен")

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description or "",
        "column_id": task.column_id,
        "images": [
            {
                "id": img.id,
                "filename": img.filename,
                "url": img.file_path,
                "size": img.file_size
            }
            for img in task.task_images
        ]
    }

@router.post("/{task_id}/update")
async def update_task(
        task_id: int,
        request: Request,
        title: str = Form(...),
        description: str = Form(""),
        column_id: int = Form(...),
        new_images: List[UploadFile] = File(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    task_repo = TaskRepository(db)
    image_repo = TaskImageRepository(db)
    column_repo = ColumnRepository(db)
    board_repo = BoardRepository(db)
    task_service = TaskService(task_repo, image_repo)

    task = task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    column = column_repo.get(task.column_id)
    if not column:
        raise HTTPException(status_code=404, detail="Колонка не найдена")

    board = board_repo.get(column.board_id)
    if not board or board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    task_repo.update(task, title=title, description=description, column_id=column_id)

    if new_images and new_images[0].filename:
        for image in new_images:
            if image and image.filename:
                try:
                    content = await image.read()
                    if content:
                        ext = os.path.splitext(image.filename)[1]
                        filename = f"{uuid.uuid4()}{ext}"
                        file_path = os.path.join(UPLOAD_DIR, filename)

                        with open(file_path, "wb") as f:
                            f.write(content)

                        task_service.add_image_to_task(
                            task_id,
                            image.filename,
                            f"/static/uploads/{filename}",
                            len(content)
                        )
                except Exception as e:
                    print(f"Error saving image: {e}")
                    continue

    return RedirectResponse(url=f"/boards/{board.id}", status_code=303)


@router.post("/{task_id}/move")
async def move_task(
        task_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Некорректный JSON"}
        )

    new_column_id = data.get("column_id")
    new_order = data.get("order", 0)

    if new_column_id is None:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Не указан column_id"}
        )

    task_repo = TaskRepository(db)
    image_repo = TaskImageRepository(db)
    column_repo = ColumnRepository(db)
    board_repo = BoardRepository(db)
    task_service = TaskService(task_repo, image_repo)

    task = task_repo.get(task_id)
    if not task:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Задача не найдена"}
        )

    column = column_repo.get(task.column_id)
    if not column:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Колонка не найдена"}
        )

    board = board_repo.get(column.board_id)
    if not board or board.owner_id != current_user.id:
        return JSONResponse(
            status_code=403,
            content={"success": False, "error": "Доступ запрещен"}
        )

    try:
        if task.column_id == new_column_id and task.order == new_order:
            return JSONResponse({
                "success": True,
                "task_id": task.id,
                "new_column_id": task.column_id,
                "new_order": task.order,
                "message": "Задача уже на нужном месте"
            })

        task = task_service.move_task(task_id, new_column_id, new_order)
        return JSONResponse({
            "success": True,
            "task_id": task.id,
            "new_column_id": task.column_id,
            "new_order": task.order
        })
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )


@router.post("/reorder")
async def reorder_tasks(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Некорректный JSON"}
        )

    column_id = data.get("column_id")
    task_orders = data.get("task_orders", [])

    if not column_id:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Не указан column_id"}
        )

    column_repo = ColumnRepository(db)
    board_repo = BoardRepository(db)

    column = column_repo.get(column_id)
    if not column:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Колонка не найдена"}
        )

    board = board_repo.get(column.board_id)
    if not board or board.owner_id != current_user.id:
        return JSONResponse(
            status_code=403,
            content={"success": False, "error": "Доступ запрещен"}
        )

    task_repo = TaskRepository(db)
    task_service = TaskService(task_repo)

    try:
        task_service.reorder_tasks(column_id, task_orders)
        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )


@router.post("/image/{image_id}/delete")
async def delete_task_image(
        image_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    image_repo = TaskImageRepository(db)
    task_repo = TaskRepository(db)
    column_repo = ColumnRepository(db)
    board_repo = BoardRepository(db)

    image = image_repo.get(image_id)
    if not image:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Изображение не найдено"}
        )

    task = task_repo.get(image.task_id)
    if not task:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Задача не найдена"}
        )

    column = column_repo.get(task.column_id)
    if not column:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Колонка не найдена"}
        )

    board = board_repo.get(column.board_id)
    if not board:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Доска не найдена"}
        )

    if board.owner_id != current_user.id:
        from app.repositories.board_member_repository import BoardMemberRepository
        from app.models.board_member import MemberRole

        member_repo = BoardMemberRepository(db)
        member = member_repo.db.query(member_repo.model).filter(
            member_repo.model.board_id == board.id,
            member_repo.model.user_id == current_user.id
        ).first()

        if not member or member.role == MemberRole.VIEWER:
            return JSONResponse(
                status_code=403,
                content={"success": False, "error": "Доступ запрещен"}
            )

    try:
        if os.path.exists(image.file_path):
            os.remove(image.file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")

    image_repo.delete(image)
    return JSONResponse(
        status_code=200,
        content={"success": True, "message": "Изображение удалено"}
    )

@router.post("/{task_id}/delete")
async def delete_task(
        task_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    task_repo = TaskRepository(db)
    image_repo = TaskImageRepository(db)
    column_repo = ColumnRepository(db)
    board_repo = BoardRepository(db)
    task_service = TaskService(task_repo, image_repo)

    task = task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    column = column_repo.get(task.column_id)
    if not column:
        raise HTTPException(status_code=404, detail="Колонка не найдена")

    board = board_repo.get(column.board_id)
    if not board or board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    board_id = board.id
    task_service.delete_task(task_id)

    return RedirectResponse(url=f"/boards/{board_id}", status_code=303)