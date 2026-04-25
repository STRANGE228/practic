from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = ""
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    column_id: int


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    column_id: Optional[int] = None
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None


class TaskResponse(TaskBase):
    id: int
    column_id: int
    order: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    status_display: str
    is_overdue: bool

    class Config:
        from_attributes = True