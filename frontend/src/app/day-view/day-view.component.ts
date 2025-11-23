import { Component, OnInit, OnDestroy, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CalendarService } from '../services/calendar.service';
import { CalendarAuthService } from '../services/calendar-auth.service';
import { ViewStateService } from '../services/view-state.service';
import { environment } from '../../environments/environment';

interface CalendarEvent {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
}

interface ProposedTask {
  task_name: string;
  estimated_duration_minutes: number;
  assigned_date: string;
  assigned_start_time: string;
  assigned_end_time: string;
  slot_id: string;
  reasoning: string;
}

@Component({
  selector: 'app-day-view',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './day-view.component.html',
  styleUrl: './day-view.component.css'
})
export class DayViewComponent implements OnInit, OnDestroy {
  @Input() showTaskButton = false;
  @Output() openTaskPanel = new EventEmitter<void>();

  events: CalendarEvent[] = [];
  proposedTasks: ProposedTask[] = [];
  isLoading = false;
  error: string | null = null;
  isAuthError = false;
  currentTime: string = '';
  private timeInterval: any;
  private refreshInterval: any;

  today: Date = new Date();
  todayStr: string = '';

  hours: string[] = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`);

  constructor(
    private calendarService: CalendarService,
    public calendarAuth: CalendarAuthService,
    public viewState: ViewStateService
  ) {
    if (!environment.production && typeof window !== 'undefined') {
      (window as any).__timeoptiViewState = this.viewState;
    }
  }

  ngOnInit() {
    this.todayStr = this.today.toLocaleDateString('fr-FR', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });

    if (this.calendarAuth.connected()) {
      this.loadTodayEvents();
    }

    this.updateCurrentTime();
    // Update time every minute
    this.timeInterval = setInterval(() => {
      this.updateCurrentTime();
    }, 60000);

    // Refresh calendar events every minute to show new events
    if (this.calendarAuth.connected()) {
      this.refreshInterval = setInterval(() => {
        if (!this.isLoading) {
          this.loadTodayEvents();
        }
      }, 60000); // Refresh every 60 seconds
    }
  }

  ngOnDestroy() {
    if (this.timeInterval) {
      clearInterval(this.timeInterval);
    }
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }

  updateCurrentTime() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    this.currentTime = `${hours}:${minutes}`;
  }

  loadTodayEvents() {
    this.isLoading = true;
    this.error = null;
    this.isAuthError = false;

    // Get tokens from localStorage
    const tokensStr = localStorage.getItem('calendar_tokens');
    if (!tokensStr) {
      console.warn('No tokens found in DayView, redirecting to connect...');
      this.calendarAuth.disconnect();
      window.location.href = '/app/dashboard';
      return;
    }

    const tokens = JSON.parse(tokensStr);

    // Fetch today's events from Google Calendar only
    this.calendarService.getTodayEvents(tokens).subscribe({
      next: (response) => {
        // Only show real events from Google Calendar
        this.events = (response.events || []).map((e: any) => ({
          id: e.id || Math.random().toString(),
          title: e.title || e.summary || 'Untitled Event',
          start_time: e.start_time || e.start?.dateTime || e.start?.date,
          end_time: e.end_time || e.end?.dateTime || e.end?.date
        }));

        this.isLoading = false;
        console.log(`Loaded ${this.events.length} real events from Google Calendar`);
      },
      error: (err) => {
        console.error('Failed to load calendar events', err);

        // Show error, but don't load fake events
        this.events = []; // Clear any previous events
        this.isLoading = false;

        // Check if it's an authentication error (401)
        if (err.status === 401 || (err.error && err.error.detail &&
          (err.error.detail.includes('Invalid or expired') ||
            err.error.detail.includes('authentication') ||
            err.error.detail.includes('reconnect')))) {
          // Clear invalid tokens and update connection status
          this.isAuthError = true;
          this.calendarAuth.disconnect();
          // Force re-check of connection status
          this.calendarAuth.checkConnectionStatus();

          this.error = 'Vos tokens de calendrier sont invalides ou expirés. Veuillez vous reconnecter à Google Calendar.';
        } else if (err.error && err.error.detail) {
          this.error = err.error.detail;
        } else {
          this.error = 'Erreur lors du chargement du calendrier Google. Veuillez réessayer.';
        }
      }
    });
  }

  reconnect() {
    this.calendarAuth.disconnect();
    window.location.href = '/app/dashboard';
  }

  disconnect() {
    if (confirm('Êtes-vous sûr de vouloir déconnecter votre calendrier Google ?')) {
      this.calendarAuth.disconnect();
      window.location.href = '/app/dashboard';
    }
  }

  getTopPosition(time: string): string {
    if (!time) {
      return '0px';
    }

    let hours = 0;
    let minutes = 0;

    if (time.includes('T')) {
      // ISO format (e.g., "2025-11-23T20:00:00+01:00")
      const date = new Date(time);
      if (!isNaN(date.getTime())) {
        // Respect the user's timezone when positioning events
        hours = date.getHours();
        minutes = date.getMinutes();
      } else {
        // Fallback: try to extract the time portion manually
        const timeMatch = time.match(/T(\d{2}):(\d{2})/);
        if (timeMatch) {
          hours = parseInt(timeMatch[1], 10);
          minutes = parseInt(timeMatch[2], 10);
        }
      }
    } else {
      // HH:MM format (e.g., "20:00")
      const parts = time.split(':');
      hours = parseInt(parts[0], 10);
      minutes = parseInt(parts[1] || '0', 10);
    }

    if (isNaN(hours) || isNaN(minutes)) {
      return '0px';
    }

    // Calculate position: each hour is 60px, each minute is 1px
    const totalMinutes = hours * 60 + minutes;
    return `${totalMinutes}px`;
  }

  formatTime(time: string): string {
    if (!time) {
      return '';
    }

    if (time.includes('T')) {
      const date = new Date(time);
      if (!isNaN(date.getTime())) {
        return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
      }

      const timeMatch = time.match(/T(\d{2}:\d{2})/);
      if (timeMatch) {
        return timeMatch[1];
      }
    }

    // Already HH:MM format or similar
    return time.slice(0, 5);
  }

  getHeight(start: string, end: string): string {
    if (!start || !end) return '0px';

    let duration = 0;

    // Handle ISO format times
    if (start.includes('T') && end.includes('T')) {
      // For ISO format, calculate duration using time difference (timezone-independent)
      const startDate = new Date(start);
      const endDate = new Date(end);
      duration = (endDate.getTime() - startDate.getTime()) / (1000 * 60);
    } else if (start.includes('T') || end.includes('T')) {
      // Mixed formats - extract time from ISO and compare with HH:MM
      let startMinutes = 0;
      let endMinutes = 0;

      if (start.includes('T')) {
        const timeMatch = start.match(/T(\d{2}):(\d{2})/);
        if (timeMatch) {
          startMinutes = parseInt(timeMatch[1], 10) * 60 + parseInt(timeMatch[2], 10);
        }
      } else {
        const [h, m] = start.split(':').map(Number);
        startMinutes = h * 60 + (m || 0);
      }

      if (end.includes('T')) {
        const timeMatch = end.match(/T(\d{2}):(\d{2})/);
        if (timeMatch) {
          endMinutes = parseInt(timeMatch[1], 10) * 60 + parseInt(timeMatch[2], 10);
        }
      } else {
        const [h, m] = end.split(':').map(Number);
        endMinutes = h * 60 + (m || 0);
      }

      duration = endMinutes - startMinutes;
    } else {
      // Both are HH:MM format
      const [startH, startM] = start.split(':').map(Number);
      const [endH, endM] = end.split(':').map(Number);
      duration = (endH * 60 + (endM || 0)) - (startH * 60 + (startM || 0));
    }

    // Ensure non-negative duration
    return `${Math.max(0, duration)}px`;
  }

  goToToday() {
    this.today = new Date();
    this.todayStr = this.today.toLocaleDateString('fr-FR', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
    this.loadTodayEvents();
  }
}

