import { Component, effect, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ViewStateService } from '../services/view-state.service';
import { CalendarAuthService } from '../services/calendar-auth.service';
import { OptimizerComponent } from '../optimizer/optimizer';
import { DayViewComponent } from '../day-view/day-view.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, OptimizerComponent, DayViewComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit {
  // Local input
  input: string = '';
  
  // View Toggle (Timeline vs Calendar vs Week)
  showCalendarGrid = false;
  
  // Task panel toggle
  showTaskPanel = false;

  constructor(
    public viewState: ViewStateService,
    public calendarAuth: CalendarAuthService,
    private route: ActivatedRoute
  ) {
    // Reactively update state when connection status changes
    effect(() => {
      const isConnected = this.calendarAuth.connected();
      console.log('🔄 [DASHBOARD] Connection status changed:', isConnected);
      
      if (isConnected) {
        // Only set to input if we're not already in results
        if (this.viewState.state() !== 'results') {
          this.viewState.setState('input');
        }
      } else {
        // If disconnected, go back to onboarding
        console.log('🔴 [DASHBOARD] Disconnected, forcing onboarding state');
        this.viewState.setState('onboarding');
      }
    });
    
    // Set initial state based on calendar connection
    if (this.calendarAuth.connected()) {
      this.viewState.setState('input');
    } else {
      this.viewState.setState('onboarding');
    }
  }

  ngOnInit() {
    console.log('🟢 [DASHBOARD] Component initialized');
    console.log('🟢 [DASHBOARD] Current URL:', window.location.href);
    console.log('🟢 [DASHBOARD] Search params:', window.location.search);
    console.log('🟢 [DASHBOARD] Hash:', window.location.hash);
    
    // Force re-check of connection status to ensure it's up to date
    this.calendarAuth.checkConnectionStatus();
    console.log('🟢 [DASHBOARD] Calendar connected (after check):', this.calendarAuth.connected());
    
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

    // Ensure state is correct based on connection
    if (this.calendarAuth.connected()) {
      console.log('Calendar connected, ensuring input state');
      this.viewState.setState('input');
    } else {
       // If not connected, ensure we are in onboarding (unless we are already in results or something else, but initially onboarding)
       if (this.viewState.state() === 'input') {
           this.viewState.setState('onboarding');
       }
    }
  }

  handleOAuthCallback(code: string) {
    // Exchange code for tokens via backend
    this.calendarAuth.exchangeCodeForTokens(code, 'http://localhost:4200/app/dashboard');
  }

  connectCalendar() {
    this.calendarAuth.connect();
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
  
  toggleTaskPanel() {
    this.showTaskPanel = !this.showTaskPanel;
  }
}
