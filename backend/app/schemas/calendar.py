from pydantic import BaseModel
from typing import Optional, Dict

class CalendarAuthRequest(BaseModel):
    redirect_uri: str

class CalendarTokenRequest(BaseModel):
    code: str
    redirect_uri: str

class CalendarEventsRequest(BaseModel):
    tokens: Dict
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class TodayEventsRequest(BaseModel):
    tokens: Dict
