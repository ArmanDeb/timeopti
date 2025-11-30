from pydantic import BaseModel
from typing import Optional

class Task(BaseModel):
    id: str
    title: str
    duration_minutes: int
    priority: str  # "high", "medium", "low"
    deadline: Optional[str] = None
    time_preference: Optional[str] = None  # "morning", "afternoon", "evening"
    reasoning: Optional[str] = None  # Why this task should be at this time
