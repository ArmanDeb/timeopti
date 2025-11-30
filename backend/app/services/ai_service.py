import os
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

from app.schemas.task import Task
from app.schemas.common import Event, Gap
from app.schemas.optimization import AgendaRequest

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

    def optimize_agenda(self, request: AgendaRequest) -> tuple[str, dict]:
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
            
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "model": response.model
            }
            
            return response.choices[0].message.content, usage
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return "Failed to optimize agenda.", {}

    def analyze_calendar_gaps(self, events: List[Event], start_window: str, end_window: str) -> List[Gap]:
        # Analyze gaps based on events
        # If events are in ISO format, extract time for simple gap analysis
        # or perform full datetime analysis
        
        gaps = []
        
        # For now, we'll try to extract HH:MM from ISO strings if necessary
        # to maintain compatibility with existing logic that expects HH:MM
        
        processed_events = []
        for event in events:
            start = event.start_time
            end = event.end_time
            
            # Try to convert ISO to HH:MM if it contains 'T'
            if 'T' in start:
                try:
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    start = dt.strftime("%H:%M")
                except:
                    pass
            
            if 'T' in end:
                try:
                    dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                    end = dt.strftime("%H:%M")
                except:
                    pass
            
            processed_events.append(Event(title=event.title, start_time=start, end_time=end))

        fmt = "%H:%M"
        sorted_events = sorted(processed_events, key=lambda x: x.start_time)
        
        try:
            current_time = datetime.strptime(start_window, fmt)
            end_time = datetime.strptime(end_window, fmt)

            for event in sorted_events:
                try:
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
                except ValueError:
                    continue # Skip invalid time formats

            if current_time < end_time:
                duration = int((end_time - current_time).total_seconds() / 60)
                if duration > 0:
                    gaps.append(Gap(
                        start_time=current_time.strftime(fmt),
                        end_time=end_time.strftime(fmt),
                        duration_minutes=duration
                    ))
        except ValueError:
            print(f"Error parsing time window: {start_window} - {end_window}")
        
        return gaps

    def get_priority_tasks(self, tasks: List[Task]) -> tuple[str, dict]:
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
            
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "model": response.model
            }
            
            return response.choices[0].message.content, usage
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return "Failed to prioritize tasks.", {}

    def detect_scope_from_input(self, natural_input: str) -> tuple[str, str]:
        """
        Detect if the user wants to optimize 'today', 'tomorrow', or 'this week' from their input.
        Returns (scope, target_date) where target_date is 'today', 'tomorrow', or 'week'
        """
        input_lower = natural_input.lower()
        
        # Check for tomorrow
        tomorrow_keywords = ['tomorrow', 'demain']
        if any(keyword in input_lower for keyword in tomorrow_keywords):
            return ('today', 'tomorrow')  # Use 'today' scope but for tomorrow's date
        
        # Check for explicit week indicators
        week_keywords = ['this week', 'week', 'weekly', 'cette semaine', 'semaine']
        if any(keyword in input_lower for keyword in week_keywords):
            return ('week', 'week')
        
        # Check for explicit today indicators
        today_keywords = ['today', "aujourd'hui", 'ce jour']
        if any(keyword in input_lower for keyword in today_keywords):
            return ('today', 'today')
        
        # Default to today if not specified
        return ('today', 'today')
    
    def parse_natural_language_to_tasks(self, natural_input: str, scope: str) -> tuple[List[Task], dict]:
        """
        Parse natural language input into structured tasks with context awareness.
        
        Example: "today I want to study, have breakfast and visit friend"
        -> [
            Task(title="Breakfast", duration=30, priority="high", ...),
            Task(title="Study", duration=120, priority="medium", ...),
            Task(title="Visit friend", duration=90, priority="medium", ...)
        ]
        """
        prompt = f"""
TASK: Split the user's input into SEPARATE individual activities.

USER INPUT: "{natural_input}"
SCOPE: {scope}

SPLITTING RULES (MANDATORY):
1. Count the activities mentioned (gym, dinner, games = 3 activities)
2. Create ONE JSON object per activity
3. If user says "gym, dinner, games" → create 3 separate objects
4. If user says "breakfast and study" → create 2 separate objects
5. NEVER merge activities into one object

For EACH SEPARATE activity, extract:

1. **Title**: Clear, concise task name
2. **Duration**: Realistic estimate in minutes
   - Breakfast: 20-30 min
   - Lunch/Dinner: 30-60 min
   - Study session: 60-120 min (optimal: 90 min with breaks)
   - Work/Project: 60-180 min
   - Exercise/Gym: 45-60 min
   - Social visit: 60-120 min
   - Commute: 15-45 min

3. **Priority**: Intelligent priority based on:
   - Meals: high (physiological need)
   - Urgent keywords (must, need, deadline, important): high
   - Work/Study: medium-high
   - Social/Leisure: medium-low

4. **Time preference**: When this task should ideally occur
   - Breakfast: 07:00-09:00 (morning energy)
   - Lunch: 12:00-14:00 (midday)
   - Dinner: 18:00-20:00 (evening)
   - Study/Deep work: 09:00-12:00 or 14:00-17:00 (peak cognitive hours)
   - Exercise: 07:00-09:00 or 17:00-19:00 (energy peaks)
   - Meetings: 10:00-16:00 (business hours)
   - Social: 14:00-21:00 (afternoon/evening)
   - Creative work: 09:00-12:00 (morning clarity)

5. **Reasoning**: WHY this task should be at this time (for explanations)

OUTPUT FORMAT (MANDATORY):
Return a JSON object with a "tasks" array. Each activity gets its own object in the array.

Example 1:
Input: "go to gym, have dinner, play games"
Output:
{{
  "tasks": [
    {{"id": "1", "title": "Go to gym", "duration_minutes": 60, "priority": "medium", "time_preference": "evening", "reasoning": "Evening workout"}},
    {{"id": "2", "title": "Have dinner", "duration_minutes": 60, "priority": "high", "time_preference": "evening", "reasoning": "Evening meal"}},
    {{"id": "3", "title": "Play games", "duration_minutes": 90, "priority": "low", "time_preference": "evening", "reasoning": "Leisure before bed"}}
  ]
}}

Example 2:
Input: "clean room and study"
Output:
{{
  "tasks": [
    {{"id": "1", "title": "Clean room", "duration_minutes": 30, "priority": "medium", "time_preference": "morning", "reasoning": "Morning cleaning"}},
    {{"id": "2", "title": "Study", "duration_minutes": 90, "priority": "high", "time_preference": "morning", "reasoning": "Peak focus hours"}}
  ]
}}

CRITICAL: Count activities in input. Output MUST have same number of objects in "tasks" array.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": """You are a task extraction AI. Your ONLY job is to split activities into separate tasks.
CRITICAL RULES:
1. Each activity = ONE separate task object
2. "gym, dinner, games" = 3 separate objects
3. NEVER combine multiple activities into one task
4. Return a JSON array with one object per activity"""},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Lower temperature for more deterministic output
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            content = response.choices[0].message.content
            print(f"AI Response: {content}")
            
            # Parse JSON response
            import json
            response_data = json.loads(content)
            
            # Handle both formats: {"tasks": [...]} or [...]
            if isinstance(response_data, dict) and 'tasks' in response_data:
                tasks_data = response_data['tasks']
            elif isinstance(response_data, list):
                tasks_data = response_data
            else:
                print(f"Unexpected response format: {response_data}")
                tasks_data = []
            
            print(f"Extracted {len(tasks_data)} tasks from AI response")
            
            # Convert to Task objects
            tasks = []
            for i, task_data in enumerate(tasks_data):
                task = Task(
                    id=task_data.get('id', str(i+1)),
                    title=task_data['title'],
                    duration_minutes=task_data['duration_minutes'],
                    priority=task_data.get('priority', 'medium'),
                    deadline=None,  # Can be added later if needed
                    time_preference=task_data.get('time_preference'),
                    reasoning=task_data.get('reasoning', 'Optimal time based on task type')
                )
                tasks.append(task)
                print(f"Task {i+1}: {task.title} ({task.duration_minutes}min)")
            
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "model": response.model
            }
            
            return tasks, usage
            
        except Exception as e:
            print(f"Error parsing natural language: {e}")
            # Fallback: create a single generic task
            return [Task(
                id="1",
                title=natural_input[:50],
                duration_minutes=60,
                priority="medium"
            )], {}

    def _build_prompt(self, request: AgendaRequest) -> str:
        tasks_str = "\n".join([f"- {t.title} ({t.duration_minutes}m) [{t.priority}]" for t in request.tasks])
        return f"""
        Please optimize the following agenda:
        
        Time Window: {request.start_time} to {request.end_time}
        
        Tasks:
        {tasks_str}
        
        Output a schedule with start and end times for each task.
        """

    def llm_assign_tasks_to_slots(
        self, 
        natural_input: str, 
        free_slots: List, 
        target_date: str, 
        timezone: str = "UTC"
    ) -> tuple[dict, dict]:
        """
        Probabilistic layer: Use LLM to split tasks and assign them to provided free slots.
        """
        import json
        
        # Format free slots for prompt
        slots_str = json.dumps([
            {"id": s.id, "start": s.start, "end": s.end, "duration_minutes": s.duration_minutes} 
            for s in free_slots
        ])
        
        prompt = f"""
        You are a scheduling engine.
        
        Context:
        - Date: {target_date}
        - Timezone: {timezone}
        - Free Slots: {slots_str}
        
        User Input: "{natural_input}"
        
        Your Goal:
        1. Parse distinct tasks from the input.
        2. Estimate duration for each task (e.g. Gym=60m, Dinner=90m) if not specified.
        3. Assign each task to a specific FREE SLOT from the provided list.
        
        Rules:
        - Assign times strictly within the start/end of a free slot.
        - Start and End times MUST be multiples of 15 minutes (e.g., 00, 15, 30, 45). Never use 13:20, 14:10, etc.
        - Do not overlap tasks.
        - Respect context: 
          * Dinner -> Evening (18:00+)
          * Shopping -> Business hours (09:00-19:00)
          * Gym -> Flexible (Morning/Evening preferred)
          * Study -> Morning/Afternoon
        - Act as a Productivity Strategist (Coach Exécutif).
        - Reasoning MUST be analytical, motivating but serious, and performance-oriented.
        - Briefly explain WHY this task is placed at this time (e.g., "morning energy peak", "avoiding fragmentation").
        - Use formal/sophisticated language.
        - Reasoning MUST be in the SAME LANGUAGE as the "User Input".
        - Reasoning MUST be personal (use "you", "your").
        - **IMPORTANT**: Include healthy breaks (5-15 minutes) between tasks to prevent burnout, especially after long deep work sessions.
        - Avoid back-to-back tasks if possible, unless they are related or short.
        - Ensure the schedule is realistic and sustainable.
        
        Output JSON Schema:
        {{
          "proposals": [
            {{
              "task_name": "string",
              "estimated_duration_minutes": int,
              "assigned_date": "YYYY-MM-DD",
              "assigned_start_time": "HH:MM",
              "assigned_end_time": "HH:MM",
              "slot_id": "string",
              "reasoning": "string (Analytical, performance-oriented, personal, formal, and in the detected language. E.g., 'Placed at 09:00 to leverage your morning concentration peak.')"
            }}
          ]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful scheduling assistant. Return JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "model": response.model
            }
            
            return json.loads(content), usage
            
        except Exception as e:
            print(f"Error in llm_assign_tasks_to_slots: {e}")
            return {"proposals": []}, {}
