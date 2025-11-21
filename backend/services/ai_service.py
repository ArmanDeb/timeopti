import os
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Optional

class Task(BaseModel):
    id: str
    title: str
    duration_minutes: int
    priority: str  # "high", "medium", "low"
    deadline: Optional[str] = None

class AgendaRequest(BaseModel):
    tasks: List[Task]
    start_time: str
    end_time: str

class AIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def optimize_agenda(self, request: AgendaRequest) -> str:
        prompt = self._build_prompt(request)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert time management assistant. Organize the following tasks into an optimized schedule."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return "Failed to optimize agenda."

    def _build_prompt(self, request: AgendaRequest) -> str:
        tasks_str = "\n".join([f"- {t.title} ({t.duration_minutes}m) [{t.priority}]" for t in request.tasks])
        return f"""
        Please optimize the following agenda:
        
        Time Window: {request.start_time} to {request.end_time}
        
        Tasks:
        {tasks_str}
        
        Output a schedule with start and end times for each task.
        """
