from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from auth import get_current_user
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.ai_service import AIService, AgendaRequest, Event, Task
from services.matching_service import TaskMatcher, ScheduleResult
from services.google_calendar_service import GoogleCalendarService
from services.free_time_service import calculate_free_slots
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
def get_or_create_user(clerk_user_id: str, email: Optional[str], db: Session) -> User:
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if not user:
        # Handle case where email might be None
        email = email or f"{clerk_user_id}@noemail.com"
        user = User(clerk_user_id=clerk_user_id, email=email)
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            # If commit fails, try to get existing user
            user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
            if not user:
                raise e
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
    except TimeOptiException as e:
        raise e
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
    except TimeOptiException as e:
        raise e
    except Exception as e:
        import traceback
        print(f"ERROR in exchange_calendar_token: {str(e)}")
        print(traceback.format_exc())
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
        import traceback
        
        print(f"Received request: {request}")
        print(f"Tokens: {request.tokens}")
        
        # Fix: Replace 'Z' with '+00:00' for Python's fromisoformat
        start_date_str = request.start_date.replace('Z', '+00:00') if request.start_date else None
        end_date_str = request.end_date.replace('Z', '+00:00') if request.end_date else None
        
        start = datetime.fromisoformat(start_date_str) if start_date_str else None
        end = datetime.fromisoformat(end_date_str) if end_date_str else None
        
        print(f"Date range: {start} to {end}")
        
        events = gcal_service.get_events(request.tokens, start, end)
        print(f"Got {len(events)} events")
        return {"events": [e.model_dump() for e in events]}
    except TimeOptiException as e:
        raise e
    except Exception as e:
        import traceback
        print(f"ERROR in get_calendar_events: {str(e)}")
        print(traceback.format_exc())
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
        
    except TimeOptiException as e:
        error = e.message
        raise e
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

class NaturalOptimizeRequest(BaseModel):
    natural_input: str
    scope: str  # "today" or "week"
    start_window: str = "09:00"
    end_window: str = "17:00"
    events: Optional[List[Event]] = None  # Optional calendar events

class GapRequest(BaseModel):
    events: List[Event]
    start_window: str
    end_window: str

@app.post("/smart-optimize-natural")
def smart_optimize_natural(request: NaturalOptimizeRequest, db: Session = Depends(get_db)):
    """
    Smart optimization from natural language input.
    
    Example: "today I want to study, have breakfast and visit friend"
    
    Workflow:
    1. Use AI to parse natural language into structured tasks
    2. Get calendar events for the specified scope (today or week)
    3. Analyze gaps and match tasks intelligently
    4. Return optimized schedule with context-aware placement
    """
    start_time = time.time()
    error = None
    result = None
    
    try:
        # Step 0: Auto-detect scope and target date from input
        detected_scope, target_date = ai_service.detect_scope_from_input(request.natural_input)
        scope_to_use = detected_scope
        
        # Step 1: Parse natural language into tasks using AI
        try:
            parsed_tasks = ai_service.parse_natural_language_to_tasks(
                request.natural_input,
                scope_to_use
            )
        except Exception as e:
            error_msg = f"Failed to parse natural language: {str(e)}"
            error = error_msg
            raise OptimizationError(error_msg)
        
        # Step 2: Get calendar events based on scope and target date
        # Try to get real calendar events if tokens are available in localStorage
        # For now, we'll use empty list as frontend will send events if available
        events = []
        
        # If manual events provided, use them
        if hasattr(request, 'events') and request.events:
            events = request.events
        
        # Step 3: Analyze gaps
        try:
            gaps = ai_service.analyze_calendar_gaps(events, request.start_window, request.end_window)
        except Exception as e:
            error_msg = f"Failed to analyze calendar gaps: {str(e)}"
            error = error_msg
            raise OptimizationError(error_msg)
        
        # Step 4: Match tasks to gaps with context awareness
        try:
            schedule = task_matcher.match_tasks_to_gaps(parsed_tasks, gaps)
        except Exception as e:
            error_msg = f"Failed to match tasks to gaps: {str(e)}"
            error = error_msg
            raise OptimizationError(error_msg)
        
        # Step 5: Generate result
        result = {
            "schedule": schedule.model_dump(),
            "gaps_found": [g.model_dump() for g in gaps],
            "events": [e.model_dump() for e in events],
            "parsed_tasks": [t.model_dump() for t in parsed_tasks]
        }
        
        return result
        
    except TimeOptiException as e:
        error = e.message
        raise e
    except Exception as e:
        error = str(e)
        raise HTTPException(status_code=500, detail=error)
    
    finally:
        # Log to database
        duration_ms = int((time.time() - start_time) * 1000)
        log = AILog(
            user_id=None,
            endpoint="/smart-optimize-natural",
            request_data=request.model_dump(),
            response_data=result,
            duration_ms=duration_ms,
            error=error
        )
        db.add(log)
        db.commit()

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

class AnalyzeRequest(BaseModel):
    natural_input: str
    tokens: Optional[dict] = None  # Calendar tokens for fetching events
    timezone: Optional[str] = "UTC"
    sleep_start: Optional[str] = "23:00"
    sleep_end: Optional[str] = "07:00"

class TodayEventsRequest(BaseModel):
    tokens: dict

