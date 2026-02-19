from pydantic import BaseModel

class TaskBase(BaseModel):
    title: str
    description: str | None = None
    status: str = "todo"

class TaskCreate(TaskBase):
    board_id: int

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    board_id: int | None = None

class Task(TaskBase):
    id: int
    board_id: int

    class Config:
        from_attributes = True