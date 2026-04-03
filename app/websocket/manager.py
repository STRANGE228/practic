from typing import Dict, Set, List
from fastapi import WebSocket
import json
import asyncio


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
        self.user_boards: Dict[int, int] = {}

    async def connect(self, websocket: WebSocket, board_id, user_id):
        await websocket.accept()

        if board_id not in self.active_connections:
            self.active_connections[board_id] = {}

        self.active_connections[board_id][user_id] = websocket
        self.user_boards[user_id] = board_id
        await self.broadcast_to_board(
            board_id,
            {
                "type": "user_connected",
                "user_id": user_id,
                "message": f"Пользователь подключился"
            },
            exclude_user=user_id
        )

    async def disconnect(self, board_id, user_id):
        if board_id in self.active_connections:
            if user_id in self.active_connections[board_id]:
                del self.active_connections[board_id][user_id]

            if not self.active_connections[board_id]:
                del self.active_connections[board_id]

        if user_id in self.user_boards:
            del self.user_boards[user_id]
        await self.broadcast_to_board(
            board_id,
            {
                "type": "user_disconnected",
                "user_id": user_id,
                "message": f"Пользователь отключился"
            }
        )

    async def send_personal_message(self, message, user_id):
        if user_id in self.user_boards:
            board_id = self.user_boards[user_id]
            if board_id in self.active_connections and user_id in self.active_connections[board_id]:
                websocket = self.active_connections[board_id][user_id]
                await websocket.send_json(message)

    async def broadcast_to_board(self, board_id, message, exclude_user = None):
        if board_id in self.active_connections:
            for user_id, connection in self.active_connections[board_id].items():
                if exclude_user is None or user_id != exclude_user:
                    try:
                        await connection.send_json(message)
                    except:
                        pass

    async def broadcast_task_update(self, board_id, task_data, exclude_user = None):
        await self.broadcast_to_board(board_id, {
            "type": "task_updated",
            "task": task_data
        }, exclude_user)

    async def broadcast_column_update(self, board_id, column_data, exclude_user = None):
        await self.broadcast_to_board(board_id, {
            "type": "column_updated",
            "column": column_data
        }, exclude_user)


manager = ConnectionManager()