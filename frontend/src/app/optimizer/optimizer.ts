import { Component, computed, inject, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CalendarService, CalendarEvent, ScheduleResponse } from '../services/calendar.service';
import { ViewService } from '../services/view.service';
import { CalendarAuthService } from '../services/calendar-auth.service';
import { ViewStateService } from '../services/view-state.service';

interface Task {
    id: string;
    title: string;
    duration_minutes: number;
    priority: 'high' | 'medium' | 'low';
    deadline?: string;
}

interface CalendarEventInput extends CalendarEvent {
    id: string;
    date?: Date;
}

interface ScheduledTaskInput {
    task: any;
    start_time: string;
    end_time: string;
    gap_index: number;
    fit_score: number;
    explanation?: string;  // AI explanation for placement
    date?: Date;
}

@Component({
    selector: 'app-optimizer',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './optimizer.html',
    styleUrl: './optimizer.css'
})
export class OptimizerComponent {
    @Output() close = new EventEmitter<void>();
    
    // Natural language input
    naturalInput: string = '';
    optimizationScope: 'today' | 'week' = 'today';
    
    // Task management
    tasks: Task[] = [];
    newTask: Partial<Task> = {
        title: '',
        duration_minutes: 30,
        priority: 'medium'
    };

    // Calendar events
    events: CalendarEventInput[] = [];
    newEvent: Partial<CalendarEventInput> = {
        title: '',
        start_time: '',
        end_time: ''
    };

    // Time window
    sleepStart = '23:00';
    sleepEnd = '07:00';

    // Results
    scheduleResult: ScheduleResponse | null = null;
    isOptimizing = false;
    error: string | null = null;
    
