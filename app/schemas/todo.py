from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from pydantic import field_validator

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = 2
    due_date: Optional[date] = None

    @classmethod
    @field_validator("due_date", "description", mode="before")
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v

class TodoResponse(TodoCreate):
    id: int
    is_completed: bool
    created_at: datetime
    