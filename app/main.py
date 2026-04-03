from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.database import engine
from app.models import user, board, column, task, task_image, board_member, invitation
from app.web.routes import home, auth_routes, board_routes, column_routes, task_routes, invitation_routes
from app.websocket.endpoints import websocket_endpoint

user.Base.metadata.create_all(bind=engine)
board.Base.metadata.create_all(bind=engine)
column.Base.metadata.create_all(bind=engine)
task.Base.metadata.create_all(bind=engine)
task_image.Base.metadata.create_all(bind=engine)
board_member.Base.metadata.create_all(bind=engine)
invitation.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kanban Board")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_api_websocket_route("/ws/{board_id}/{token}", websocket_endpoint)

app.include_router(home.router)
app.include_router(auth_routes.router)
app.include_router(board_routes.router)
app.include_router(column_routes.router)
app.include_router(task_routes.router)
app.include_router(invitation_routes.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}