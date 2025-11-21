from fastapi import FastAPI, Depends
from auth import get_current_user

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.ai_service import AIService, AgendaRequest

app = FastAPI()
ai_service = AIService()

# Configure CORS
origins = [
    "http://localhost:4200",
    "https://timeopti.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello World from TimeOpti Backend"}

@app.post("/optimize")
def optimize_agenda(request: AgendaRequest):
    return {"optimized_agenda": ai_service.optimize_agenda(request)}

from services.ai_service import Event, Task
from typing import List

class GapRequest(BaseModel):
    events: List[Event]
    start_window: str
    end_window: str

class PriorityRequest(BaseModel):
    tasks: List[Task]

@app.post("/analyze/gaps")
def analyze_gaps(request: GapRequest):
    gaps = ai_service.analyze_calendar_gaps(request.events, request.start_window, request.end_window)
    return {"gaps": gaps}

@app.post("/analyze/priorities")
def analyze_priorities(request: PriorityRequest):
    priorities = ai_service.get_priority_tasks(request.tasks)
    return {"priorities": priorities}

@app.get("/protected")
def read_protected(user: dict = Depends(get_current_user)):
    return {"message": "You are authenticated", "user_id": user.get("sub")}
