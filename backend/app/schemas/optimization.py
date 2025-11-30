from pydantic import BaseModel
from typing import List, Optional, Dict
from app.schemas.task import Task
from app.schemas.common import Event

class SmartOptimizeRequest(BaseModel):
    tasks: List[Task]
    calendar_tokens: Optional[Dict] = None
    events: Optional[List[Event]] = None  # Manual events if no tokens
    start_window: str = "09:00"
    end_window: str = "17:00"

class NaturalOptimizeRequest(BaseModel):
    natural_input: str
    scope: str  # "today" or "week"
    start_window: str = "09:00"
    end_window: str = "17:00"
    events: Optional[List[Event]] = None  # Optional calendar events

class GapRequest(BaseModel):
    events: List[Event]
    start_window: str
    end_window: str

class PriorityRequest(BaseModel):
    tasks: List[Task]

class AgendaRequest(BaseModel):
    tasks: List[Task]
    start_time: str
    end_time: str

class AnalyzeRequest(BaseModel):
    natural_input: str
    tokens: Optional[Dict] = None  # Calendar tokens for fetching events
    timezone: Optional[str] = "UTC"
    sleep_start: Optional[str] = "23:00"
    sleep_end: Optional[str] = "07:00"
    start_from_now: Optional[bool] = True
    target_date: Optional[str] = None  # YYYY-MM-DD format, defaults to today if not provided
    existing_tasks: Optional[List[Dict]] = []  # Tasks already scheduled for this day

class ScheduledTaskProposal(BaseModel):
    task_name: str
    estimated_duration_minutes: int
    assigned_date: str
    assigned_start_time: str
    assigned_end_time: str
    reasoning: Optional[str] = None

class CommitScheduleRequest(BaseModel):
    tokens: Dict
    proposals: List[ScheduledTaskProposal]
    timezone: str = "UTC"
