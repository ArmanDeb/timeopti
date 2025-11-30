from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.core.utils import calculate_cost
from app.core.exceptions import TimeOptiException, CalendarError, OptimizationError
from app.services.ai_service import AIService
from app.services.matching_service import TaskMatcher
from app.services.google_calendar_service import GoogleCalendarService
from app.services.free_time_service import calculate_free_slots
from app.schemas.validators import OptimizationValidator
from app.schemas.optimization import (
    SmartOptimizeRequest, 
    NaturalOptimizeRequest, 
    GapRequest, 
    PriorityRequest, 
    AgendaRequest, 
    AnalyzeRequest
)
from app.models.all_models import User, AILog
import time
from datetime import datetime, timedelta

router = APIRouter()

ai_service = AIService()
task_matcher = TaskMatcher()
gcal_service = GoogleCalendarService()

# Helper function (duplicated for now)
def get_or_create_user(clerk_user_id: str, email: str, db: Session) -> User:
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if not user:
        email = email or f"{clerk_user_id}@noemail.com"
        user = User(clerk_user_id=clerk_user_id, email=email)
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
            if not user:
                raise e
    return user

@router.post("/smart-optimize")
def smart_optimize(request: SmartOptimizeRequest, db: Session = Depends(get_db)):
    """Smart task optimization using calendar integration and matching algorithm."""
    start_time = time.time()
    error = None
    result = None
    
    try:
        request_dict = request.model_dump()
        OptimizationValidator.validate_optimization_request(request_dict)
        
        try:
            if request.calendar_tokens:
                events = gcal_service.get_today_events(request.calendar_tokens)
            elif request.events:
                events = request.events
            else:
                events = []
        except Exception as e:
            raise CalendarError(f"Failed to fetch calendar events: {str(e)}")
        
        try:
            gaps = ai_service.analyze_calendar_gaps(events, request.start_window, request.end_window)
        except Exception as e:
            raise OptimizationError(f"Failed to analyze calendar gaps: {str(e)}")
        
        try:
            schedule = task_matcher.match_tasks_to_gaps(request.tasks, gaps)
        except Exception as e:
            raise OptimizationError(f"Failed to match tasks to gaps: {str(e)}")
        
        result = {
            "schedule": schedule.model_dump(),
            "gaps_found": [g.model_dump() for g in gaps],
            "events": [e.model_dump() for e in events]
        }
        if not schedule.success:
            result["warning"] = "Some tasks could not be scheduled."
        
        return result
        
    except TimeOptiException as e:
        error = e.message
        raise e
    except Exception as e:
        error = str(e)
        raise HTTPException(status_code=500, detail=error)
    
    finally:
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

@router.post("/smart-optimize-natural")
def smart_optimize_natural(request: NaturalOptimizeRequest, db: Session = Depends(get_db)):
    """Smart optimization from natural language input."""
    start_time = time.time()
    error = None
    result = None
    
    try:
        detected_scope, target_date = ai_service.detect_scope_from_input(request.natural_input)
        
        usage_data = {}
        try:
            parsed_tasks, parse_usage = ai_service.parse_natural_language_to_tasks(
                request.natural_input,
                detected_scope
            )
            usage_data["parse"] = parse_usage
        except Exception as e:
            raise OptimizationError(f"Failed to parse natural language: {str(e)}")
        
        events = []
        if hasattr(request, 'events') and request.events:
            events = request.events
        
        try:
            gaps = ai_service.analyze_calendar_gaps(events, request.start_window, request.end_window)
        except Exception as e:
            raise OptimizationError(f"Failed to analyze calendar gaps: {str(e)}")
        
        try:
            schedule = task_matcher.match_tasks_to_gaps(parsed_tasks, gaps)
        except Exception as e:
            raise OptimizationError(f"Failed to match tasks to gaps: {str(e)}")
        
        result = {
            "schedule": schedule.model_dump(),
            "gaps_found": [g.model_dump() for g in gaps],
            "events": [e.model_dump() for e in events],
            "parsed_tasks": [t.model_dump() for t in parsed_tasks],
            "usage": usage_data
        }
        
        return result
        
    except TimeOptiException as e:
        error = e.message
        raise e
    except Exception as e:
        error = str(e)
        raise HTTPException(status_code=500, detail=error)
    
    finally:
        duration_ms = int((time.time() - start_time) * 1000)
        
        total_tokens = 0
        total_cost = 0.0
        model_used = "gpt-4o"
        
        if result and "usage" in result:
            for key, usage in result["usage"].items():
                if usage:
                    total_tokens += usage.get("total_tokens", 0)
                    total_cost += calculate_cost(
                        usage.get("model", "gpt-4o"),
                        usage.get("prompt_tokens", 0),
                        usage.get("completion_tokens", 0)
                    )
                    model_used = usage.get("model", model_used)

        log = AILog(
            user_id=None,
            endpoint="/smart-optimize-natural",
            request_data=request.model_dump(),
            response_data=result,
            duration_ms=duration_ms,
            error=error,
            tokens_used=total_tokens,
            model=model_used,
            cost=total_cost
        )
        db.add(log)
        db.commit()

