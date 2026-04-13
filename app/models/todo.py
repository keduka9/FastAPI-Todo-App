from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    is_completed: bool = False
    priority: int = Field(default=2, ge=1, le=3)    # 1: 高, 2: 中, 3: 低
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)