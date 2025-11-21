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

class Event(BaseModel):
    title: str
    start_time: str  # ISO format or HH:MM
    end_time: str

class Gap(BaseModel):
    start_time: str
    end_time: str
    duration_minutes: int

class AIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = None
        
        if not api_key:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if api_key:
                base_url = "https://openrouter.ai/api/v1"
        
        if not api_key:
            print("Warning: No API Key found (OPENAI_API_KEY or OPENROUTER_API_KEY)")

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

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

    def analyze_calendar_gaps(self, events: List[Event], start_window: str, end_window: str) -> List[Gap]:
        # Simple logic-based gap analysis (assuming HH:MM for simplicity in this demo)
        # In a real app, use datetime objects
        from datetime import datetime, timedelta

        fmt = "%H:%M"
        sorted_events = sorted(events, key=lambda x: x.start_time)
        gaps = []
        
        current_time = datetime.strptime(start_window, fmt)
        end_time = datetime.strptime(end_window, fmt)

        for event in sorted_events:
            event_start = datetime.strptime(event.start_time, fmt)
            event_end = datetime.strptime(event.end_time, fmt)

            if event_start > current_time:
                duration = int((event_start - current_time).total_seconds() / 60)
                if duration > 0:
                    gaps.append(Gap(
                        start_time=current_time.strftime(fmt),
                        end_time=event_start.strftime(fmt),
                        duration_minutes=duration
                    ))
            
            current_time = max(current_time, event_end)

        if current_time < end_time:
            duration = int((end_time - current_time).total_seconds() / 60)
            if duration > 0:
                gaps.append(Gap(
                    start_time=current_time.strftime(fmt),
                    end_time=end_time.strftime(fmt),
                    duration_minutes=duration
                ))
        
        return gaps

    def get_priority_tasks(self, tasks: List[Task]) -> str:
        tasks_str = "\n".join([f"- {t.title} (Priority: {t.priority})" for t in tasks])
        prompt = f"""
        Analyze the following tasks and identify the top 3 highest priority tasks based on the Eisenhower Matrix.
        Explain why they are important.

        Tasks:
        {tasks_str}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a productivity expert. Prioritize tasks effectively."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return "Failed to prioritize tasks."

    def _build_prompt(self, request: AgendaRequest) -> str:
        tasks_str = "\n".join([f"- {t.title} ({t.duration_minutes}m) [{t.priority}]" for t in request.tasks])
        return f"""
        Please optimize the following agenda:
        
        Time Window: {request.start_time} to {request.end_time}
        
        Tasks:
        {tasks_str}
        
        Output a schedule with start and end times for each task.
        """
