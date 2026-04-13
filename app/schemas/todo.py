from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = 2
    due_date: Optional[datetime] = None

class TodoResponse(TodoCreate):
    id: int
    is_completed: bool
    created_at: datetime
    