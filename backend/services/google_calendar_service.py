import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from typing import List, Optional
from services.ai_service import Event

class GoogleCalendarService:
    """
    Service for interacting with Google Calendar API.
    Handles OAuth flow and fetching calendar events.
    """
    
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    
    def __init__(self):
        self.credentials_path = os.getenv('GOOGLE_CALENDAR_CREDENTIALS_PATH', 'google_credentials.json')
        self.credentials_available = os.path.exists(self.credentials_path)
        
        if not self.credentials_available:
            print(f"Warning: Google Calendar credentials not found at {self.credentials_path}")
            print("Google Calendar features will not be available until credentials are configured.")
    
    def _check_credentials(self):
        """Check if credentials are available before operations"""
        if not self.credentials_available:
            raise Exception(
                f"Google Calendar credentials not found. "
                f"Please create '{self.credentials_path}' with your OAuth credentials from Google Cloud Console."
            )
    
    def get_authorization_url(self, redirect_uri: str) -> str:
        """
        Get the Google OAuth authorization URL.
        User should be redirected to this URL to grant calendar access.
        """
        self._check_credentials()
        
        flow = Flow.from_client_secrets_file(
            self.credentials_path,
            scopes=self.SCOPES,
            redirect_uri=redirect_uri
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        return authorization_url
    
    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> dict:
        """
        Exchange authorization code for access and refresh tokens.
        Returns token dictionary to be stored for the user.
        """
        self._check_credentials()
        
        flow = Flow.from_client_secrets_file(
            self.credentials_path,
            scopes=self.SCOPES,
            redirect_uri=redirect_uri
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
    
    def get_events(
        self, 
        user_tokens: dict,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_results: int = 50
    ) -> List[Event]:
        """
        Fetch calendar events from user's Google Calendar.
        
        Args:
            user_tokens: User's stored OAuth tokens
            start_date: Start of time range (defaults to now)
            end_date: End of time range (defaults to 7 days from now)
            max_results: Maximum number of events to fetch
            
        Returns:
            List of Event objects
        """
        # Create credentials from stored tokens
        credentials = Credentials(**user_tokens)
        
        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            # Note: You should update the stored tokens with new access token
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            
            # Default time range: now to 7 days from now
            if not start_date:
                start_date = datetime.utcnow()
            if not end_date:
                end_date = start_date + timedelta(days=7)
            
            # Format for API
            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'
            
            # Fetch events
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Convert to our Event format
            return self._convert_google_events(events)
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise Exception(f"Failed to fetch calendar events: {error}")
    
    def _convert_google_events(self, google_events: list) -> List[Event]:
        """Convert Google Calendar events to our Event format."""
        converted_events = []
        
        for event in google_events:
            # Skip all-day events
            if 'dateTime' not in event.get('start', {}):
                continue
            
            start = event['start'].get('dateTime')
            end = event['end'].get('dateTime')
            
            if start and end:
                # Parse datetime and format as HH:MM
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                
                converted_events.append(Event(
                    title=event.get('summary', 'Busy'),
                    start_time=start_dt.strftime('%H:%M'),
                    end_time=end_dt.strftime('%H:%M')
                ))
        
        return converted_events
    
    def get_today_events(self, user_tokens: dict) -> List[Event]:
        """Convenience method to get today's events."""
        now = datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        return self.get_events(user_tokens, start_of_day, end_of_day)
