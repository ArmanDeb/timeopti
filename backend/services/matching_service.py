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
    explanation: str  # Why this task was placed here

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
        - Time of day: Context-aware placement (breakfast in morning, etc.)
        - Task type: Meals, study, social activities have preferred times
        """
        # Efficiency score: penalize large gaps for small tasks
        waste = gap.duration_minutes - task.duration_minutes
        efficiency = 1.0 - (waste / gap.duration_minutes)
        
        # Priority boost
        priority_boost = self.priority_weights.get(task.priority.lower(), 1.0) / 3.0
        
        # Context-aware time preference
        time_boost = 0.0
        try:
            gap_hour = int(gap.start_time.split(':')[0])
            task_lower = task.title.lower()
            
            # Use explicit time_preference if provided by AI
            # CRITICAL: Strong boost/penalty to enforce time preferences
            if task.time_preference:
                pref = task.time_preference.lower()
                if pref == 'morning' and 7 <= gap_hour <= 12:
                    time_boost = 2.0  # Strong boost
                elif pref == 'afternoon' and 12 <= gap_hour <= 17:
                    time_boost = 2.0
                elif pref == 'evening' and 17 <= gap_hour <= 21:
                    time_boost = 2.0
                elif pref == 'midday' and 11 <= gap_hour <= 14:
                    time_boost = 2.0
                else:
                    time_boost = -5.0  # STRONG penalty for wrong time
            
            # Fallback to keyword-based detection
            
            # Breakfast: 7-10 AM (STRICT)
            if any(word in task_lower for word in ['breakfast', 'petit déjeuner']):
                if 7 <= gap_hour <= 10:
                    time_boost = 3.0  # Perfect time
                elif gap_hour < 7 or gap_hour > 12:
                    time_boost = -10.0  # ABSURD time - breakfast at night!
                else:
                    time_boost = -2.0
            
            # Lunch: 11 AM - 2 PM (STRICT)
            elif any(word in task_lower for word in ['lunch', 'déjeuner midi']):
                if 11 <= gap_hour <= 14:
                    time_boost = 3.0
                else:
                    time_boost = -8.0  # Wrong meal time
            
            # Dinner: 6-9 PM (STRICT) - includes "dinner with friends"
            elif any(word in task_lower for word in ['dinner', 'dîner', 'souper', 'diner']) or \
                 ('dinner' in task_lower and 'friend' in task_lower):
                if 18 <= gap_hour <= 21:
                    time_boost = 3.0  # Perfect evening time
                elif gap_hour < 12:
                    time_boost = -10.0  # ABSURD - dinner in the morning!
                elif 12 <= gap_hour < 17:
                    time_boost = -7.0  # Too early for dinner
                else:
                    time_boost = -5.0  # Still wrong
            
            # Study/Work: Morning/Early afternoon preferred
            elif any(word in task_lower for word in ['study', 'work', 'étudier', 'travailler', 'projet']):
                if 9 <= gap_hour <= 15:
                    time_boost = 1.5
                elif gap_hour >= 20:
                    time_boost = -3.0  # Too late for focused work
            
            # Social/Visit: Afternoon/Evening
            elif any(word in task_lower for word in ['visit', 'friend', 'social', 'visite', 'ami', 'friends']):
                if 14 <= gap_hour <= 21:
                    time_boost = 1.5  # Good social time
                elif gap_hour < 10:
                    time_boost = -5.0  # Too early for social visits
                else:
                    time_boost = -1.0
            
            # Exercise: Morning or late afternoon
            elif any(word in task_lower for word in ['exercise', 'gym', 'sport', 'workout']):
                if (7 <= gap_hour <= 9) or (17 <= gap_hour <= 19):
                    time_boost = 1.5
                elif gap_hour >= 21:
                    time_boost = -3.0  # Too late for exercise
            
            # High priority tasks: prefer morning slots
            elif task.priority.lower() == "high":
                if 9 <= gap_hour <= 12:
                    time_boost = 0.2
                    
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
        """Create a scheduled task from a task and gap with explanation."""
        from datetime import datetime, timedelta
        
        # Parse gap start time
        start = datetime.strptime(gap.start_time, "%H:%M")
        end = start + timedelta(minutes=task.duration_minutes)
        
        # Generate explanation
        explanation = self._generate_task_explanation(task, start.strftime("%H:%M"), fit_score)
        
        return ScheduledTask(
            task=task,
            start_time=start.strftime("%H:%M"),
            end_time=end.strftime("%H:%M"),
            gap_index=gap_index,
            fit_score=fit_score,
            explanation=explanation
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
    
    def _generate_task_explanation(self, task: Task, start_time: str, fit_score: float) -> str:
        """Generate a human-readable explanation for why this task was placed at this time."""
        hour = int(start_time.split(':')[0])
        task_lower = task.title.lower()
        
        # Use AI reasoning if available
        if task.reasoning:
            return task.reasoning
        
        # Generate contextual explanation
        explanations = []
        
        # Time-based reasoning
        if 7 <= hour <= 9:
            if any(word in task_lower for word in ['breakfast', 'petit déjeuner']):
                explanations.append("Optimal breakfast time for morning energy")
            elif any(word in task_lower for word in ['exercise', 'gym', 'sport']):
                explanations.append("Morning workout boosts metabolism and energy")
            elif any(word in task_lower for word in ['study', 'work', 'learn']):
                explanations.append("Morning hours offer peak cognitive performance")
        
        elif 9 <= hour <= 12:
            if any(word in task_lower for word in ['study', 'work', 'project', 'code']):
                explanations.append("Peak focus hours for deep work and complex tasks")
            elif any(word in task_lower for word in ['meeting', 'call']):
                explanations.append("Optimal time for collaborative work")
        
        elif 12 <= hour <= 14:
            if any(word in task_lower for word in ['lunch', 'déjeuner', 'repas']):
                explanations.append("Natural midday break for energy replenishment")
        
        elif 14 <= hour <= 17:
            if any(word in task_lower for word in ['study', 'work']):
                explanations.append("Good afternoon productivity window")
            elif any(word in task_lower for word in ['meeting', 'social']):
                explanations.append("Ideal for collaborative and social activities")
        
        elif 17 <= hour <= 19:
            if any(word in task_lower for word in ['exercise', 'gym', 'sport']):
                explanations.append("Evening workout helps decompress after work")
            elif any(word in task_lower for word in ['visit', 'friend', 'social']):
                explanations.append("Perfect time for social activities")
        
        elif 18 <= hour <= 21:
            if any(word in task_lower for word in ['dinner', 'dîner', 'souper']):
                explanations.append("Evening meal time for family and relaxation")
            elif any(word in task_lower for word in ['visit', 'friend']):
                explanations.append("Evening is ideal for social gatherings")
        
        # Priority-based reasoning
        if task.priority == 'high' and 9 <= hour <= 12:
            explanations.append("High priority task scheduled during peak hours")
        
        # Fit score reasoning
        if fit_score > 1.5:
            explanations.append(f"Perfect fit for this {task.duration_minutes}min time slot")
        
        return " • ".join(explanations) if explanations else f"Scheduled based on availability and task type"
    
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
