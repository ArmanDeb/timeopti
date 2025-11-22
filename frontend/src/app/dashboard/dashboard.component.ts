import { Component, effect, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ViewStateService } from '../services/view-state.service';
import { CalendarAuthService } from '../services/calendar-auth.service';
import { OptimizerComponent } from '../optimizer/optimizer';
import { WeekViewComponent } from '../week-view/week-view.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, OptimizerComponent, WeekViewComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit {
  // Local input
  input: string = '';
  
  // View Toggle (Timeline vs Calendar vs Week)
  showCalendarGrid = false;
  showWeekView = false;

  constructor(
    public viewState: ViewStateService,
    public calendarAuth: CalendarAuthService,
    private route: ActivatedRoute
  ) {
    // Initialize to input state if calendar is connected
    if (this.viewState.state() === 'onboarding' && this.calendarAuth.connected()) {
      this.viewState.setState('input');
    }
  }

  ngOnInit() {
    console.log('🟢 [DASHBOARD] Component initialized');
    console.log('🟢 [DASHBOARD] Current URL:', window.location.href);
    console.log('🟢 [DASHBOARD] Search params:', window.location.search);
    console.log('🟢 [DASHBOARD] Hash:', window.location.hash);
    console.log('🟢 [DASHBOARD] Calendar connected:', this.calendarAuth.connected());
    
    // Handle OAuth callback from query params
    this.route.queryParams.subscribe(params => {
      console.log('🟢 [DASHBOARD] Query params received:', params);
      console.log('🟢 [DASHBOARD] Params keys:', Object.keys(params));
      console.log('🟢 [DASHBOARD] Code param:', params['code']);
      console.log('🟢 [DASHBOARD] State param:', params['state']);
      console.log('🟢 [DASHBOARD] Scope param:', params['scope']);
      
      if (params['code']) {
        console.log('✅ [DASHBOARD] OAuth code found! Starting token exchange...');
        console.log('🔵 [DASHBOARD] Code value:', params['code']);
        this.handleOAuthCallback(params['code']);
        return;
      } else {
        console.log('⚠️ [DASHBOARD] No OAuth code in URL params');
      }
    });

    // Also check URL search params directly (in case Angular routing doesn't catch it)
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    if (code) {
      console.log('OAuth code received from URL search:', code);
      this.handleOAuthCallback(code);
      return;
    }

    // Show week view if calendar is connected
    if (this.calendarAuth.connected()) {
      console.log('Showing week view');
      this.showWeekView = true;
    }
  }

  handleOAuthCallback(code: string) {
    // Exchange code for tokens via backend
    this.calendarAuth.exchangeCodeForTokens(code, 'http://localhost:4200/app/dashboard');
  }

  connectCalendar() {
    this.calendarAuth.connect();
  }

  enableDemoMode() {
    // Enable demo mode with mock data
    this.calendarAuth.mockConnect();
    
    // Create mock tokens
    const mockTokens = {
      token: 'demo_token',
      refresh_token: 'demo_refresh',
      token_uri: 'https://oauth2.googleapis.com/token',
      client_id: 'demo_client',
      client_secret: 'demo_secret',
      scopes: ['https://www.googleapis.com/auth/calendar.readonly']
    };
    localStorage.setItem('calendar_tokens', JSON.stringify(mockTokens));
    
    // Show week view
    this.showWeekView = true;
  }

  analyze() {
    if (!this.input.trim()) return;
    this.viewState.inputText.set(this.input);
    this.viewState.simulateOptimization(this.input);
  }

  copyPlan() {
    const results = this.viewState.results();
    if (!results) return;
    const text = results.items.map(i => `${i.startTime} - ${i.endTime}: ${i.title}`).join('\n');
    navigator.clipboard.writeText(text).then(() => {
      alert('Plan copié !'); // Minimal feedback
    });
  }

  reset() {
    this.viewState.reset();
    this.input = '';
    this.showCalendarGrid = false;
  }

  toggleView() {
    this.showCalendarGrid = !this.showCalendarGrid;
  }

  // DEBUG: Force complete reset
  forceCompleteReset() {
    console.log('🔴 [DEBUG] === FORCING COMPLETE RESET ===');
    console.log('🔴 [DEBUG] Current localStorage:', { ...localStorage });
    
    // Clear everything
    localStorage.clear();
    console.log('🔴 [DEBUG] ✅ LocalStorage cleared');
    
    // Disconnect calendar
    this.calendarAuth.disconnect();
    console.log('🔴 [DEBUG] ✅ Calendar disconnected');
    
    // Reset view state
    this.viewState.reset();
    console.log('🔴 [DEBUG] ✅ View state reset');
    
    // Hide week view
    this.showWeekView = false;
    console.log('🔴 [DEBUG] ✅ Week view hidden');
    
    console.log('🔴 [DEBUG] === RELOADING PAGE ===');
    
    // Reload page
    setTimeout(() => {
      window.location.href = '/app/dashboard';
    }, 500);
  }
}
