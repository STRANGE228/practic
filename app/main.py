from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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

templates = Jinja2Templates(directory="app/templates")
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

@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    return templates.TemplateResponse(
        "errors/404.html",
        {"request": request},
        status_code=404
    )
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(request: Request, path: str):
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse(
        "errors/404.html",
        {"request": request},
        status_code=404
    )