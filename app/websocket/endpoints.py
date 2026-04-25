from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository
from app.websocket.manager import manager
import json


async def get_current_user_ws(token: str, db: Session):
    if not token:
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    try:
        user_id = int(user_id)
    except ValueError:
        return None

    user_repo = UserRepository(db)
    user = user_repo.get(user_id)

    return user


async def websocket_endpoint(
        websocket: WebSocket,
        board_id: int,
        token: str,
        db: Session = Depends(get_db)
):
    # Обрабатывает соединение, синхронизирует изменения между пользователями

    current_user = await get_current_user_ws(token, db)

    if not current_user:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await manager.connect(websocket, board_id, current_user.id)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "task_updated":
                await manager.broadcast_task_update(
                    board_id,
                    message["task"],
                    exclude_user=current_user.id
                )
            elif message["type"] == "task_deleted":
                await manager.broadcast_to_board(
                    board_id,
                    {
                        "type": "task_deleted",
                        "task_id": message["task_id"]
                    },
                    exclude_user=current_user.id
                )
            elif message["type"] == "column_updated":
                await manager.broadcast_column_update(
                    board_id,
                    message["column"],
                    exclude_user=current_user.id
                )
            elif message["type"] == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        await manager.disconnect(board_id, current_user.id)