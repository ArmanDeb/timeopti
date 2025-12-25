import os
import json
from google.oauth2.credentials import Credentials
from google.auth.credentials import Credentials as BaseCredentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from app.schemas.common import Event
from app.core.exceptions import AuthenticationError, CalendarError


class StaticCredentials(BaseCredentials):
    """
    Credentials class for static access tokens (like from Clerk).
    These tokens don't support refresh - Clerk handles refresh on their side.
    """
    
    def __init__(self, token):
        super().__init__()
        self.token = token
    
    @property
    def expired(self):
        # Never report as expired - Clerk manages token lifecycle
        return False
    
    @property
    def valid(self):
        # Always valid if we have a token
        return self.token is not None
    
    def refresh(self, request):
        # Clerk tokens can't be refreshed by us - just pass (don't raise)
        # The token is assumed to be valid since Clerk manages its lifecycle
        pass
    
    def apply(self, headers, token=None):
        # Apply the access token to the request headers
        headers['authorization'] = f'Bearer {token or self.token}'
    
    def before_request(self, request, method, url, headers):
        # Override to skip refresh logic entirely
        # Just apply the token to headers without any refresh attempt
        self.apply(headers, token=self.token)

class GoogleCalendarService:
    """
    Service for interacting with Google Calendar API.
    Handles OAuth flow and fetching calendar events.
    """
    
    # Updated scope to allow writing events
    SCOPES = ['https://www.googleapis.com/auth/calendar.events']
    
    def __init__(self):
        # Allow OAuth scope to change (e.g. if Google adds extra scopes)
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
        
        self.credentials_path = os.getenv('GOOGLE_CALENDAR_CREDENTIALS_PATH', 'google_credentials.json')
        self.credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        
        # Check if we have credentials either as file or env var
        self.credentials_available = os.path.exists(self.credentials_path) or bool(self.credentials_json)
        
        if not self.credentials_available:
            print(f"Warning: Google Calendar credentials not found at {self.credentials_path} and GOOGLE_CREDENTIALS_JSON not set.")
            print("Google Calendar features will not be available until credentials are configured.")
        else:
            print("Google Calendar Service initialized with credentials.")

    def _check_credentials(self):
        """Check if credentials are available before operations"""
        if not self.credentials_available:
            raise CalendarError(
                f"Google Calendar credentials not found. "
                f"Please set GOOGLE_CREDENTIALS_JSON env var or create '{self.credentials_path}'."
            )
    
    def _get_flow(self, redirect_uri: str):
        """Helper to create Flow from file or env var"""
        if self.credentials_json:
            try:
                config = json.loads(self.credentials_json)
                return Flow.from_client_config(
                    config,
                    scopes=self.SCOPES,
                    redirect_uri=redirect_uri
                )
            except json.JSONDecodeError as e:
                raise CalendarError(f"Invalid JSON in GOOGLE_CREDENTIALS_JSON: {str(e)}")
        else:
            return Flow.from_client_secrets_file(
                self.credentials_path,
                scopes=self.SCOPES,
                redirect_uri=redirect_uri
            )

    def get_authorization_url(self, redirect_uri: str) -> str:
        """
        Get the Google OAuth authorization URL.
        User should be redirected to this URL to grant calendar access.
        """
        self._check_credentials()
        
        flow = self._get_flow(redirect_uri)
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent to ensure we get a refresh token
        )
        
        return authorization_url
    
    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> dict:
        """
        Exchange authorization code for access and refresh tokens.
        Returns token dictionary to be stored for the user.
        """
        self._check_credentials()
        
        flow = self._get_flow(redirect_uri)
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        if not credentials.refresh_token:
            print("⚠️ [exchange_code_for_tokens] No refresh_token received from Google! Token expiry will cause issues.")
        else:
            print("✅ [exchange_code_for_tokens] Refresh token received.")
            
        token_data = {
            'token': credentials.token,  # For frontend compatibility
            'access_token': credentials.token,  # For Google API
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        print(f"[exchange_code_for_tokens] Returning tokens. Access token length: {len(credentials.token) if credentials.token else 0}")
        return token_data
    
    def _get_calendar_service(self, user_tokens: dict):
        """Helper to build the Calendar service from tokens."""
        try:
            # Get the actual access token
            token = user_tokens.get('token') or user_tokens.get('access_token', '')
            access_token = user_tokens.get('access_token') or user_tokens.get('token', '')
            
            # Use the access_token for the token field (Google OAuth format)
            actual_token = access_token or token
            
            # Check for demo/mock tokens
            if not actual_token or len(actual_token) < 10 or actual_token.startswith('demo_') or actual_token.startswith('mock_'):
                print(f"[_get_calendar_service] Invalid token detected. Length: {len(actual_token) if actual_token else 0}")
                raise AuthenticationError(
                    f"Invalid or expired calendar tokens detected. Please reconnect your Google Calendar."
                )
            
            # Check if this is a Clerk-sourced token
            is_clerk_token = user_tokens.get('source') == 'clerk'
            
            if is_clerk_token:
                # Clerk tokens: use access token directly, no refresh capability
                # Clerk manages token refresh on their side
                print("[_get_calendar_service] Using Clerk-sourced token (no refresh)")
                
                # Use StaticCredentials which won't try to refresh
                credentials = StaticCredentials(token=actual_token)
                
                return build('calendar', 'v3', credentials=credentials)
            
            # Standard OAuth flow tokens (from our own OAuth)
            # Validate required fields for refresh
            if not user_tokens.get('client_id') or not user_tokens.get('client_secret'):
                print("⚠️ [_get_calendar_service] Missing client_id or client_secret in tokens! Token refresh will fail.")
            
            if not user_tokens.get('refresh_token'):
                print("⚠️ [_get_calendar_service] Missing refresh_token! Token refresh will fail if access token is expired.")

            # Create credentials from stored tokens
            try:
                # Ensure scopes is a list
                scopes = user_tokens.get('scopes', [])
                if isinstance(scopes, str):
                    scopes = [scopes]
                
                # Construct info dict for from_authorized_user_info
                info = {
                    'token': actual_token,
                    'refresh_token': user_tokens.get('refresh_token'),
                    'token_uri': user_tokens.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    'client_id': user_tokens.get('client_id'),
                    'client_secret': user_tokens.get('client_secret'),
                    'scopes': scopes
                }
                
                credentials = Credentials.from_authorized_user_info(info, scopes=scopes)
            except Exception as cred_err:
                print(f"Error using from_authorized_user_info: {cred_err}")
                # Fallback to manual creation
                token_dict = {
                    'token': actual_token,
                    'refresh_token': user_tokens.get('refresh_token'),
                    'token_uri': user_tokens.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    'client_id': user_tokens.get('client_id'),
                    'client_secret': user_tokens.get('client_secret'),
                    'scopes': scopes
                }
                credentials = Credentials(**token_dict)
            
            # Refresh if expired
            if credentials.expired and credentials.refresh_token:
                print("[_get_calendar_service] Token expired, refreshing...")
                credentials.refresh(Request())
                print("[_get_calendar_service] Token refreshed successfully.")
                
            return build('calendar', 'v3', credentials=credentials)
            
        except AuthenticationError:
            raise
        except RefreshError as e:
            print(f"Token refresh failed: {e}")
            raise AuthenticationError("Token expired or invalid. Please reconnect your calendar.")
        except Exception as e:
            print(f"Error creating credentials: {e}")
            raise CalendarError(f"Failed to initialize calendar credentials: {str(e)}")


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
        try:
            service = self._get_calendar_service(user_tokens)
            
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
            print(f"[get_events] Google API returned {len(events)} raw events")
            
            # Convert to our Event format
            converted = self._convert_google_events(events)
            print(f"[get_events] Converted to {len(converted)} events (all-day events filtered out)")
            return converted
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            print(f'Error details: {error.resp.status} - {error.content}')
            
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
            print(f"Unexpected error in get_events: {str(e)}")
            import traceback
            traceback.print_exc()
            raise CalendarError(f"Unexpected error fetching events: {str(e)}")
    
    def _convert_google_events(self, google_events: list) -> List[Event]:
        """Convert Google Calendar events to our Event format."""
        converted_events = []
        
        for event in google_events:
            event_title = event.get('summary', 'Untitled')
            
            # Skip all-day events
            if 'dateTime' not in event.get('start', {}):
                print(f"[_convert_google_events] Skipping all-day event: {event_title}")
                continue
            
            start = event['start'].get('dateTime')
            end = event['end'].get('dateTime')
            
            if start and end:
                print(f"[_convert_google_events] Converting event: {event_title} ({start} to {end})")
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

    def create_event(self, user_tokens: dict, summary: str, start_time: str, end_time: str, description: str = None, timezone: str = 'UTC'):
        """
        Create a new event in the primary calendar.
        start_time and end_time should be ISO 8601 strings.
        """
        self._check_credentials()
        
        service = self._get_calendar_service(user_tokens)
        
        event_body = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_time,
                'timeZone': timezone,
            },
        }
        
        try:
            event = service.events().insert(calendarId='primary', body=event_body).execute()
            return event
        except HttpError as e:
            if e.resp.status == 401:
                raise AuthenticationError("Google Calendar token expired or invalid")
            raise CalendarError(f"Failed to create event: {e}")
