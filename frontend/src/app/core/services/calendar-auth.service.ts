import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { CalendarService } from './calendar.service';
import { environment } from '../../../environments/environment';

interface TokenResponse {
  connected: boolean;
  tokens: any;
}

@Injectable({
  providedIn: 'root'
})
export class CalendarAuthService {
  connected = signal<boolean>(false);
  private apiUrl = environment.apiUrl;
  private cachedTokens: any = null;

  constructor(
    private calendarService: CalendarService,
    private http: HttpClient
  ) {
    // Check initial status
    this.checkConnectionStatus();
  }

  async checkConnectionStatus() {
    // First check localStorage flag for quick UI update
    const hasConnectedFlag = localStorage.getItem('calendar_connected') === 'true';

    if (!hasConnectedFlag) {
      this.connected.set(false);
      this.cachedTokens = null;
      return;
    }

    // Verify with backend
    try {
      const response = await firstValueFrom(
        this.http.get<TokenResponse>(`${this.apiUrl}/auth/calendar-tokens`)
      );

      if (response.connected && response.tokens) {
        this.connected.set(true);
        this.cachedTokens = response.tokens;
      } else {
        this.connected.set(false);
        this.cachedTokens = null;
        localStorage.removeItem('calendar_connected');
      }
    } catch (e) {
      console.error('Failed to check calendar connection:', e);
      // Keep localStorage flag for offline/unauthenticated scenarios
      this.connected.set(hasConnectedFlag);
    }
  }

  connect() {
    const redirectUri = `${window.location.origin}/app/dashboard`;
    console.log('🔵 [CONNECT] Starting Google Calendar OAuth flow');
    console.log('🔵 [CONNECT] Redirect URI:', redirectUri);

    this.calendarService.getAuthUrl(redirectUri).subscribe({
      next: (res) => {
        console.log('✅ [CONNECT] Auth URL received from backend');
        console.log('🔵 [CONNECT] Redirecting to Google OAuth page...');
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
        console.log('✅ [AUTH] Tokens received and stored in backend');

        // Cache tokens locally for immediate use
        this.cachedTokens = res.tokens;

        // Set localStorage flag for quick UI status (tokens are in DB, not localStorage)
        localStorage.setItem('calendar_connected', 'true');
        this.connected.set(true);

        console.log('✅ [AUTH] Connection complete, redirecting to dashboard...');

        // Redirect to dashboard without query params
        window.location.replace('/app/dashboard');
      },
      error: (err) => {
        console.error('❌ [AUTH] Failed to exchange token', err);

        // Clear connection status
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

  async disconnect() {
    this.connected.set(false);
    this.cachedTokens = null;
    localStorage.removeItem('calendar_connected');

    // Also clear from backend
    try {
      await firstValueFrom(
        this.http.delete(`${this.apiUrl}/auth/calendar-tokens`)
      );
      console.log('✅ [AUTH] Tokens deleted from backend');
    } catch (e) {
      console.error('Failed to delete tokens from backend:', e);
    }
  }

  /**
   * Get calendar tokens. Fetches from backend if not cached.
   * Returns null if not connected.
   */
  async getTokens(): Promise<any> {
    // Return cached tokens if available
    if (this.cachedTokens) {
      return this.cachedTokens;
    }

    // Fetch from backend
    try {
      const response = await firstValueFrom(
        this.http.get<TokenResponse>(`${this.apiUrl}/auth/calendar-tokens`)
      );

      if (response.connected && response.tokens) {
        this.cachedTokens = response.tokens;
        return response.tokens;
      }
    } catch (e) {
      console.error('Failed to fetch tokens:', e);
    }

    return null;
  }

  /**
   * Synchronous getter for cached tokens (for backward compatibility).
   * May return null if tokens haven't been fetched yet.
   * Prefer using getTokens() async method.
   */
  getTokensSync(): any {
    return this.cachedTokens;
  }
}
