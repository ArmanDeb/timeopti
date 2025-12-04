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
    // Check if user has valid tokens (not demo tokens)
    const tokensStr = localStorage.getItem('calendar_tokens');
    const hasConnectedFlag = localStorage.getItem('calendar_connected') === 'true';

    if (!tokensStr || !hasConnectedFlag) {
      this.connected.set(false);
      return;
    }

    try {
      const tokens = JSON.parse(tokensStr);
      const token = tokens.token || tokens.access_token || '';

      // Check if tokens are valid (not demo tokens)
      if (!token || token.length < 10 || token.startsWith('demo_') || token.startsWith('mock_')) {
        console.log(`⚠️ [AUTH] Invalid tokens detected (Length: ${token ? token.length : 0}), clearing...`);
        this.disconnect();
        this.connected.set(false);
        return;
      }

      this.connected.set(true);
    } catch (e) {
      console.error('Failed to parse tokens:', e);
      this.disconnect();
      this.connected.set(false);
    }
  }

  connect() {
    const redirectUri = `${window.location.origin}/app/dashboard`;
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
    console.log('🔄 [AUTH] Exchanging code for tokens...');
    this.calendarService.exchangeToken(code, redirectUri).subscribe({
      next: (res) => {
        console.log('✅ [AUTH] Tokens received successfully');
        const tokens = res.tokens as any; // Type assertion for flexibility
        console.log('🔐 [AUTH] Token length:', tokens?.token?.length || tokens?.access_token?.length || 0);

        // Store tokens in localStorage
        localStorage.setItem('calendar_tokens', JSON.stringify(res.tokens));
        localStorage.setItem('calendar_connected', 'true');
        this.connected.set(true);

        console.log('✅ [AUTH] Tokens stored, redirecting to dashboard...');

        // Redirect to dashboard without query params
        window.location.replace('/app/dashboard');
      },
      error: (err) => {
        console.error('❌ [AUTH] Failed to exchange token', err);

        // Clear any existing tokens
        this.disconnect();

        // Show error message to user
        const errorMessage = err.error?.detail || 'Failed to connect to Google Calendar. Please try again.';
        alert(`Erreur de connexion: ${errorMessage}`);

        // Stay on dashboard to allow retry
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

  getTokens() {
    const tokensStr = localStorage.getItem('calendar_tokens');
    if (!tokensStr) return null;

    try {
      return JSON.parse(tokensStr);
    } catch (e) {
      console.error('Failed to parse tokens:', e);
      return null;
    }
  }
}

