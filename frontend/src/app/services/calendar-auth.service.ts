import { Injectable, signal } from '@angular/core';
import { CalendarService } from './calendar.service'; // Existing service

@Injectable({
  providedIn: 'root'
})
export class CalendarAuthService {
  connected = signal<boolean>(false);

  constructor(private calendarService: CalendarService) {
    // Check initial status (mock for now or check local storage/user profile)
    this.checkConnectionStatus();
  }

  checkConnectionStatus() {
    // In a real app, check if user has tokens in DB
    const hasTokens = localStorage.getItem('calendar_connected') === 'true';
    this.connected.set(hasTokens);
  }

  connect() {
    const redirectUri = 'http://localhost:4200/app/dashboard';
    console.log('🔵 [CONNECT] Starting Google Calendar OAuth flow');
    console.log('🔵 [CONNECT] Redirect URI:', redirectUri);
    
    this.calendarService.getAuthUrl(redirectUri).subscribe({
      next: (res) => {
        console.log('✅ [CONNECT] Auth URL received from backend');
        console.log('🔵 [CONNECT] Full auth URL:', res.auth_url);
        console.log('🔵 [CONNECT] Redirecting to Google OAuth page...');
        console.log('⚠️ [CONNECT] IMPORTANT: After authorizing on Google, you should be redirected back to:', redirectUri + '?code=...');
        window.location.href = res.auth_url;
      },
      error: (err) => {
        console.error('❌ [CONNECT] Failed to get auth URL from backend:', err);
        console.log('⚠️ [CONNECT] Falling back to mock mode (demo data)');
        this.mockConnect();
      }
    });
  }

  exchangeCodeForTokens(code: string, redirectUri: string) {
    console.log('Exchanging code for tokens...');
    this.calendarService.exchangeToken(code, redirectUri).subscribe({
      next: (res) => {
        console.log('Tokens received:', res);
        // Store tokens in localStorage
        localStorage.setItem('calendar_tokens', JSON.stringify(res.tokens));
        localStorage.setItem('calendar_connected', 'true');
        this.connected.set(true);
        
        // Redirect to dashboard without query params
        window.location.replace('/app/dashboard');
      },
      error: (err) => {
        console.error('Failed to exchange token', err);
        // Fallback to mock for demo
        this.mockConnect();
        // Create mock tokens for testing
        const mockTokens = {
          token: 'demo_token',
          refresh_token: 'demo_refresh',
          token_uri: 'https://oauth2.googleapis.com/token',
          client_id: 'demo_client',
          client_secret: 'demo_secret',
          scopes: ['https://www.googleapis.com/auth/calendar.readonly']
        };
        localStorage.setItem('calendar_tokens', JSON.stringify(mockTokens));
        window.location.replace('/app/dashboard');
      }
    });
  }

  mockConnect() {
    this.connected.set(true);
    localStorage.setItem('calendar_connected', 'true');
  }

  disconnect() {
    this.connected.set(false);
    localStorage.removeItem('calendar_connected');
    localStorage.removeItem('calendar_tokens');
  }
}

