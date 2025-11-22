import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from services.ai_service import Event
from exceptions import AuthenticationError, CalendarError

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
        else:
            # Try to log client ID for debugging
            try:
                with open(self.credentials_path) as f:
                    creds = json.load(f)
                    client_id = creds.get('installed', {}).get('client_id') or creds.get('web', {}).get('client_id')
                    if client_id:
                        print(f"Google Calendar Service initialized with Client ID: {client_id[:15]}...")
            except Exception as e:
                print(f"Error reading credentials file: {e}")
    
    def _check_credentials(self):
        """Check if credentials are available before operations"""
        if not self.credentials_available:
            raise CalendarError(
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
            'token': credentials.token,  # For frontend compatibility
            'access_token': credentials.token,  # For Google API
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
        """
        # Handle mock tokens
        token = user_tokens.get('token', '')
        access_token = user_tokens.get('access_token', '')
        if (token and (token.startswith('mock_') or 'demo' in token)) or \
           (access_token and (access_token.startswith('mock_') or 'demo' in access_token)):
            print("Mock/Demo tokens detected, returning empty list to avoid API error")
            return []

        try:
            # Create credentials from stored tokens
            token_dict = {
                'token': access_token or token,
                'refresh_token': user_tokens.get('refresh_token'),
                'token_uri': user_tokens.get('token_uri'),
                'client_id': user_tokens.get('client_id'),
                'client_secret': user_tokens.get('client_secret'),
                'scopes': user_tokens.get('scopes', [])
            }
            
            credentials = Credentials(**token_dict)
            
            # Refresh if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
        except RefreshError as e:
            print(f"Token refresh failed: {e}")
            raise AuthenticationError("Token expired or invalid. Please reconnect your calendar.")
        except Exception as e:
            print(f"Error creating credentials: {e}")
            print(f"User tokens: {user_tokens}")
            raise CalendarError(f"Failed to initialize calendar credentials: {str(e)}")
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            
            # Default time range: now to 7 days from now
            if not start_date:
                start_date = datetime.now(timezone.utc)
            if not end_date:
                end_date = start_date + timedelta(days=7)
            
            # Format for API - ensure proper RFC3339 format
            if start_date.tzinfo:
                time_min = start_date.isoformat()
            else:
                time_min = start_date.isoformat() + 'Z'
                
            if end_date.tzinfo:
                time_max = end_date.isoformat()
            else:
                time_max = end_date.isoformat() + 'Z'
            
            print(f"Fetching events from {time_min} to {time_max}")
            
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
            
            # Handle 403 - API Not Enabled or Usage Limit
            if error.resp.status == 403 and 'accessNotConfigured' in str(error):
                 raise CalendarError(
                    "Google Calendar API is not enabled. Please enable it in Google Cloud Console "
                    "for this project: https://console.developers.google.com/apis/api/calendar-json.googleapis.com/overview"
                )
            
            if error.resp.status == 401:
                raise AuthenticationError("Calendar access revoked or expired. Please reconnect.")
                
            raise CalendarError(f"Failed to fetch calendar events: {error}")
        except Exception as e:
            raise CalendarError(f"Unexpected error fetching events: {str(e)}")
    
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
                # Use the full ISO string for the date, so the frontend can parse it correctly
                # Note: AIService.analyze_calendar_gaps might need adjustment if it expects HH:MM
                # But for the week view, we definitely need the full date.
                
                converted_events.append(Event(
                    title=event.get('summary', 'Busy'),
                    start_time=start, # Pass full ISO string
                    end_time=end      # Pass full ISO string
                ))
        
        return converted_events
    
    def get_today_events(self, user_tokens: dict) -> List[Event]:
        """Convenience method to get today's events."""
        now = datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        return self.get_events(user_tokens, start_of_day, end_of_day)
