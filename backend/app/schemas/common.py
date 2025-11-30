from pydantic import BaseModel

class Event(BaseModel):
    title: str
    start_time: str  # ISO format or HH:MM
    end_time: str

class Gap(BaseModel):
    start_time: str
    end_time: str
    duration_minutes: int

class FreeSlot(BaseModel):
    id: str
    start: str  # HH:MM
    end: str    # HH:MM
    duration_minutes: int