    // Derived state for displayed days (Day or Week)
    displayedDays = computed(() => {
        const mode = this.viewService.viewMode();
        const current = this.viewService.currentDate();
        
        if (mode === 'Day') {
            return [current];
        }
        
        // Week Mode
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

    private calendarAuth = inject(CalendarAuthService);
    private viewState = inject(ViewStateService);
    
    // Store real calendar events from Google Calendar
    realCalendarEvents: CalendarEvent[] = [];

    constructor(
        private calendarService: CalendarService,
        public viewService: ViewService
    ) {
        // Add sample data for demo
        this.addSampleData();
        
        // Load real calendar events if connected
        this.loadRealCalendarEvents();
    }

    addSampleData() {
        // Don't add sample tasks by default - let user add their own
        this.tasks = [];

        // Don't add sample events - we'll use real calendar events
        this.events = [];
    }
    
    loadRealCalendarEvents() {
        if (!this.calendarAuth.connected()) {
            console.log('Calendar not connected, skipping event load');
            return;
        }
        
        const tokens = this.calendarAuth.getTokens();
        if (!tokens) {
            console.log('No tokens available');
            return;
        }
        
        // Get events for the current week
        const today = new Date();
        const startOfWeek = new Date(today);
        startOfWeek.setDate(today.getDate() - today.getDay() + 1); // Monday
        startOfWeek.setHours(0, 0, 0, 0);
        
        const endOfWeek = new Date(startOfWeek);
        endOfWeek.setDate(startOfWeek.getDate() + 6); // Sunday
        endOfWeek.setHours(23, 59, 59, 999);
        
        this.calendarService.getEvents(
            tokens,
            startOfWeek.toISOString(),
            endOfWeek.toISOString()
        ).subscribe({
            next: (response) => {
                console.log('Loaded calendar events:', response.events);
                this.realCalendarEvents = response.events;
                
                // Convert ISO events to display format with dates
                this.events = response.events.map((event, index) => {
                    const startDate = new Date(event.start_time);
                    return {
                        id: `gcal-${index}`,
                        title: event.title,
                        start_time: this.extractTime(event.start_time),
                        end_time: this.extractTime(event.end_time),
                        date: startDate
                    };
                });
            },
            error: (err) => {
                console.error('Failed to load calendar events:', err);
                // Continue with empty events
            }
        });
    }
    
    extractTime(isoString: string): string {
        // Extract HH:MM from ISO string
        const date = new Date(isoString);
        return date.toTimeString().slice(0, 5);
    }

    // Task management methods
    addTask() {
        if (!this.newTask.title || !this.newTask.duration_minutes) {
            return;
        }

        const task: Task = {
            id: Date.now().toString(),
            title: this.newTask.title,
            duration_minutes: this.newTask.duration_minutes,
            priority: this.newTask.priority || 'medium'
        };

        this.tasks.push(task);
        this.newTask = { title: '', duration_minutes: 30, priority: 'medium' };
    }

    removeTask(id: string) {
        this.tasks = this.tasks.filter(t => t.id !== id);
    }

    // Event management methods
    addEvent() {
        if (!this.newEvent.title || !this.newEvent.start_time || !this.newEvent.end_time) {
            return;
        }

        const event: CalendarEventInput = {
            id: Date.now().toString(),
            title: this.newEvent.title,
            start_time: this.newEvent.start_time,
            end_time: this.newEvent.end_time,
            date: this.viewService.currentDate()
        };

        this.events.push(event);
        this.newEvent = { title: '', start_time: '', end_time: '' };
    }

    removeEvent(id: string) {
        this.events = this.events.filter(e => e.id !== id);
    }

    // Natural language optimization
    optimizeFromNaturalInput() {
        if (!this.naturalInput.trim()) {
            this.error = 'Please describe what you want to accomplish';
            return;
        }

        this.isOptimizing = true;
        this.error = null;

        console.log('Natural input:', this.naturalInput);

        // Get tokens for server-side event fetching
        const tokens = this.calendarAuth.getTokens();
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        
        this.calendarService.analyze(
            this.naturalInput,
            tokens, // Pass tokens for server-side event fetching
            timezone,
            this.sleepStart,
            this.sleepEnd
        ).subscribe({
            next: (result) => {
                console.log('Analysis result:', result);
                this.isOptimizing = false;
                
                // Map proposals to format expected by day-view
                const tasksWithDates = result.proposals.map((p, index) => ({
                    task_name: p.task_name,
                    estimated_duration_minutes: p.estimated_duration_minutes,
                    assigned_date: p.assigned_date,
                    assigned_start_time: p.assigned_start_time,
                    assigned_end_time: p.assigned_end_time,
                    slot_id: p.slot_id,
                    reasoning: p.reasoning
                }));
                
                // Share optimized tasks with day-view via ViewStateService
                this.viewState.setOptimizedTasks(tasksWithDates as any[]);
                
                // Close the panel after successful optimization
                this.close.emit();
            },
            error: (err) => {
                console.error('Optimization error:', err);
                this.error = err.error?.detail || 'Failed to optimize schedule';
                this.isOptimizing = false;
            }
        });
    }
    
    // Optimization (legacy - keep for manual task addition)
    optimizeSchedule() {
        if (this.tasks.length === 0) {
            this.error = 'Please add at least one task';
            return;
        }

        this.isOptimizing = true;
        this.error = null;

        // Get today's events only for optimization
        const today = new Date();
        const todayEvents = this.events
            .filter(e => this.isSameDate(e.date, today))
            .map(e => ({
                title: e.title,
                start_time: e.start_time,
                end_time: e.end_time
            }));

        console.log('Optimizing with events:', todayEvents);
        console.log('Tasks:', this.tasks);
        console.log('Sleep window:', this.sleepStart, '-', this.sleepEnd);

        // Use real calendar events if available
        this.calendarService.smartOptimize(
            this.tasks,
            undefined, // We already have events loaded
            todayEvents.length > 0 ? todayEvents : undefined,
            this.sleepStart,
            this.sleepEnd
        ).subscribe({
            next: (result) => {
                console.log('Optimization result:', result);
                this.scheduleResult = result;
                this.isOptimizing = false;
                
                // Assign date to scheduled tasks (today)
                if (this.scheduleResult?.schedule.scheduled_tasks) {
                    this.scheduleResult.schedule.scheduled_tasks = this.scheduleResult.schedule.scheduled_tasks.map(t => ({
                        ...t,
                        date: today
                    }));
                }
            },
            error: (err) => {
                console.error('Optimization error:', err);
                this.error = err.error?.detail || 'Failed to optimize schedule';
                this.isOptimizing = false;
            }
        });
    }

    clearResults() {
        this.scheduleResult = null;
        this.error = null;
    }

    getPriorityColor(priority: string): string {
        switch (priority) {
            case 'high': return '#ef4444';
            case 'medium': return '#f59e0b';
            case 'low': return '#10b981';
            default: return '#6b7280';
        }
    }

    // Timeline helpers
    hours: string[] = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`); // 00:00 to 23:00

    getTopPosition(time: string): string {
        const [hours, minutes] = time.split(':').map(Number);
        const startHour = 0; // Start of timeline (00:00)
        const totalMinutes = (hours - startHour) * 60 + minutes;
        return `${totalMinutes}px`; // 1px per minute
    }

    getHeight(start: string, end: string): string {
        const [startH, startM] = start.split(':').map(Number);
        const [endH, endM] = end.split(':').map(Number);
        const durationMinutes = (endH * 60 + endM) - (startH * 60 + startM);
        return `${durationMinutes}px`;
    }
    
    // Filter events for a specific date
    getEventsForDate(date: Date): CalendarEventInput[] {
        return this.events.filter(e => this.isSameDate(e.date, date));
    }
    
    // Filter scheduled tasks for a specific date
    getTasksForDate(date: Date): ScheduledTaskInput[] {
         if (!this.scheduleResult?.schedule.scheduled_tasks) return [];
         return (this.scheduleResult.schedule.scheduled_tasks as ScheduledTaskInput[])
            .filter(t => this.isSameDate(t.date, date));
    }

    isSameDate(d1?: Date, d2?: Date): boolean {
        if (!d1 || !d2) return false;
        // Normalize to check just YYYY-MM-DD
        const date1 = new Date(d1);
        const date2 = new Date(d2);
        return date1.getFullYear() === date2.getFullYear() &&
               date1.getMonth() === date2.getMonth() &&
               date1.getDate() === date2.getDate();
    }
    
    isToday(date: Date): boolean {
        return this.isSameDate(date, new Date());
    }
    
    // Drag & Drop functionality
    draggedTask: ScheduledTaskInput | null = null;
    
    onDragStart(task: ScheduledTaskInput, event: DragEvent) {
        this.draggedTask = task;
        if (event.dataTransfer) {
            event.dataTransfer.effectAllowed = 'move';
            event.dataTransfer.setData('text/plain', task.task.id);
        }
    }
    
    onDragOver(event: DragEvent) {
        event.preventDefault();
        if (event.dataTransfer) {
            event.dataTransfer.dropEffect = 'move';
        }
    }
    
    onDrop(event: DragEvent, day: Date) {
        event.preventDefault();
        
        if (!this.draggedTask || !this.scheduleResult) return;
        
        // Get drop position relative to the day column
        const target = event.currentTarget as HTMLElement;
        const rect = target.getBoundingClientRect();
        const y = event.clientY - rect.top;
        
        // Calculate new time based on Y position (1px = 1 minute)
        const newStartMinutes = Math.floor(y);
        const newStartHour = Math.floor(newStartMinutes / 60);
        const newStartMin = newStartMinutes % 60;
        const newStartTime = `${newStartHour.toString().padStart(2, '0')}:${newStartMin.toString().padStart(2, '0')}`;
        
        // Calculate end time
        const duration = this.draggedTask.task.duration_minutes;
        const endMinutes = newStartMinutes + duration;
        const endHour = Math.floor(endMinutes / 60);
        const endMin = endMinutes % 60;
        const newEndTime = `${endHour.toString().padStart(2, '0')}:${endMin.toString().padStart(2, '0')}`;
        
        // Update the task
        const taskIndex = this.scheduleResult.schedule.scheduled_tasks.findIndex(
            t => (t as ScheduledTaskInput).task.id === this.draggedTask!.task.id
        );
        
        if (taskIndex !== -1) {
            const updatedTask = {
                ...this.scheduleResult.schedule.scheduled_tasks[taskIndex],
                start_time: newStartTime,
                end_time: newEndTime,
                date: day
            } as ScheduledTaskInput;
            
            this.scheduleResult.schedule.scheduled_tasks[taskIndex] = updatedTask;
        }
        
        this.draggedTask = null;
    }
}
