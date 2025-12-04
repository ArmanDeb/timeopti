from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.services.google_calendar_service import GoogleCalendarService
from app.schemas.calendar import (
    CalendarAuthRequest, 
    CalendarTokenRequest, 
    CalendarEventsRequest, 
    TodayEventsRequest
)
from app.schemas.optimization import CommitScheduleRequest
from app.models.all_models import User
from app.core.exceptions import TimeOptiException
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter()
gcal_service = GoogleCalendarService()

# Helper function (duplicated for now, should be in user service)
def get_or_create_user(clerk_user_id: str, email: Optional[str], db: Session) -> User:
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

@router.post("/calendar/auth-url")
def get_calendar_auth_url(request: CalendarAuthRequest):
    """Get Google Calendar OAuth authorization URL"""
    try:
        auth_url = gcal_service.get_authorization_url(request.redirect_uri)
        return {"auth_url": auth_url}
    except TimeOptiException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calendar/exchange-token")
def exchange_calendar_token(request: CalendarTokenRequest, user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Exchange OAuth code for tokens and store them"""
    try:
        tokens = gcal_service.exchange_code_for_tokens(request.code, request.redirect_uri)
        return {"success": True, "tokens": tokens}
    except TimeOptiException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        import traceback
        print(f"ERROR in exchange_calendar_token: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calendar/events")
def get_calendar_events(request: CalendarEventsRequest):
    """Fetch events from user's Google Calendar"""
    try:
        print(f"Received request: {request}")
        
        start_date_str = request.start_date.replace('Z', '+00:00') if request.start_date else None
        end_date_str = request.end_date.replace('Z', '+00:00') if request.end_date else None
        
        start = datetime.fromisoformat(start_date_str) if start_date_str else None
        end = datetime.fromisoformat(end_date_str) if end_date_str else None
        
        events = gcal_service.get_events(request.tokens, start, end)
        return {"events": [e.model_dump() for e in events]}
    except TimeOptiException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        import traceback
        print(f"ERROR in get_calendar_events: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/today")
def get_today_events(request: TodayEventsRequest, user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Fetch today's events from user's Google Calendar.
    Requires authentication and calendar tokens.
    """
    try:
        print(f"[/events/today] Received request with tokens: {bool(request.tokens)}")
        
        clerk_user_id = user_data.get("sub")
        # Ensure user exists
        get_or_create_user(clerk_user_id, user_data.get("email"), db)
        
        today = datetime.now()
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        events = gcal_service.get_events(request.tokens, start_of_day, end_of_day)
        return {"events": [e.model_dump() for e in events]}
        
    except TimeOptiException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/commit-schedule")
def commit_schedule(request: CommitScheduleRequest, db: Session = Depends(get_db)):
    """
    Commit the proposed schedule to Google Calendar.
    """
    success_count = 0
    errors = []
    
    for proposal in request.proposals:
        try:
            start_iso = f"{proposal.assigned_date}T{proposal.assigned_start_time}:00"
            end_iso = f"{proposal.assigned_date}T{proposal.assigned_end_time}:00"
            
            description = f"Scheduled via TimeOpti.\nReasoning: {proposal.reasoning}"
            
            gcal_service.create_event(
                request.tokens,
                proposal.task_name,
                start_iso,
                end_iso,
                description,
                timezone=request.timezone
            )
            success_count += 1
        except Exception as e:
            errors.append(f"Failed to create {proposal.task_name}: {str(e)}")
    
    return {
        "success": len(errors) == 0,
        "committed_count": success_count,
        "errors": errors
    }
