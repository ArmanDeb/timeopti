from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from services.ai_service import Task, Event, Gap
from pydantic import BaseModel

class ScheduledTask(BaseModel):
    task: Task
    start_time: str  # HH:MM format
    end_time: str
    gap_index: int  # Which gap was used
    fit_score: float  # How well it fits

class ScheduleResult(BaseModel):
    scheduled_tasks: List[ScheduledTask]
    unscheduled_tasks: List[Task]
    explanation: str
    success: bool

class TaskMatcher:
    """
    Intelligent task-to-calendar-gap matching service.
    Uses a hybrid approach: logic-based matching + AI explanations.
    """
    
    def __init__(self):
        self.priority_weights = {
            "high": 3.0,
            "medium": 2.0,
            "low": 1.0
        }
    
    def match_tasks_to_gaps(
        self, 
        tasks: List[Task], 
        gaps: List[Gap],
        preferences: Optional[dict] = None
    ) -> ScheduleResult:
        """
        Match tasks to calendar gaps using intelligent algorithm.
        
        Algorithm:
        1. Sort tasks by priority (high first) and deadline
        2. For each task, find best fitting gap
        3. Assign task to gap and update remaining gap space
        4. Return scheduled and unscheduled tasks
        """
        if not tasks:
            return ScheduleResult(
                scheduled_tasks=[],
                unscheduled_tasks=[],
                explanation="No tasks to schedule.",
                success=True
            )
        
        if not gaps:
            return ScheduleResult(
                scheduled_tasks=[],
                unscheduled_tasks=tasks,
                explanation="No available time gaps found in calendar.",
                success=False
            )
        
        # Sort tasks by priority and deadline
        sorted_tasks = self._prioritize_tasks(tasks)
        
        # Track available gaps (mutable list of remaining gap time)
        available_gaps = [gap.model_copy(deep=True) for gap in gaps]
        
        scheduled = []
        unscheduled = []
        
        for task in sorted_tasks:
            best_match = self._find_best_gap(task, available_gaps)
            
            if best_match:
                gap_index, gap, fit_score = best_match
                
                # Schedule the task
                scheduled_task = self._schedule_task_in_gap(task, gap, gap_index, fit_score)
                scheduled.append(scheduled_task)
                
                # Update gap availability
                self._update_gap_after_assignment(available_gaps, gap_index, task.duration_minutes)
            else:
                unscheduled.append(task)
        
        explanation = self._generate_explanation(scheduled, unscheduled, gaps)
        
        return ScheduleResult(
            scheduled_tasks=scheduled,
            unscheduled_tasks=unscheduled,
            explanation=explanation,
            success=len(unscheduled) == 0
        )
    
    def _prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by priority (high first), then by deadline."""
        def sort_key(task: Task):
            priority_score = self.priority_weights.get(task.priority.lower(), 1.0)
            # Higher priority = lower sort value (comes first)
            # Earlier deadline = lower sort value (comes first)
            deadline_score = 0
            if task.deadline:
                try:
                    deadline_dt = datetime.fromisoformat(task.deadline)
                    # Convert to timestamp for sorting
                    deadline_score = deadline_dt.timestamp()
                except:
                    deadline_score = float('inf')
            else:
                deadline_score = float('inf')
            
            return (-priority_score, deadline_score)
        
        return sorted(tasks, key=sort_key)
    
    def _find_best_gap(
        self, 
        task: Task, 
        gaps: List[Gap]
    ) -> Optional[Tuple[int, Gap, float]]:
        """
        Find the best gap for a task.
        Returns (gap_index, gap, fit_score) or None if no suitable gap.
        """
        best_match = None
        best_score = -1
        
        for i, gap in enumerate(gaps):
            if gap.duration_minutes >= task.duration_minutes:
                score = self._calculate_fit_score(task, gap)
                if score > best_score:
                    best_score = score
                    best_match = (i, gap, score)
        
        return best_match
    
    def _calculate_fit_score(self, task: Task, gap: Gap) -> float:
        """
        Calculate how well a task fits a gap.
        Higher score = better fit.
        
        Factors:
        - Efficiency: Prefer gaps that minimize wasted time
        - Priority: High priority tasks get preference for good slots
        - Time of day: Morning gaps slightly preferred for high priority
        """
        # Efficiency score: penalize large gaps for small tasks
        waste = gap.duration_minutes - task.duration_minutes
        efficiency = 1.0 - (waste / gap.duration_minutes)
        
        # Priority boost
        priority_boost = self.priority_weights.get(task.priority.lower(), 1.0) / 3.0
        
        # Time of day preference (morning = higher score for high priority)
        try:
            gap_hour = int(gap.start_time.split(':')[0])
            if gap_hour >= 9 and gap_hour <= 11 and task.priority.lower() == "high":
                time_boost = 0.2
            else:
                time_boost = 0
        except:
            time_boost = 0
        
        total_score = efficiency + priority_boost + time_boost
        return total_score
    
    def _schedule_task_in_gap(
        self, 
        task: Task, 
        gap: Gap, 
        gap_index: int,
        fit_score: float
    ) -> ScheduledTask:
        """Create a scheduled task from a task and gap."""
        from datetime import datetime, timedelta
        
        # Parse gap start time
        start = datetime.strptime(gap.start_time, "%H:%M")
        end = start + timedelta(minutes=task.duration_minutes)
        
        return ScheduledTask(
            task=task,
            start_time=start.strftime("%H:%M"),
            end_time=end.strftime("%H:%M"),
            gap_index=gap_index,
            fit_score=fit_score
        )
    
    def _update_gap_after_assignment(
        self, 
        gaps: List[Gap], 
        gap_index: int, 
        duration: int
    ):
        """Update gap after assigning a task to it."""
        gap = gaps[gap_index]
        
        # Calculate new gap start time
        from datetime import datetime, timedelta
        old_start = datetime.strptime(gap.start_time, "%H:%M")
        new_start = old_start + timedelta(minutes=duration)
        
        # Update gap
        gap.start_time = new_start.strftime("%H:%M")
        gap.duration_minutes -= duration
        
        # Remove gap if no time left
        if gap.duration_minutes <= 0:
            gaps.pop(gap_index)
    
    def _generate_explanation(
        self, 
        scheduled: List[ScheduledTask], 
        unscheduled: List[Task],
        original_gaps: List[Gap]
    ) -> str:
        """Generate human-readable explanation of scheduling decisions."""
        lines = []
        
        if scheduled:
            lines.append(f"✅ Successfully scheduled {len(scheduled)} task(s):")
            for st in scheduled:
                lines.append(
                    f"  • {st.task.title} ({st.start_time}-{st.end_time}) "
                    f"[{st.task.priority} priority]"
                )
        
        if unscheduled:
            lines.append(f"\n⚠️ Could not schedule {len(unscheduled)} task(s):")
            for task in unscheduled:
                lines.append(
                    f"  • {task.title} ({task.duration_minutes}m) - "
                    f"No suitable gap found"
                )
            
            total_gap_time = sum(g.duration_minutes for g in original_gaps)
            lines.append(
                f"\n💡 Tip: You have {total_gap_time} minutes of free time, "
                f"but it may be fragmented across multiple small gaps."
            )
        
        return "\n".join(lines)
