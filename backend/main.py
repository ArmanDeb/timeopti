from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from auth import get_current_user
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.ai_service import AIService, AgendaRequest, Event, Task
from services.matching_service import TaskMatcher, ScheduleResult
from services.google_calendar_service import GoogleCalendarService
from validators import OptimizationValidator, TaskValidator, EventValidator
from exceptions import TimeOptiException, ValidationError, CalendarError, OptimizationError
from typing import List, Optional
from sqlalchemy.orm import Session
from database import get_db, Base, engine
from models import User, AILog, Recommendation
import time
import json
import os

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI()
ai_service = AIService()
task_matcher = TaskMatcher()
gcal_service = GoogleCalendarService()

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

@app.exception_handler(TimeOptiException)
async def timeopti_exception_handler(request: Request, exc: TimeOptiException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )

# Helper function to get or create user
def get_or_create_user(clerk_user_id: str, email: str, db: Session) -> User:
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if not user:
        user = User(clerk_user_id=clerk_user_id, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@app.get("/")
def read_root():
    return {"message": "Hello World from TimeOpti Backend"}

# Google Calendar OAuth endpoints
class CalendarAuthRequest(BaseModel):
    redirect_uri: str

@app.post("/calendar/auth-url")
def get_calendar_auth_url(request: CalendarAuthRequest):
    """Get Google Calendar OAuth authorization URL"""
    try:
        auth_url = gcal_service.get_authorization_url(request.redirect_uri)
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CalendarTokenRequest(BaseModel):
    code: str
    redirect_uri: str

@app.post("/calendar/exchange-token")
def exchange_calendar_token(request: CalendarTokenRequest, user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Exchange OAuth code for tokens and store them"""
    try:
        tokens = gcal_service.exchange_code_for_tokens(request.code, request.redirect_uri)
        
        # Store tokens in user record (you'll need to add a tokens field to User model)
        # For now, just return them
        # TODO: Store in database
        
        return {"success": True, "tokens": tokens}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CalendarEventsRequest(BaseModel):
    tokens: dict
    start_date: Optional[str] = None
    end_date: Optional[str] = None

@app.post("/calendar/events")
def get_calendar_events(request: CalendarEventsRequest):
    """Fetch events from user's Google Calendar"""
    try:
        from datetime import datetime
        
        start = datetime.fromisoformat(request.start_date) if request.start_date else None
        end = datetime.fromisoformat(request.end_date) if request.end_date else None
        
        events = gcal_service.get_events(request.tokens, start, end)
        return {"events": [e.model_dump() for e in events]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Smart Optimization Endpoint
class SmartOptimizeRequest(BaseModel):
    tasks: List[Task]
    calendar_tokens: Optional[dict] = None
    events: Optional[List[Event]] = None  # Manual events if no tokens
    start_window: str = "09:00"
    end_window: str = "17:00"

@app.post("/smart-optimize")
def smart_optimize(request: SmartOptimizeRequest, db: Session = Depends(get_db)):
    """
    Smart task optimization using calendar integration and matching algorithm.
    
    Workflow:
    1. Get calendar events (from Google Calendar or manual input)
    2. Analyze gaps in the calendar
    3. Match tasks to gaps intelligently
    4. Return optimized schedule with explanations
    """
    start_time = time.time()
    error = None
    result = None
    
    try:
        # Validate input
        request_dict = request.model_dump()
        OptimizationValidator.validate_optimization_request(request_dict)
        
        # Step 1: Get calendar events
        try:
            if request.calendar_tokens:
                # Fetch from Google Calendar
                events = gcal_service.get_today_events(request.calendar_tokens)
            elif request.events:
                # Use manually provided events
                events = request.events
            else:
                # No events = full day available
                events = []
        except Exception as e:
            error_msg = f"Failed to fetch calendar events: {str(e)}"
            error = error_msg
            raise CalendarError(error_msg)
        
        # Step 2: Analyze gaps
        try:
            gaps = ai_service.analyze_calendar_gaps(events, request.start_window, request.end_window)
        except Exception as e:
            error_msg = f"Failed to analyze calendar gaps: {str(e)}"
            error = error_msg
            raise OptimizationError(error_msg)
        
        # Step 3: Match tasks to gaps
        try:
            schedule = task_matcher.match_tasks_to_gaps(request.tasks, gaps)
        except Exception as e:
            error_msg = f"Failed to match tasks to gaps: {str(e)}"
            error = error_msg
            raise OptimizationError(error_msg)
        
        # Step 4: Generate result
        if schedule.success:
            result = {
                "schedule": schedule.model_dump(),
                "gaps_found": [g.model_dump() for g in gaps],
                "events": [e.model_dump() for e in events]
            }
        else:
            result = {
                "schedule": schedule.model_dump(),
                "gaps_found": [g.model_dump() for g in gaps],
                "events": [e.model_dump() for e in events],
                "warning": "Some tasks could not be scheduled. Consider adjusting your time window or task priorities."
            }
        
        return result
        
    except Exception as e:
        error = str(e)
        raise HTTPException(status_code=500, detail=error)
    
    finally:
        # Log to database
        duration_ms = int((time.time() - start_time) * 1000)
        log = AILog(
            user_id=None,
            endpoint="/smart-optimize",
            request_data=request.model_dump(),
            response_data=result,
            duration_ms=duration_ms,
            error=error
        )
        db.add(log)
        db.commit()

class GapRequest(BaseModel):
    events: List[Event]
    start_window: str
    end_window: str

class PriorityRequest(BaseModel):
    tasks: List[Task]

@app.post("/optimize")
def optimize_agenda(request: AgendaRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    error = None
    result = None
    
    try:
        result = ai_service.optimize_agenda(request)
        return {"optimized_agenda": result}
    except Exception as e:
        error = str(e)
        raise HTTPException(status_code=500, detail=error)
    finally:
        duration_ms = int((time.time() - start_time) * 1000)
        # Log to database (anonymous for now, will add user tracking later)
        log = AILog(
            user_id=None,  # Will be populated when user auth is integrated
            endpoint="/optimize",
            request_data=request.model_dump(),
            response_data={"result": result} if result else None,
            duration_ms=duration_ms,
            error=error
        )
        db.add(log)
        db.commit()

@app.post("/analyze/gaps")
def analyze_gaps(request: GapRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    error = None
    result = None
    
    try:
        gaps = ai_service.analyze_calendar_gaps(request.events, request.start_window, request.end_window)
        result = {"gaps": [gap.dict() for gap in gaps]}
        return result
    except Exception as e:
        error = str(e)
        raise HTTPException(status_code=500, detail=error)
    finally:
        duration_ms = int((time.time() - start_time) * 1000)
        log = AILog(
            user_id=None,
            endpoint="/analyze/gaps",
            request_data=request.model_dump(),
            response_data=result,
            duration_ms=duration_ms,
            error=error
        )
        db.add(log)
        db.commit()

@app.post("/analyze/priorities")
def analyze_priorities(request: PriorityRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    error = None
    result = None
    
    try:
        priorities = ai_service.get_priority_tasks(request.tasks)
        result = {"priorities": priorities}
        return result
    except Exception as e:
        error = str(e)
        raise HTTPException(status_code=500, detail=error)
    finally:
        duration_ms = int((time.time() - start_time) * 1000)
        log = AILog(
            user_id=None,
            endpoint="/analyze/priorities",
            request_data=request.model_dump(),
            response_data=result,
            duration_ms=duration_ms,
            error=error
        )
        db.add(log)
        db.commit()

@app.get("/protected")
def read_protected(user: dict = Depends(get_current_user)):
    return {"message": "You are authenticated", "user_id": user.get("sub")}

# Admin Endpoints
@app.get("/admin/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    """Get overall system statistics"""
    total_users = db.query(User).count()
    total_logs = db.query(AILog).count()
    total_recommendations = db.query(Recommendation).count()
    
    # Get endpoint usage breakdown
    from sqlalchemy import func
    endpoint_stats = db.query(
        AILog.endpoint,
        func.count(AILog.id).label('count'),
        func.avg(AILog.duration_ms).label('avg_duration')
    ).group_by(AILog.endpoint).all()
    
    return {
        "total_users": total_users,
        "total_logs": total_logs,
        "total_recommendations": total_recommendations,
        "endpoint_stats": [
            {
                "endpoint": stat.endpoint,
                "count": stat.count,
                "avg_duration_ms": round(stat.avg_duration, 2) if stat.avg_duration else 0
            }
            for stat in endpoint_stats
        ]
    }

@app.get("/admin/logs")
def get_admin_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent AI logs"""
    logs = db.query(AILog).order_by(AILog.created_at.desc()).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "endpoint": log.endpoint,
                "duration_ms": log.duration_ms,
                "error": log.error,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    }

@app.get("/admin/users")
def get_admin_users(db: Session = Depends(get_db)):
    """Get all users with usage statistics"""
    users = db.query(User).all()
    
    result = []
    for user in users:
        log_count = db.query(AILog).filter(AILog.user_id == user.id).count()
        rec_count = db.query(Recommendation).filter(Recommendation.user_id == user.id).count()
        
        result.append({
            "id": str(user.id),
            "email": user.email,
            "clerk_user_id": user.clerk_user_id,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat(),
            "total_logs": log_count,
            "total_recommendations": rec_count
        })
    
    return {"users": result}

@app.get("/admin/recommendations")
def get_admin_recommendations(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent recommendations"""
    recommendations = db.query(Recommendation).order_by(
        Recommendation.created_at.desc()
    ).limit(limit).all()
    
    return {
        "recommendations": [
            {
                "id": str(rec.id),
                "user_id": str(rec.user_id) if rec.user_id else None,
                "recommendation_text": rec.recommendation_text[:200] + "..." if len(rec.recommendation_text) > 200 else rec.recommendation_text,
                "tasks_count": rec.tasks_count,
                "created_at": rec.created_at.isoformat()
            }
            for rec in recommendations
        ]
    }
