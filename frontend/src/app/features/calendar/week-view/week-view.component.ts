import { Component, OnInit, OnDestroy, computed, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CalendarService } from '../../../core/services/calendar.service';
import { CalendarAuthService } from '../../../core/services/calendar-auth.service';
import { ViewService } from '../../../core/services/view.service';
import { ViewStateService } from '../../../core/services/view-state.service';

interface CalendarEvent {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  date: Date;
}

interface FreeSlot {
  start: string;
  end: string;
  duration: number; // in minutes
  date: Date;
}

@Component({
  selector: 'app-week-view',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './week-view.component.html',
  styleUrl: './week-view.component.css'
})
export class WeekViewComponent implements OnInit, OnDestroy {
  @Input() showTaskButton = false;
  @Output() openTaskPanel = new EventEmitter<void>();

  events: CalendarEvent[] = [];
  freeSlots: FreeSlot[] = [];
  isLoading = false;
  error: string | null = null;
  currentTime: string = '';
  private timeInterval: any;

  // Work hours
  workStart = '09:00';
  workEnd = '18:00';

  // Week days
  displayedDays = computed(() => {
    const current = this.viewService.currentDate();
    const startOfWeek = new Date(current);
    const day = startOfWeek.getDay();
    const diff = startOfWeek.getDate() - day + (day === 0 ? -6 : 1); // Monday start
    startOfWeek.setDate(diff);

    const days = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(startOfWeek);
      d.setDate(startOfWeek.getDate() + i);
      days.push(d);
    }
    return days;
  });

  hours: string[] = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`);

  constructor(
    private calendarService: CalendarService,
    public calendarAuth: CalendarAuthService,
    public viewService: ViewService,
    public viewState: ViewStateService
  ) { }

  ngOnInit() {
    if (this.calendarAuth.connected()) {
      this.loadCalendarEvents();
    }

    this.updateCurrentTime();
    // Update time every minute
    this.timeInterval = setInterval(() => {
      this.updateCurrentTime();
    }, 60000);
  }

  ngOnDestroy() {
    if (this.timeInterval) {
      clearInterval(this.timeInterval);
    }
  }

  updateCurrentTime() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    this.currentTime = `${hours}:${minutes}`;
  }

  loadCalendarEvents() {
    this.isLoading = true;
    this.error = null;

    const days = this.displayedDays();
    const startDate = days[0].toISOString();
    const endDate = days[days.length - 1].toISOString();

    // Get tokens from localStorage (temporary solution)
    const tokensStr = localStorage.getItem('calendar_tokens');
    if (!tokensStr) {
      this.error = 'Tokens non trouvés. Veuillez reconnecter votre calendrier.';
      this.isLoading = false;
      return;
    }

    const tokens = JSON.parse(tokensStr);

    // Check if demo mode (tokens contain 'demo' or 'mock')
    if (tokens.token.includes('demo') || tokens.token.includes('mock')) {
      // Load demo data
      this.loadDemoData();
      return;
    }

    this.calendarService.getCalendarEvents(tokens, startDate, endDate).subscribe({
      next: (response) => {
        // Map events to our format
        this.events = response.events.map((e: any) => ({
          id: e.id || Math.random().toString(),
          title: e.title,
          start_time: e.start_time,
          end_time: e.end_time,
          date: new Date(e.start_time) // Parse date from start_time
        }));

        this.calculateFreeSlots();
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Failed to load calendar events', err);

        // Check for specific error messages from backend
        if (err.error && err.error.detail) {
          this.error = err.error.detail;
        } else {
          this.error = 'Erreur lors du chargement du calendrier. Passage en mode démo.';
        }

        // Fallback to demo data on error
        this.loadDemoData();
      }
    });
  }

  loadDemoData() {
    const days = this.displayedDays();

    // Create demo events for this week
    this.events = [
      // Monday
      { id: '1', title: 'Réunion d\'équipe', start_time: '09:00', end_time: '10:00', date: days[0] },
      { id: '2', title: 'Appel client', start_time: '11:00', end_time: '12:00', date: days[0] },
      { id: '3', title: 'Déjeuner', start_time: '12:00', end_time: '13:00', date: days[0] },
      { id: '4', title: 'Code review', start_time: '15:00', end_time: '16:00', date: days[0] },

      // Tuesday
      { id: '5', title: 'Stand-up', start_time: '09:00', end_time: '09:30', date: days[1] },
      { id: '6', title: 'Développement', start_time: '10:00', end_time: '12:00', date: days[1] },
      { id: '7', title: 'Pause déjeuner', start_time: '12:00', end_time: '13:00', date: days[1] },
      { id: '8', title: 'Réunion projet', start_time: '14:00', end_time: '15:30', date: days[1] },

      // Wednesday
      { id: '9', title: 'Planning', start_time: '09:00', end_time: '10:30', date: days[2] },
      { id: '10', title: 'Déjeuner', start_time: '12:00', end_time: '13:00', date: days[2] },
      { id: '11', title: 'Formation', start_time: '14:00', end_time: '17:00', date: days[2] },

      // Thursday
      { id: '12', title: 'Réunion hebdo', start_time: '09:00', end_time: '10:00', date: days[3] },
      { id: '13', title: 'Déjeuner', start_time: '12:00', end_time: '13:00', date: days[3] },
      { id: '14', title: 'Présentation', start_time: '15:00', end_time: '16:30', date: days[3] },

      // Friday
      { id: '15', title: 'Rétrospective', start_time: '09:00', end_time: '10:30', date: days[4] },
      { id: '16', title: 'Déjeuner d\'équipe', start_time: '12:00', end_time: '14:00', date: days[4] },
    ];

    this.calculateFreeSlots();
    this.isLoading = false;
  }

  disconnect() {
    if (confirm('Êtes-vous sûr de vouloir déconnecter votre calendrier Google ?')) {
      this.calendarAuth.disconnect();
      // Reload the page to go back to onboarding
      window.location.href = '/app/dashboard';
    }
  }

  calculateFreeSlots() {
    this.freeSlots = [];
    const days = this.displayedDays();

    days.forEach(day => {
      const dayEvents = this.getEventsForDate(day).sort((a, b) =>
        a.start_time.localeCompare(b.start_time)
      );

      // Start from work start time
      let currentTime = this.workStart;

      dayEvents.forEach(event => {
        // If there's a gap between current time and event start
        if (currentTime < event.start_time) {
          const duration = this.getMinutesBetween(currentTime, event.start_time);
          if (duration >= 30) { // Only show slots >= 30 minutes
            this.freeSlots.push({
              start: currentTime,
              end: event.start_time,
              duration,
              date: day
            });
          }
        }
        currentTime = event.end_time;
      });

      // Check for free time after last event until work end
      if (currentTime < this.workEnd) {
        const duration = this.getMinutesBetween(currentTime, this.workEnd);
        if (duration >= 30) {
          this.freeSlots.push({
            start: currentTime,
            end: this.workEnd,
            duration,
            date: day
          });
        }
      }
    });
  }

  getMinutesBetween(start: string, end: string): number {
    const [startH, startM] = start.split(':').map(Number);
    const [endH, endM] = end.split(':').map(Number);
    return (endH * 60 + endM) - (startH * 60 + startM);
  }

  getEventsForDate(date: Date): CalendarEvent[] {
    return this.events.filter(e => this.isSameDate(e.date, date));
  }

  getFreeSlotsForDate(date: Date): FreeSlot[] {
    return this.freeSlots.filter(s => this.isSameDate(s.date, date));
  }

  getOptimizedTasksForDate(date: Date): any[] {
    const tasks = this.viewState.optimizedTasks();
    // For MVP, we only show today's tasks
    return tasks.filter(t => {
      const taskDate = new Date(t.assigned_date);
      return this.isSameDate(taskDate, date);
    });
  }

  isSameDate(d1: Date, d2: Date): boolean {
    return d1.getFullYear() === d2.getFullYear() &&
      d1.getMonth() === d2.getMonth() &&
      d1.getDate() === d2.getDate();
  }

  isToday(date: Date): boolean {
    return this.isSameDate(date, new Date());
  }

  getTopPosition(time: string): string {
    if (!time) return '0px';

    // Handle ISO string or HH:MM
    let hours = 0;
    let minutes = 0;

    if (time.includes('T')) {
      const date = new Date(time);
      if (!isNaN(date.getTime())) {
        hours = date.getHours();
        minutes = date.getMinutes();
      } else {
        const timeMatch = time.match(/T(\d{2}):(\d{2})/);
        if (timeMatch) {
          hours = parseInt(timeMatch[1], 10);
          minutes = parseInt(timeMatch[2], 10);
        }
      }
    } else {
      const parts = time.split(':');
      hours = parseInt(parts[0], 10);
      minutes = parseInt(parts[1] || '0', 10);
    }

    if (isNaN(hours) || isNaN(minutes)) return '0px';

    const totalMinutes = hours * 60 + minutes;
    return `${totalMinutes}px`;
  }

  getHeight(start: string, end: string): string {
    if (!start || !end) return '0px';

    let duration = 0;

    // Handle ISO format times
    if (start.includes('T') && end.includes('T')) {
      // For ISO format, calculate duration using time difference
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
        } else {
          const d = new Date(start);
          startMinutes = d.getHours() * 60 + d.getMinutes();
        }
      } else {
        const [h, m] = start.split(':').map(Number);
        startMinutes = h * 60 + (m || 0);
      }

      if (end.includes('T')) {
        const timeMatch = end.match(/T(\d{2}):(\d{2})/);
        if (timeMatch) {
          endMinutes = parseInt(timeMatch[1], 10) * 60 + parseInt(timeMatch[2], 10);
        } else {
          const d = new Date(end);
          endMinutes = d.getHours() * 60 + d.getMinutes();
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

    return `${Math.max(0, duration)}px`;
  }

  previousWeek() {
    this.viewService.previousPeriod();
    this.loadCalendarEvents();
  }

  nextWeek() {
    this.viewService.nextPeriod();
    this.loadCalendarEvents();
  }

  goToToday() {
    this.viewService.goToToday();
    this.loadCalendarEvents();
  }
}