@app.post("/events/today")
def get_today_events(request: TodayEventsRequest, user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Fetch today's events from user's Google Calendar.
    Requires authentication and calendar tokens.
    """
    try:
        from datetime import datetime, timedelta
        
        print(f"[/events/today] Received request with tokens: {bool(request.tokens)}")
        
        clerk_user_id = user_data.get("sub")
        user = get_or_create_user(clerk_user_id, user_data.get("email"), db)
        
        # Get today's date range
        today = datetime.now()
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        print(f"[/events/today] Fetching events from {start_of_day} to {end_of_day}")
        
        # Fetch events from Google Calendar
        events = gcal_service.get_events(request.tokens, start_of_day, end_of_day)
        
        print(f"[/events/today] Got {len(events)} events")
        
        return {"events": [e.model_dump() for e in events]}
        
    except TimeOptiException as e:
        print(f"[/events/today] TimeOptiException: {e}")
        raise e
    except Exception as e:
        print(f"[/events/today] Exception: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
def analyze_schedule(request: AnalyzeRequest, user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Analyze natural language input and propose a schedule based on free time.
    Server-side fetches events from Google Calendar if tokens provided.
    Always plans for TODAY only (MVP).
    """
    start_time = time.time()
    error = None
    result = None
    
    try:
        from datetime import datetime, timedelta
        
        clerk_user_id = user_data.get("sub")
        user = get_or_create_user(clerk_user_id, user_data.get("email"), db)
        
        # 1. Always use TODAY for MVP
        target_date = datetime.now()
        target_date_str = target_date.strftime("%Y-%m-%d")
            
        # 2. Fetch events from Google Calendar (server-side)
        events = []
        warning = None
        
        if request.tokens:
            try:
                # Fetch today's events
                start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = start_of_day + timedelta(days=1)
                events_list = gcal_service.get_events(request.tokens, start_of_day, end_of_day)
                events = [e.model_dump() for e in events_list]
            except Exception as e:
                warning = f"Could not fetch calendar events: {str(e)}"
                print(f"Warning: {warning}")
        else:
            warning = "No calendar tokens provided. Planning without existing events."
        
        # 3. Compute free slots
        free_slots = calculate_free_slots(
            events, 
            target_date, 
            sleep_start=request.sleep_start, 
            sleep_end=request.sleep_end, 
            min_slot_minutes=15
        )
        
        # 4. Call LLM to assign tasks to slots
        # Pass FreeSlot objects directly (they have .id, .start, .end, .duration_minutes attributes)
        proposals_data = ai_service.llm_assign_tasks_to_slots(
            request.natural_input,
            free_slots,  # Pass FreeSlot objects directly
            target_date_str,
            request.timezone
        )
        
        # 5. Return results
        # Convert FreeSlot objects to dicts for JSON response
        free_slots_response = [s.model_dump() if hasattr(s, 'model_dump') else s.dict() if hasattr(s, 'dict') else {"id": s.id, "start": s.start, "end": s.end, "duration_minutes": s.duration_minutes} for s in free_slots]
        
        result = {
            "proposals": proposals_data.get("proposals", []),
            "free_slots": free_slots_response,
            "events": events,
            "target_date": target_date_str,
            "warning": warning
        }
        
        return result

    except Exception as e:
        error = str(e)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error)
    finally:
        # Log to DB (only if we have a user and db is in good state)
        try:
            duration_ms = int((time.time() - start_time) * 1000)
            user_id = user.id if 'user' in locals() and user else None
            log = AILog(
                user_id=user_id,
                endpoint="/analyze",
                request_data=request.model_dump() if 'request' in locals() else {},
                response_data=result,
                duration_ms=duration_ms,
                error=error
            )
            db.add(log)
            db.commit()
        except Exception as log_error:
            # If logging fails, rollback and continue
            db.rollback()
            print(f"Failed to log request: {log_error}")

class ScheduledTaskProposal(BaseModel):
    task_name: str
    estimated_duration_minutes: int
    assigned_date: str
    assigned_start_time: str
    assigned_end_time: str
    reasoning: Optional[str] = None

class CommitScheduleRequest(BaseModel):
    tokens: dict
    proposals: List[ScheduledTaskProposal]
    timezone: str = "UTC"

@app.post("/commit-schedule")
def commit_schedule(request: CommitScheduleRequest, db: Session = Depends(get_db)):
    """
    Commit the proposed schedule to Google Calendar.
    """
    success_count = 0
    errors = []
    
    from datetime import datetime
    
    for proposal in request.proposals:
        try:
            # Construct ISO strings
            # We assume assigned_date is YYYY-MM-DD and times are HH:MM
            start_iso = f"{proposal.assigned_date}T{proposal.assigned_start_time}:00"
            end_iso = f"{proposal.assigned_date}T{proposal.assigned_end_time}:00"
            
            # Add timezone offset if provided? 
            # Google Calendar API is smart enough if we give it 'timeZone': '...' in body
            # But create_event expects ISO strings. 
            # We should probably let create_event handle it or pass timezone.
            # For now, simplistic construction.
            
            description = f"Scheduled via TimeOpti.\nReasoning: {proposal.reasoning}"
            
            gcal_service.create_event(
                request.tokens,
                proposal.task_name,
                start_iso,
                end_iso,
                description
            )
            success_count += 1
        except Exception as e:
            errors.append(f"Failed to create {proposal.task_name}: {str(e)}")
    
    return {
        "success": len(errors) == 0,
        "committed_count": success_count,
        "errors": errors
    }

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
