import { Component, OnInit, OnDestroy, Input, Output, EventEmitter, effect, EffectRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CalendarService } from '../services/calendar.service';
import { CalendarAuthService } from '../services/calendar-auth.service';
import { ScheduledTask, ViewStateService } from '../services/view-state.service';
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

interface DisplayEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  type: 'google' | 'ai';
  data: any; // Original event or task object
  top: string;
  height: string;
  left: string;
  width: string;
  durationMinutes: number;
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
  // proposedTasks is now accessed directly via viewState.optimizedTasks()
  displayEvents: DisplayEvent[] = [];

  isLoading = false;
  error: string | null = null;
  isAuthError = false;
  currentTime: string = '';
  private timeInterval: any;
  private refreshInterval: any;
  private tasksEffect: any; // To track signal changes if needed, but we'll use a simple approach

  today: Date = new Date();
  currentDate: Date = new Date();
  todayStr: string = '';
  showDateDropdown = false;
  selectedDateLabel = "Aujourd'hui";

  hours: string[] = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`);

  // Drag & Drop state
  draggedTaskId: string | null = null;
  draggedTask: DisplayEvent | null = null;
  private originalTaskPosition: { top: string; start: string; end: string } | null = null;
  private isDragging = false;
  private dragStartPosition: { x: number; y: number } | null = null;
  private dragInitialStartMinutes = 0;
  private dragMaxUp = 0;
  private dragMaxDown = 0;
  dragPreviewOffset = 0;
  private activePointerId: number | null = null;
  private destroyOptimizedTasksEffect?: EffectRef;

  hasAiTasks = false;
  isExporting = false;

  private readonly SELECTED_DATE_STORAGE_KEY = 'day_view_selected_date';
  private readonly DRAG_STEP_MINUTES = 15;

  constructor(
    private calendarService: CalendarService,
    public calendarAuth: CalendarAuthService,
    public viewState: ViewStateService
  ) {
    if (!environment.production && typeof window !== 'undefined') {
      (window as any).__timeoptiViewState = this.viewState;
    }

    this.destroyOptimizedTasksEffect = effect(() => {
      const tasks = this.viewState.optimizedTasks();
      this.calculateLayout(tasks);
    });
  }

  ngOnInit() {
    this.restoreSelectedDateFromStorage();
    this.updateDateDisplay();

    // Set initial date in ViewStateService
    this.viewState.setSelectedDate(this.currentDate);
    this.persistSelectedDate();

    // Load scheduled tasks from database
    this.loadScheduledTasks();

    if (this.calendarAuth.connected()) {
      this.loadEvents();
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
          this.loadEvents(true); // Pass true for background refresh
        }
      }, 60000); // Refresh every 60 seconds
    }

    // Initial layout calculation (will be empty initially)
    this.calculateLayout();

  }

  ngOnDestroy() {
    if (this.timeInterval) {
      clearInterval(this.timeInterval);
    }
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
    this.destroyOptimizedTasksEffect?.destroy();
  }

  updateCurrentTime() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    this.currentTime = `${hours}:${minutes}`;
  }

  updateDateDisplay() {
    this.todayStr = this.currentDate.toLocaleDateString('fr-FR', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });

    // Check if currentDate is today or tomorrow for the label
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (this.isSameDate(this.currentDate, today)) {
      this.selectedDateLabel = "Aujourd'hui";
    } else if (this.isSameDate(this.currentDate, tomorrow)) {
      this.selectedDateLabel = "Demain";
    } else {
      this.selectedDateLabel = this.currentDate.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    }
  }

  isSameDate(d1: Date, d2: Date): boolean {
    return d1.getDate() === d2.getDate() &&
      d1.getMonth() === d2.getMonth() &&
      d1.getFullYear() === d2.getFullYear();
  }

  toggleDateDropdown() {
    this.showDateDropdown = !this.showDateDropdown;
  }

  selectDate(offset: number) {
    const date = new Date();
    date.setDate(date.getDate() + offset);
    this.currentDate = date;
    this.updateDateDisplay();
    this.showDateDropdown = false;

    // Notify ViewStateService of date change
    this.viewState.setSelectedDate(this.currentDate);
    this.persistSelectedDate();

    this.loadEvents();
  }

  loadScheduledTasks() {
    this.calendarService.fetchScheduledTasks().subscribe({
      next: (response) => {
        console.log('Loaded scheduled tasks from database:', response.tasks);
        // Update ViewStateService with loaded tasks
        this.viewState.setOptimizedTasks(response.tasks);
        // Recalculate layout to show the tasks
        this.calculateLayout();
      },
      error: (err) => {
        console.error('Failed to load scheduled tasks:', err);
        // Continue with empty tasks - they might not exist yet
      }
    });
  }

  loadEvents(isBackgroundRefresh = false) {
    if (!isBackgroundRefresh) {
      this.isLoading = true;
    }
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

    // Calculate start and end of the selected day
    const start = new Date(this.currentDate);
    start.setHours(0, 0, 0, 0);

    const end = new Date(this.currentDate);
    end.setHours(23, 59, 59, 999);

    // Format as ISO strings
    const startDateStr = start.toISOString();
    const endDateStr = end.toISOString();

    this.calendarService.getEvents(tokens, startDateStr, endDateStr).subscribe({
      next: (response) => {
        // Only show real events from Google Calendar
        this.events = (response.events || []).map((e: any) => ({
          id: e.id || Math.random().toString(),
          title: e.title || e.summary || 'Untitled Event',
          start_time: e.start_time || e.start?.dateTime || e.start?.date,
          end_time: e.end_time || e.end?.dateTime || e.end?.date
        }));

        this.isLoading = false;
        console.log(`Loaded ${this.events.length} real events from Google Calendar for ${startDateStr}`);
        this.calculateLayout();
      },
      error: (err) => {
        console.error('Failed to load calendar events', err);

        // Show error, but don't load fake events
        this.events = []; // Clear any previous events
        this.isLoading = false;
        this.calculateLayout();

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

  calculateLayout(tasksOverride?: ScheduledTask[]) {
    const googleEvents = this.events.map(e => ({
      id: e.id,
      title: e.title,
      start: e.start_time,
      end: e.end_time,
      type: 'google' as const,
      data: e
    }));

    // Filter AI tasks to only show those for the currently selected date
    // Use local date formatting to avoid timezone issues
    const year = this.currentDate.getFullYear();
    const month = String(this.currentDate.getMonth() + 1).padStart(2, '0');
    const day = String(this.currentDate.getDate()).padStart(2, '0');
    const currentDateStr = `${year}-${month}-${day}`; // Format: YYYY-MM-DD in local timezone

    const optimizedTasks = tasksOverride ?? this.viewState.optimizedTasks();
    const aiTasks = optimizedTasks
      .filter(t => {
        // Compare assigned_date with currentDate
        if (!t.assigned_date) return false;
        // Extract date part (handle both YYYY-MM-DD and ISO formats)
        const taskDateStr = t.assigned_date.split('T')[0].split(' ')[0]; // Handle YYYY-MM-DD and ISO formats
        const matches = taskDateStr === currentDateStr;
        if (!matches) {
          console.log(`[DayView] Filtered out task "${t.task_name}": assigned_date="${taskDateStr}" !== currentDate="${currentDateStr}"`);
        }
        return matches;
      })
      .map(t => {
        const snappedStart = this.snapToStep(this.getMinutesFromTime(t.assigned_start_time));
        const snappedEndRaw = this.snapToStep(this.getMinutesFromTime(t.assigned_end_time));
        const snappedEnd = Math.max(snappedStart + this.DRAG_STEP_MINUTES, snappedEndRaw);
        const startTime = this.minutesToTime(snappedStart);
        const endTime = this.minutesToTime(snappedEnd);

        const normalizedTask = {
          ...t,
          assigned_start_time: startTime,
          assigned_end_time: endTime,
          id: t.id || t.slot_id || Math.random().toString()
        };

        return {
          id: normalizedTask.id,
          title: normalizedTask.task_name,
          start: startTime,
          end: endTime,
          type: 'ai' as const,
          data: normalizedTask
        };
      });

    // Update hasAiTasks flag
    this.hasAiTasks = aiTasks.length > 0;

    const allItems = [...googleEvents, ...aiTasks];

    // 1. Convert times to minutes for easier calculation
    const itemsWithMinutes = allItems.map(item => {
      let startMin = this.getMinutesFromTime(item.start);
      let endMin = this.getMinutesFromTime(item.end);
      if (item.type === 'ai') {
        startMin = this.snapToStep(startMin);
        endMin = this.snapToStep(endMin);
      }
      const duration = endMin - startMin;
      // Visual end includes the minimum height (20px = 20min)
      // We use this for overlap detection to ensure tasks with min-height don't cover others
      const visualEndMin = Math.max(endMin, startMin + 20);

      return {
        ...item,
        startMin,
        endMin,
        visualEndMin,
        duration
      };
    }).sort((a, b) => a.startMin - b.startMin || (b.visualEndMin - b.startMin) - (a.visualEndMin - a.startMin));

    // 2. Group overlapping events
    const columns: any[][] = [];

    const clusters: any[][] = [];
    let currentCluster: any[] = [];
    let clusterEnd = -1;

    for (const item of itemsWithMinutes) {
      if (currentCluster.length === 0) {
        currentCluster.push(item);
        clusterEnd = item.visualEndMin;
      } else {
        if (item.startMin < clusterEnd) {
          // Overlaps with the current cluster (visually)
          currentCluster.push(item);
          clusterEnd = Math.max(clusterEnd, item.visualEndMin);
        } else {
          // Starts after the current cluster ends
          clusters.push(currentCluster);
          currentCluster = [item];
          clusterEnd = item.visualEndMin;
        }
      }
    }
    if (currentCluster.length > 0) {
      clusters.push(currentCluster);
    }

    // 3. Process each cluster to assign width and left position
    this.displayEvents = [];

    for (const cluster of clusters) {
      const slots: any[][] = []; // slots[colIndex] = [event, event]

      for (const item of cluster) {
        let placed = false;
        for (let i = 0; i < slots.length; i++) {
          const lastInSlot = slots[i][slots[i].length - 1];
          // Check against visual end of the last item to prevent overlap
          if (lastInSlot.visualEndMin <= item.startMin) {
            slots[i].push(item);
            item.colIndex = i;
            placed = true;
            break;
          }
        }
        if (!placed) {
          slots.push([item]);
          item.colIndex = slots.length - 1;
        }
      }

      const totalCols = slots.length;

      for (const item of cluster) {
        // Calculate visual properties
        const top = `${item.startMin}px`; // 1 min = 1px
        const height = `${Math.max(20, item.duration)}px`; // Min height 20px
        const width = `${100 / totalCols}%`;
        const left = `${(item.colIndex / totalCols) * 100}%`;

        this.displayEvents.push({
          id: item.id,
          title: item.title,
          start: item.start,
          end: item.end,
          type: item.type,
          data: item.data,
          top,
          height,
          left,
          width,
          durationMinutes: item.duration
        });
      }
    }
  }

  getMinutesFromTime(time: string): number {
    if (!time) return 0;

    if (time.includes('T')) {
      const match = time.match(/T(\d{2}):(\d{2})/);
      if (match) {
        return parseInt(match[1], 10) * 60 + parseInt(match[2], 10);
      }
      const date = new Date(time);
      if (!isNaN(date.getTime())) {
        return date.getHours() * 60 + date.getMinutes();
      }
    } else {
      const [h, m] = time.split(':').map(Number);
      return h * 60 + (m || 0);
    }
    return 0;
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
    // Kept for current time line
    return `${this.getMinutesFromTime(time)}px`;
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

  getDurationMinutes(start: string, end: string): number {
    return this.getMinutesFromTime(end) - this.getMinutesFromTime(start);
  }

  // Deprecated but kept if referenced elsewhere
  getHeight(start: string, end: string): string {
    return `${Math.max(20, this.getDurationMinutes(start, end))}px`;
  }

  goToToday() {
    this.selectDate(0);
  }

  trackByItemId(index: number, item: DisplayEvent): string {
    return item.id;
  }

  resetTasks() {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer toutes les tâches ? Cette action est irréversible.')) {
      return;
    }

    // Reset both manual tasks and scheduled tasks
    this.calendarService.resetTasks().subscribe({
      next: (response) => {
        console.log('All tasks deleted:', response);

        // Also reset scheduled tasks (optimized tasks)
        this.calendarService.resetScheduledTasks().subscribe({
          next: () => {
            console.log('All scheduled tasks deleted');
            // Clear optimized tasks from ViewStateService
            this.viewState.clearOptimizedTasks();
            // Recalculate layout to remove tasks from view
            this.calculateLayout();
          },
          error: (err) => {
            console.error('Failed to reset scheduled tasks:', err);
          }
        });
      },
      error: (err) => {
        console.error('Failed to reset tasks:', err);
      }
    });
  }

  exportToGoogleCalendar() {
    if (this.isExporting) return;

    const tokensStr = localStorage.getItem('calendar_tokens');
    if (!tokensStr) {
      this.error = 'Vous devez être connecté à Google Calendar pour exporter.';
      return;
    }

    const tokens = JSON.parse(tokensStr);

    // Get all AI tasks (not just for current day, but all proposed tasks)
    // We sanitize the date format to ensure YYYY-MM-DD
    const tasksToExport = this.viewState.optimizedTasks().map(t => ({
      ...t,
      assigned_date: t.assigned_date.split('T')[0].split(' ')[0]
    }));

    if (tasksToExport.length === 0) {
      return;
    }

    this.isExporting = true;

    this.calendarService.commitSchedule(tasksToExport, tokens).subscribe({
      next: (response) => {
        console.log('Export successful:', response);

        if (response.success) {
          // 1. Clear the "proposed" tasks since they are now real events
          this.calendarService.resetScheduledTasks().subscribe(() => {
            this.viewState.clearOptimizedTasks();

            // 2. Refresh calendar events to show the new Google events
            this.loadEvents();

            this.isExporting = false;
            // Optional: Show success toast/message
          });
        } else {
          this.error = 'Certaines tâches n\'ont pas pu être exportées.';
          this.isExporting = false;
        }
      },
      error: (err) => {
        console.error('Export failed:', err);
        this.error = 'Erreur lors de l\'export vers Google Calendar.';
        this.isExporting = false;
      }
    });
  }

  // Drag & Drop handlers
  onPointerDown(event: PointerEvent, item: DisplayEvent) {
    if (item.type !== 'ai') return;

    console.log('🖱️ Mouse down on AI task:', item);
    console.log('Event target:', event.target);
    console.log('Event currentTarget:', event.currentTarget);

    // Prevent default to avoid text selection / scroll on touch
    event.preventDefault();
    event.stopPropagation();

    // Store reference to the element
    const dragElement = event.currentTarget as HTMLElement;
    if (dragElement?.setPointerCapture) {
      try {
        dragElement.setPointerCapture(event.pointerId);
      } catch (err) {
        console.warn('Unable to set pointer capture', err);
      }
    }

    this.activePointerId = event.pointerId;
    this.isDragging = false;
    this.dragStartPosition = { x: event.clientX, y: event.clientY };

    // Add pointermove and pointerup listeners
    const onPointerMove = (e: PointerEvent) => {
      if (!this.dragStartPosition || e.pointerId !== this.activePointerId) return;

      const deltaX = Math.abs(e.clientX - this.dragStartPosition.x);
      const deltaY = Math.abs(e.clientY - this.dragStartPosition.y);

      // If mouse moved more than 5px, consider it a drag
      if (deltaX > 5 || deltaY > 5) {
        if (!this.isDragging) {
          this.isDragging = true;
          console.log('🔄 Drag detected, starting drag operation');
          // Initialize drag state
          this.draggedTaskId = item.id;
          this.draggedTask = item;
          this.originalTaskPosition = {
            top: item.top,
            start: item.start,
            end: item.end
          };
          this.dragInitialStartMinutes = this.getMinutesFromTime(item.start);
          this.dragMaxUp = this.dragInitialStartMinutes;
          this.dragMaxDown = 1440 - (this.dragInitialStartMinutes + item.durationMinutes);
          this.dragPreviewOffset = 0;

          // Visual feedback
          if (dragElement) {
            dragElement.style.opacity = '0.5';
            dragElement.style.cursor = 'grabbing';
          }
        }

        // Update position during drag (clamped within the day)
        const rawOffsetMinutes = e.clientY - this.dragStartPosition.y;
        const clampedRaw = Math.min(Math.max(rawOffsetMinutes, -this.dragMaxUp), this.dragMaxDown);
        const snapped = Math.round(clampedRaw / this.DRAG_STEP_MINUTES) * this.DRAG_STEP_MINUTES;
        const clampedSnapped = Math.min(Math.max(snapped, -this.dragMaxUp), this.dragMaxDown);
        this.dragPreviewOffset = clampedSnapped;
      }
    };

    const cleanup = () => {
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      window.removeEventListener('pointercancel', onPointerCancel);
      if (dragElement?.releasePointerCapture && this.activePointerId !== null) {
        try {
          dragElement.releasePointerCapture(this.activePointerId);
        } catch (err) {
          console.warn('Unable to release pointer capture', err);
        }
      }
      this.activePointerId = null;
    };

    const onPointerUp = (e: PointerEvent) => {
      if (e.pointerId !== this.activePointerId) {
        return;
      }
      cleanup();

      if (this.isDragging && this.draggedTaskId && this.draggedTask) {
        this.handleDrop();
      }

      // Reset visual feedback
      if (dragElement) {
        dragElement.style.opacity = '';
        dragElement.style.cursor = '';
      }

      this.dragStartPosition = null;
      this.isDragging = false;
      this.dragPreviewOffset = 0;
    };

    const onPointerCancel = (e: PointerEvent) => {
      if (e.pointerId !== this.activePointerId) {
        return;
      }
      cleanup();
      this.resetDragState();
      if (dragElement) {
        dragElement.style.opacity = '';
        dragElement.style.cursor = '';
      }
    };

    window.addEventListener('pointermove', onPointerMove, { passive: false });
    window.addEventListener('pointerup', onPointerUp, { passive: false });
    window.addEventListener('pointercancel', onPointerCancel, { passive: false });
  }

  private handleDrop() {
    if (!this.draggedTaskId || !this.draggedTask || !this.originalTaskPosition) {
      return;
    }

    console.log('📍 Handling drop with offset:', this.dragPreviewOffset);

    const deltaMinutes = Math.round(this.dragPreviewOffset / this.DRAG_STEP_MINUTES) * this.DRAG_STEP_MINUTES;
    const durationMinutes = this.draggedTask.durationMinutes;
    const tentativeStart = this.dragInitialStartMinutes + deltaMinutes;
    const newStartMinutes = Math.max(0, Math.min(1440 - durationMinutes, tentativeStart));
    const newEndMinutes = newStartMinutes + durationMinutes;

    const newStartTime = this.minutesToTime(newStartMinutes);
    const newEndTime = this.minutesToTime(newEndMinutes);

    // Get the task ID
    const taskData = this.draggedTask.data;
    const taskId = taskData.id || taskData.slot_id || this.draggedTaskId;

    // Get current date in YYYY-MM-DD format
    const year = this.currentDate.getFullYear();
    const month = String(this.currentDate.getMonth() + 1).padStart(2, '0');
    const day = String(this.currentDate.getDate()).padStart(2, '0');
    const assignedDate = `${year}-${month}-${day}`;

    // Update task position optimistically
    const taskIndex = this.displayEvents.findIndex(e => e.id === this.draggedTaskId);
    if (taskIndex !== -1) {
      this.displayEvents[taskIndex].start = newStartTime;
      this.displayEvents[taskIndex].end = newEndTime;
      this.calculateLayout();
    }
    this.dragPreviewOffset = 0;
    this.isDragging = false;

    // Send update to backend
    this.calendarService.updateScheduledTask(taskId, {
      assigned_date: assignedDate,
      assigned_start_time: newStartTime,
      assigned_end_time: newEndTime
    }).subscribe({
      next: (response) => {
        console.log('✅ Task updated successfully:', response);

        // Update the task in ViewStateService
        const optimizedTasks = this.viewState.optimizedTasks();
        const taskIndex = optimizedTasks.findIndex(t =>
          (t.id === taskId || t.slot_id === taskId)
        );

        if (taskIndex !== -1) {
          const updatedTasks = [...optimizedTasks];
          updatedTasks[taskIndex] = {
            ...updatedTasks[taskIndex],
            assigned_date: assignedDate,
            assigned_start_time: newStartTime,
            assigned_end_time: newEndTime
          };
          this.viewState.setOptimizedTasks(updatedTasks);
        }

        // Recalculate layout with updated data
        this.calculateLayout();

        this.resetDragState();
      },
      error: (err) => {
        console.error('❌ Failed to update task:', err);

        // Rollback: restore original position
        if (taskIndex !== -1 && this.originalTaskPosition) {
          this.displayEvents[taskIndex].start = this.originalTaskPosition.start;
          this.displayEvents[taskIndex].end = this.originalTaskPosition.end;
          this.calculateLayout();
        }

        // Show error message
        this.error = 'Erreur lors du déplacement de la tâche. Veuillez réessayer.';
        setTimeout(() => {
          this.error = null;
        }, 3000);

        this.resetDragState();
      }
    });
  }

  private resetDragState() {
    this.draggedTaskId = null;
    this.draggedTask = null;
    this.originalTaskPosition = null;
    this.dragPreviewOffset = 0;
    this.isDragging = false;
  }

  private minutesToTime(totalMinutes: number): string {
    const minutes = Math.max(0, Math.min(1440, totalMinutes));
    const hrs = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;
  }

  private snapToStep(minutes: number): number {
    const snapped = Math.round(minutes / this.DRAG_STEP_MINUTES) * this.DRAG_STEP_MINUTES;
    return Math.max(0, Math.min(1440, snapped));
  }

  private persistSelectedDate() {
    if (typeof window === 'undefined') {
      return;
    }
    try {
      localStorage.setItem(this.SELECTED_DATE_STORAGE_KEY, this.currentDate.toISOString());
    } catch (error) {
      console.warn('Unable to persist selected date', error);
    }
  }

  private restoreSelectedDateFromStorage() {
    if (typeof window === 'undefined') {
      return;
    }
    try {
      const stored = localStorage.getItem(this.SELECTED_DATE_STORAGE_KEY);
      if (stored) {
        const parsed = new Date(stored);
        if (!isNaN(parsed.getTime())) {
          this.currentDate = parsed;
        }
      }
    } catch (error) {
      console.warn('Unable to restore selected date', error);
    }
  }

}

