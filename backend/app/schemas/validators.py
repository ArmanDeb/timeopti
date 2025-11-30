"""
Input validators for TimeOpti API
"""
from typing import List, Optional
from datetime import datetime
from app.core.exceptions import ValidationError

class TimeValidator:
    """Validates time-related inputs"""
    
    @staticmethod
    def validate_time_format(time_str: str) -> bool:
        """Validate HH:MM format"""
        try:
            datetime.strptime(time_str, '%H:%M')
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_time_range(start: str, end: str) -> bool:
        """Validate that end time is after start time"""
        try:
            start_dt = datetime.strptime(start, '%H:%M')
            end_dt = datetime.strptime(end, '%H:%M')
            return end_dt > start_dt
        except ValueError:
            return False
    
    @staticmethod
    def validate_duration(duration_minutes: int) -> bool:
        """Validate task duration (5 min to 8 hours)"""
        return 5 <= duration_minutes <= 480

class TaskValidator:
    """Validates task inputs"""
    
    VALID_PRIORITIES = ['high', 'medium', 'low']
    
    @staticmethod
    def validate_task(task: dict) -> None:
        """Validate a single task"""
        errors = []
        
        # Check required fields
        if not task.get('title'):
            errors.append("Task title is required")
        elif len(task['title']) > 200:
            errors.append("Task title must be 200 characters or less")
        
        # Validate duration
        duration = task.get('duration_minutes')
        if duration is None:
            errors.append("Task duration_minutes is required")
        elif not isinstance(duration, int):
            errors.append("Task duration_minutes must be an integer")
        elif not TimeValidator.validate_duration(duration):
            errors.append("Task duration must be between 5 and 480 minutes")
        
        # Validate priority
        priority = task.get('priority', 'medium')
        if priority not in TaskValidator.VALID_PRIORITIES:
            errors.append(f"Task priority must be one of: {', '.join(TaskValidator.VALID_PRIORITIES)}")
        
        # Validate deadline if provided
        deadline = task.get('deadline')
        if deadline:
            try:
                datetime.fromisoformat(deadline)
            except ValueError:
                errors.append("Task deadline must be in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
        
        if errors:
            raise ValidationError("; ".join(errors))
    
    @staticmethod
    def validate_tasks(tasks: List[dict]) -> None:
        """Validate list of tasks"""
        if not tasks:
            raise ValidationError("At least one task is required")
        
        if len(tasks) > 50:
            raise ValidationError("Maximum 50 tasks allowed per optimization")
        
        for idx, task in enumerate(tasks):
            try:
                TaskValidator.validate_task(task)
            except ValidationError as e:
                raise ValidationError(f"Task {idx + 1}: {e.message}")

class EventValidator:
    """Validates calendar event inputs"""
    
    @staticmethod
    def validate_event(event: dict) -> None:
        """Validate a single calendar event"""
        errors = []
        
        # Check required fields
        if not event.get('title'):
            errors.append("Event title is required")
        
        start_time = event.get('start_time')
        end_time = event.get('end_time')
        
        if not start_time:
            errors.append("Event start_time is required")
        elif not TimeValidator.validate_time_format(start_time):
            errors.append("Event start_time must be in HH:MM format")
        
        if not end_time:
            errors.append("Event end_time is required")
        elif not TimeValidator.validate_time_format(end_time):
            errors.append("Event end_time must be in HH:MM format")
        
        # Validate time range
        if start_time and end_time:
            if not TimeValidator.validate_time_range(start_time, end_time):
                errors.append("Event end_time must be after start_time")
        
        if errors:
            raise ValidationError("; ".join(errors))
    
    @staticmethod
    def validate_events(events: List[dict]) -> None:
        """Validate list of events"""
        if len(events) > 100:
            raise ValidationError("Maximum 100 events allowed")
        
        for idx, event in enumerate(events):
            try:
                EventValidator.validate_event(event)
            except ValidationError as e:
                raise ValidationError(f"Event {idx + 1}: {e.message}")

class OptimizationValidator:
    """Validates optimization request inputs"""
    
    @staticmethod
    def validate_optimization_request(request_data: dict) -> None:
        """Validate smart optimization request"""
        errors = []
        
        # Validate time window
        start_window = request_data.get('start_window', '09:00')
        end_window = request_data.get('end_window', '17:00')
        
        if not TimeValidator.validate_time_format(start_window):
            errors.append("start_window must be in HH:MM format")
        
        if not TimeValidator.validate_time_format(end_window):
            errors.append("end_window must be in HH:MM format")
        
        if start_window and end_window:
            if not TimeValidator.validate_time_range(start_window, end_window):
                errors.append("end_window must be after start_window")
        
        if errors:
            raise ValidationError("; ".join(errors))
        
        # Validate tasks
        tasks = request_data.get('tasks', [])
        TaskValidator.validate_tasks(tasks)
        
        # Validate events if provided
        events = request_data.get('events', [])
        if events:
            EventValidator.validate_events(events)
