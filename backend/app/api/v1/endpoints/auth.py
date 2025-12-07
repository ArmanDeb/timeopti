from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict

from app.db.session import get_db
from app.core.security import get_current_user
from app.core.encryption import encrypt_tokens, decrypt_tokens
from app.models.all_models import User

router = APIRouter()


class CalendarTokensRequest(BaseModel):
    """Request body for storing calendar tokens."""
    tokens: Dict


def get_or_create_user(clerk_user_id: str, email: Optional[str], db: Session) -> User:
    """Get existing user or create a new one."""
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


@router.get("/protected")
def read_protected(user: dict = Depends(get_current_user)):
    return {"message": "You are authenticated", "user_id": user.get("sub")}


@router.post("/calendar-tokens")
def store_calendar_tokens(
    request: CalendarTokensRequest,
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Store encrypted calendar tokens for the authenticated user.
    Tokens are encrypted before being stored in the database.
    """
    clerk_user_id = user_data.get("sub")
    user = get_or_create_user(clerk_user_id, user_data.get("email"), db)
    
    try:
        # Encrypt tokens before storage
        encrypted = encrypt_tokens(request.tokens)
        user.calendar_tokens = encrypted
        db.commit()
        
        return {"success": True, "message": "Calendar tokens stored securely"}
    except ValueError as e:
        # ENCRYPTION_KEY not set
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to store tokens: {str(e)}")


@router.get("/calendar-tokens")
def get_calendar_tokens(
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve decrypted calendar tokens for the authenticated user.
    Returns the tokens or null if not connected.
    """
    clerk_user_id = user_data.get("sub")
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    
    if not user or not user.calendar_tokens:
        return {"connected": False, "tokens": None}
    
    try:
        tokens = decrypt_tokens(user.calendar_tokens)
        if tokens:
            return {"connected": True, "tokens": tokens}
        else:
            return {"connected": False, "tokens": None}
    except Exception as e:
        print(f"Error decrypting tokens: {e}")
        return {"connected": False, "tokens": None}


@router.delete("/calendar-tokens")
def delete_calendar_tokens(
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove calendar tokens for the authenticated user (disconnect calendar).
    """
    clerk_user_id = user_data.get("sub")
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    
    if user:
        user.calendar_tokens = None
        db.commit()
    
    return {"success": True, "message": "Calendar disconnected"}
