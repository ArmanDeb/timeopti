from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.all_models import Task, ScheduledTask, User
from pydantic import BaseModel
import uuid

router = APIRouter()

# --- Pydantic Models ---

class TaskCreate(BaseModel):
    title: str
    duration_minutes: int
    priority: str = "medium"
    deadline: Optional[str] = None

class TaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    duration_minutes: int
    priority: str
    deadline: Optional[str]
    
    class Config:
        from_attributes = True

class ScheduledTaskCreate(BaseModel):
    task_name: str
    estimated_duration_minutes: int
    assigned_date: str
    assigned_start_time: str
    assigned_end_time: str
    slot_id: Optional[str] = None
    reasoning: Optional[str] = None

class ScheduledTaskUpdate(BaseModel):
    assigned_date: Optional[str] = None
    assigned_start_time: Optional[str] = None
    assigned_end_time: Optional[str] = None

class ScheduledTaskResponse(ScheduledTaskCreate):
    id: uuid.UUID
    
    class Config:
        from_attributes = True

# --- Helper ---
def get_user(db: Session, user_data: dict) -> User:
    clerk_id = user_data.get("sub")
    user = db.query(User).filter(User.clerk_user_id == clerk_id).first()
    if not user:
        # Auto-create for now if missing (should be handled by auth/webhook)
        email = user_data.get("email", f"{clerk_id}@noemail.com")
        user = User(clerk_user_id=clerk_id, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# --- Tasks Endpoints ---

@router.get("/tasks", response_model=dict)
def get_tasks(user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user(db, user_data)
    tasks = db.query(Task).filter(Task.user_id == user.id).all()
    return {"tasks": tasks}

@router.post("/tasks", response_model=TaskResponse)
def create_task(task_in: TaskCreate, user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user(db, user_data)
    task = Task(
        user_id=user.id,
        title=task_in.title,
        duration_minutes=task_in.duration_minutes,
        priority=task_in.priority,
        deadline=task_in.deadline
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.delete("/tasks/all")
def delete_all_tasks(user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user(db, user_data)
    count = db.query(Task).filter(Task.user_id == user.id).delete()
    db.commit()
    return {"success": True, "deleted_count": count}

@router.delete("/tasks/{task_id}")
def delete_task(task_id: str, user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user(db, user_data)
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"success": True}

# --- Scheduled Tasks Endpoints ---

@router.get("/scheduled-tasks", response_model=dict[str, List[ScheduledTaskResponse]])
def get_scheduled_tasks(user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user(db, user_data)
    tasks = db.query(ScheduledTask).filter(ScheduledTask.user_id == user.id).all()
    return {"tasks": tasks}

@router.post("/scheduled-tasks")
def create_scheduled_tasks(tasks_in: List[ScheduledTaskCreate], user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user(db, user_data)
    created_tasks = []
    for t_in in tasks_in:
        task = ScheduledTask(
            user_id=user.id,
            task_name=t_in.task_name,
            estimated_duration_minutes=t_in.estimated_duration_minutes,
            assigned_date=t_in.assigned_date,
            assigned_start_time=t_in.assigned_start_time,
            assigned_end_time=t_in.assigned_end_time,
            slot_id=t_in.slot_id,
            reasoning=t_in.reasoning
        )
        db.add(task)
        created_tasks.append(task)
    
    db.commit()
    return {"success": True, "count": len(created_tasks)}

@router.delete("/scheduled-tasks/all")
def delete_all_scheduled_tasks(user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user(db, user_data)
    count = db.query(ScheduledTask).filter(ScheduledTask.user_id == user.id).delete()
    db.commit()
    return {"success": True, "deleted_count": count}

@router.patch("/scheduled-tasks/{task_id}")
def update_scheduled_task(task_id: str, updates: ScheduledTaskUpdate, user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user(db, user_data)
    # Try to find by ID (if it's a valid UUID)
    task = None
    try:
        # Check if task_id is a valid UUID
        uuid_obj = uuid.UUID(task_id)
        task = db.query(ScheduledTask).filter(ScheduledTask.id == uuid_obj, ScheduledTask.user_id == user.id).first()
    except ValueError:
        pass # Not a valid UUID, so it can't be the primary key

    # If not found by ID, try finding by slot_id as fallback
    if not task:
        task = db.query(ScheduledTask).filter(ScheduledTask.slot_id == task_id, ScheduledTask.user_id == user.id).first()
        
    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")
    
    if updates.assigned_date:
        task.assigned_date = updates.assigned_date
    if updates.assigned_start_time:
        task.assigned_start_time = updates.assigned_start_time
    if updates.assigned_end_time:
        task.assigned_end_time = updates.assigned_end_time
        
    db.commit()
    db.refresh(task)
    return {"success": True, "task": task}
