from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.database import engine
from app.models import board, task, user
from app.web.routes import home, board_routes, task_routes, auth_routes

board.Base.metadata.create_all(bind=engine)
task.Base.metadata.create_all(bind=engine)
user.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kanban")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(home.router)
app.include_router(board_routes.router)
app.include_router(task_routes.router)
app.include_router(auth_routes.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Kanban app is running"}