"""
Endpoint to fetch Google OAuth tokens from Clerk and store them for calendar access.

This enables single-step authentication: when users sign in with Google through Clerk,
we can retrieve their Google OAuth tokens (with calendar scopes) and use them for
calendar API access, eliminating the need for a separate "Connect Calendar" step.

Uses requests library directly instead of Clerk SDK to avoid httpx version conflicts.
"""
import os
import requests
from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.core.encryption import encrypt_tokens
from app.models.all_models import User

router = APIRouter()

CLERK_API_URL = "https://api.clerk.com/v1"


def get_clerk_secret_key():
    """Get Clerk secret key from environment."""
    secret_key = os.getenv("CLERK_SECRET_KEY")
    if not secret_key:
        raise ValueError("CLERK_SECRET_KEY environment variable is not set")
    return secret_key


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


def fetch_google_oauth_from_clerk(user_id: str) -> Optional[Dict]:
    """
    Fetch Google OAuth access token from Clerk API.
    
    Uses Clerk's Backend API: GET /users/{user_id}/oauth_access_tokens/oauth_google
    """
    try:
        secret_key = get_clerk_secret_key()
        
        response = requests.get(
            f"{CLERK_API_URL}/users/{user_id}/oauth_access_tokens/oauth_google",
            headers={
                "Authorization": f"Bearer {secret_key}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0]  # Return first token
        elif response.status_code == 404:
            print(f"[Clerk API] No Google OAuth token found for user {user_id}")
            return None
        else:
            print(f"[Clerk API] Error fetching token: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"[Clerk API] Exception: {e}")
        return None


@router.get("/google-token")
def fetch_google_token_from_clerk(
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch the user's Google OAuth token from Clerk and store it for calendar access.
    
    This endpoint:
    1. Gets the user's Google OAuth access token from Clerk's Backend API
    2. Encrypts and stores it in the user's calendar_tokens field
    3. Returns success/failure status
    
    This enables auto-connect for users who sign in with Google.
    """
    clerk_user_id = user_data.get("sub")
    
    if not clerk_user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token")
    
    try:
        # Fetch OAuth token from Clerk
        token_data = fetch_google_oauth_from_clerk(clerk_user_id)
        
        if not token_data:
            return {
                "success": False,
                "connected": False,
                "message": "No Google OAuth token found. User may not have signed in with Google."
            }
        
        access_token = token_data.get("token")
        if not access_token:
            return {
                "success": False,
                "connected": False,
                "message": "Google OAuth token is empty"
            }
        
        # Build tokens dict compatible with our calendar service
        scopes = token_data.get("scopes", [])
        tokens = {
            "token": access_token,
            "access_token": access_token,
            "refresh_token": None,  # Clerk manages refresh
            "token_uri": "https://oauth2.googleapis.com/token",
            "scopes": scopes,
            "source": "clerk"
        }
        
        # Store encrypted tokens in user's record
        user = get_or_create_user(clerk_user_id, user_data.get("email"), db)
        
        try:
            encrypted = encrypt_tokens(tokens)
            user.calendar_tokens = encrypted
            db.commit()
            print(f"[fetch_google_token_from_clerk] Tokens stored for user {clerk_user_id}")
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
        
        has_calendar_scopes = any("calendar" in s.lower() for s in scopes)
        
        return {
            "success": True,
            "connected": True,
            "message": "Google Calendar connected automatically via Clerk",
            "has_calendar_scopes": has_calendar_scopes
        }
        
    except Exception as e:
        print(f"Error fetching Google token from Clerk: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "connected": False,
            "message": f"Could not fetch Google token: {str(e)}"
        }


@router.get("/check-google-connection")
def check_google_connection(
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if the user has a valid Google connection through Clerk
    and whether calendar is already connected.
    """
    clerk_user_id = user_data.get("sub")
    
    # Check if user already has calendar tokens stored
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    
    if user and user.calendar_tokens:
        return {
            "has_google_sso": True,
            "calendar_connected": True,
            "needs_connect": False
        }
    
    # Check if user has Google OAuth through Clerk
    try:
        token_data = fetch_google_oauth_from_clerk(clerk_user_id)
        has_google = token_data is not None
        
        return {
            "has_google_sso": has_google,
            "calendar_connected": False,
            "needs_connect": not has_google
        }
    except Exception as e:
        print(f"Error checking Google connection: {e}")
        return {
            "has_google_sso": False,
            "calendar_connected": False,
            "needs_connect": True
        }
