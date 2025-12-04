"""
Test script for matching service
"""
import sys
sys.path.insert(0, '/Users/arman/Documents/Projects/timeopti/backend')

from app.services.matching_service import TaskMatcher
from app.services.ai_service import Task, Gap

# Create test data
tasks = [
    Task(id="1", title="Write report", duration_minutes=60, priority="high"),
    Task(id="2", title="Email team", duration_minutes=30, priority="medium"),
    Task(id="3", title="Call client", duration_minutes=15, priority="high"),
    Task(id="4", title="Review docs", duration_minutes=45, priority="low"),
]

gaps = [
    Gap(start_time="09:00", end_time="10:00", duration_minutes=60),
    Gap(start_time="11:30", end_time="12:00", duration_minutes=30),
    Gap(start_time="14:00", end_time="15:30", duration_minutes=90),
]

# Run matching
matcher = TaskMatcher()
result = matcher.match_tasks_to_gaps(tasks, gaps)

print("=" * 60)
print("MATCHING ALGORITHM TEST")
print("=" * 60)
print(f"\nSuccess: {result.success}")
print(f"\nScheduled Tasks ({len(result.scheduled_tasks)}):")
for st in result.scheduled_tasks:
    print(f"  • {st.task.title}: {st.start_time}-{st.end_time} (fit score: {st.fit_score:.2f})")

print(f"\nUnscheduled Tasks ({len(result.unscheduled_tasks)}):")
for task in result.unscheduled_tasks:
    print(f"  • {task.title} ({task.duration_minutes}m)")

print(f"\nExplanation:\n{result.explanation}")
print("=" * 60)