@router.post("/optimize")
def optimize_agenda(request: AgendaRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    error = None
    result = None
    
    try:
        result, usage = ai_service.optimize_agenda(request)
        return {"optimized_agenda": result, "usage": usage}
    except Exception as e:
        error = str(e)
        raise HTTPException(status_code=500, detail=error)
    finally:
        duration_ms = int((time.time() - start_time) * 1000)
        
        tokens_used = 0
        cost = 0.0
        model = None
        
        if 'usage' in locals() and usage:
            tokens_used = usage.get("total_tokens", 0)
            model = usage.get("model")
            cost = calculate_cost(
                model,
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0)
            )
            
        log = AILog(
            user_id=None,
            endpoint="/optimize",
            request_data=request.model_dump(),
            response_data={"result": result} if result else None,
            duration_ms=duration_ms,
            error=error,
            tokens_used=tokens_used,
            model=model,
            cost=cost
        )
        db.add(log)
        db.commit()

@router.post("/analyze/gaps")
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

@router.post("/analyze/priorities")
def analyze_priorities(request: PriorityRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    error = None
    result = None
    
    try:
        priorities, usage = ai_service.get_priority_tasks(request.tasks)
        result = {"priorities": priorities, "usage": usage}
        return result
    except Exception as e:
        error = str(e)
        raise HTTPException(status_code=500, detail=error)
    finally:
        duration_ms = int((time.time() - start_time) * 1000)
        
        tokens_used = 0
        cost = 0.0
        model = None
        
        if 'usage' in locals() and usage:
            tokens_used = usage.get("total_tokens", 0)
            model = usage.get("model")
            cost = calculate_cost(
                model,
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0)
            )

        log = AILog(
            user_id=None,
            endpoint="/analyze/priorities",
            request_data=request.model_dump(),
            response_data=result,
            duration_ms=duration_ms,
            error=error,
            tokens_used=tokens_used,
            model=model,
            cost=cost
        )
        db.add(log)
        db.commit()

@router.post("/analyze")
def analyze_schedule(request: AnalyzeRequest, user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Analyze natural language input and propose a schedule based on free time.
    """
    start_time = time.time()
    error = None
    result = None
    
    try:
        clerk_user_id = user_data.get("sub")
        user = get_or_create_user(clerk_user_id, user_data.get("email"), db)
        
        if request.target_date:
            try:
                target_date = datetime.strptime(request.target_date, "%Y-%m-%d")
            except ValueError:
                target_date = datetime.now()
        else:
            target_date = datetime.now()
        target_date_str = target_date.strftime("%Y-%m-%d")
            
        events = []
        warning = None
        
        if request.tokens:
            try:
                start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = start_of_day + timedelta(days=1)
                events_list = gcal_service.get_events(request.tokens, start_of_day, end_of_day)
                events = [e.model_dump() for e in events_list]
            except Exception as e:
                warning = f"Could not fetch calendar events: {str(e)}"
                print(f"Warning: {warning}")
        else:
            warning = "No calendar tokens provided. Planning without existing events."
            
        # Add existing scheduled tasks to events to prevent overlap
        if request.existing_tasks:
            print(f"Adding {len(request.existing_tasks)} existing tasks to busy slots")
            for task in request.existing_tasks:
                # Task from frontend has assigned_start_time (HH:MM) and assigned_end_time (HH:MM)
                # We need to convert to ISO format or whatever calculate_free_slots expects
                # calculate_free_slots handles Event objects or dicts with start_time/end_time
                
                # Construct full ISO string for the target date
                start_iso = f"{target_date_str}T{task.get('assigned_start_time')}:00"
                end_iso = f"{target_date_str}T{task.get('assigned_end_time')}:00"
                
                events.append({
                    "title": task.get('task_name', 'Existing Task'),
                    "start_time": start_iso,
                    "end_time": end_iso,
                    "description": "Already scheduled task"
                })
        
        free_slots = calculate_free_slots(
            events, 
            target_date, 
            sleep_start=request.sleep_start, 
            sleep_end=request.sleep_end, 
            min_slot_minutes=15,
            start_from_now=request.start_from_now
        )
        
        proposals_data, usage = ai_service.llm_assign_tasks_to_slots(
            request.natural_input,
            free_slots,
            target_date_str,
            request.timezone
        )
        
        free_slots_response = [s.model_dump() if hasattr(s, 'model_dump') else s.dict() if hasattr(s, 'dict') else {"id": s.id, "start": s.start, "end": s.end, "duration_minutes": s.duration_minutes} for s in free_slots]
        
        result = {
            "proposals": proposals_data.get("proposals", []),
            "free_slots": free_slots_response,
            "events": events,
            "target_date": target_date_str,
            "warning": warning,
            "usage": usage
        }
        
        return result

    except Exception as e:
        error = str(e)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error)
    finally:
        try:
            duration_ms = int((time.time() - start_time) * 1000)
            user_id = user.id if 'user' in locals() and user else None
            
            tokens_used = 0
            cost = 0.0
            model = None
            
            if 'usage' in locals() and usage:
                tokens_used = usage.get("total_tokens", 0)
                model = usage.get("model")
                cost = calculate_cost(
                    model,
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0)
                )
            
            log = AILog(
                user_id=user_id,
                endpoint="/analyze",
                request_data=request.model_dump() if 'request' in locals() else {},
                response_data=result,
                duration_ms=duration_ms,
                error=error,
                tokens_used=tokens_used,
                model=model,
                cost=cost
            )
            db.add(log)
            db.commit()
        except Exception as log_error:
            db.rollback()
            print(f"Failed to log request: {log_error}")
