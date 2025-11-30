import { Component, computed, inject, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CalendarService, CalendarEvent, ScheduleResponse } from '../../core/services/calendar.service';
import { ViewService } from '../../core/services/view.service';
import { CalendarAuthService } from '../../core/services/calendar-auth.service';
import { ViewStateService } from '../../core/services/view-state.service';

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
    startFromNow: boolean = true; // Default to true as requested

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
        // Set startFromNow based on selected date
        const selectedDate = this.viewState.selectedDate();
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        selectedDate.setHours(0, 0, 0, 0);

        // If viewing future date, turn off startFromNow
        this.startFromNow = selectedDate.getTime() <= today.getTime();

        // Add sample data for demo
        this.addSampleData();

        // Load real calendar events if connected
        this.loadRealCalendarEvents();

        // Load tasks from database
        this.loadTasks();
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
    loadTasks() {
        this.calendarService.fetchTasks().subscribe({
            next: (response) => {
                console.log('Loaded tasks from database:', response.tasks);
                this.tasks = response.tasks.map(t => ({
                    id: t.id,
                    title: t.title,
                    duration_minutes: t.duration_minutes,
                    priority: t.priority as 'high' | 'medium' | 'low',
                    deadline: t.deadline
                }));
            },
            error: (err) => {
                console.error('Failed to load tasks:', err);
                // Continue with empty tasks array
            }
        });
    }

    addTask() {
        if (!this.newTask.title || !this.newTask.duration_minutes) {
            return;
        }

        // Create task object for API
        const taskData = {
            title: this.newTask.title,
            duration_minutes: this.newTask.duration_minutes!,
            priority: this.newTask.priority || 'medium',
            deadline: this.newTask.deadline
        };

        // Save to database first
        this.calendarService.addTask(taskData).subscribe({
            next: (savedTask) => {
                console.log('Task saved to database:', savedTask);
                // Add to local array after successful save
                const task: Task = {
                    id: savedTask.id,
                    title: savedTask.title,
                    duration_minutes: savedTask.duration_minutes,
                    priority: savedTask.priority as 'high' | 'medium' | 'low',
                    deadline: savedTask.deadline
                };
                this.tasks.push(task);
                this.newTask = { title: '', duration_minutes: 30, priority: 'medium' };
            },
            error: (err) => {
                console.error('Failed to save task:', err);
                // Still add to local array for immediate feedback, but warn user
                const task: Task = {
                    id: Date.now().toString(),
                    title: this.newTask.title!,
                    duration_minutes: this.newTask.duration_minutes || 30,
                    priority: this.newTask.priority || 'medium',
                    deadline: this.newTask.deadline
                };
                this.tasks.push(task);
                this.newTask = { title: '', duration_minutes: 30, priority: 'medium' };
                this.error = 'Erreur lors de la sauvegarde de la tâche. Elle pourrait être perdue au rafraîchissement.';
            }
        });
    }

    removeTask(id: string) {
        // Try to delete from database first
        this.calendarService.deleteTask(id).subscribe({
            next: () => {
                console.log('Task deleted from database');
                // Remove from local array after successful deletion
                this.tasks = this.tasks.filter(t => t.id !== id);
            },
            error: (err) => {
                console.error('Failed to delete task from database:', err);
                // Still remove from local array
                this.tasks = this.tasks.filter(t => t.id !== id);
            }
        });
    }

    resetTasks() {
        if (!window.confirm('Êtes-vous sûr de vouloir supprimer toutes les tâches ? Cette action est irréversible.')) {
            return;
        }

        // Reset both manual tasks and scheduled tasks
        this.calendarService.resetTasks().subscribe({
            next: (response) => {
                console.log('All tasks deleted:', response);
                // Clear local array
                this.tasks = [];

                // Also reset scheduled tasks (optimized tasks)
                this.calendarService.resetScheduledTasks().subscribe({
                    next: () => {
                        console.log('All scheduled tasks deleted');
                        // Clear optimized tasks from ViewStateService
                        this.viewState.clearOptimizedTasks();
                    },
                    error: (err) => {
                        console.error('Failed to reset scheduled tasks:', err);
                    }
                });

                // Clear any error messages
                this.error = null;
            },
            error: (err) => {
                console.error('Failed to reset tasks:', err);
                this.error = 'Erreur lors de la suppression des tâches.';
            }
        });
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

    // Confirmation Modal State
    showConfirmationModal = false;
    pendingOptimization = false;

    // Natural language optimization
    optimizeFromNaturalInput() {
        if (!this.naturalInput.trim()) {
            this.error = 'Please describe what you want to accomplish';
            return;
        }

        // Check if there are already scheduled tasks for the selected date
        const selectedDate = this.viewState.selectedDate();

        // Check ViewStateService for existing tasks (source of truth)
        const viewStateTasks = this.viewState.optimizedTasks();
        const existingTasks = viewStateTasks.filter(t =>
            this.isSameDate(new Date(t.assigned_date), selectedDate)
        );

        if (existingTasks.length > 0) {
            this.showConfirmationModal = true;
            return;
        }

        this.proceedWithOptimization();
    }

    onConfirmRestart() {
        this.showConfirmationModal = false;

        // Clear existing tasks for the selected date
        // For now, we'll use the resetScheduledTasks which clears everything
        // Ideally, we should have a method to clear only for a specific date
        this.calendarService.resetScheduledTasks().subscribe({
            next: () => {
                console.log('Previous tasks cleared');
                this.viewState.clearOptimizedTasks();
                this.proceedWithOptimization();
            },
            error: (err) => {
                console.error('Failed to clear tasks:', err);
                this.error = 'Failed to clear previous tasks';
            }
        });
    }

    onConfirmAdd() {
        this.showConfirmationModal = false;
        this.proceedWithOptimization();
    }

    cancelOptimization() {
        this.showConfirmationModal = false;
    }

    proceedWithOptimization() {
        this.isOptimizing = true;
        this.error = null;

        console.log('Natural input:', this.naturalInput);

        // Get tokens for server-side event fetching
        const tokens = this.calendarAuth.getTokens();
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

        // Get the selected date from ViewStateService and format it as YYYY-MM-DD
        const selectedDate = this.viewState.selectedDate();
        const year = selectedDate.getFullYear();
        const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
        const day = String(selectedDate.getDate()).padStart(2, '0');
        const targetDateStr = `${year}-${month}-${day}`;

        console.log(`[Optimizer] Planning for date: ${targetDateStr} (selected date: ${selectedDate.toLocaleDateString()})`);

        // Get existing tasks to prevent overlap
        const viewStateTasks = this.viewState.optimizedTasks();
        const existingTasks = viewStateTasks.filter(t =>
            this.isSameDate(new Date(t.assigned_date), selectedDate)
        );

        this.calendarService.analyze(
            this.naturalInput,
            tokens, // Pass tokens for server-side event fetching
            timezone,
            this.sleepStart,
            this.sleepEnd,
            this.startFromNow,
            targetDateStr, // Pass the selected date
            existingTasks // Pass existing tasks
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
                // If we are adding, we should merge with existing tasks
                // But ViewStateService.setOptimizedTasks replaces the list
                // So we need to get current tasks, append new ones, and set back
                // However, since we are persisting to DB, maybe we should just reload from DB?
                // For now, let's just append to the view state if we didn't restart

                // Note: The backend 'analyze' currently returns NEW tasks.
                // It doesn't know about existing tasks unless we pass them (which we don't yet).
                // So 'tasksWithDates' only contains the new tasks.

                // We need to save these new tasks to the DB.
                this.calendarService.saveScheduledTasks(tasksWithDates).subscribe({
                    next: (response) => {
                        console.log('Optimized tasks saved to database:', response);

                        // After saving, let's refresh the view state with ALL tasks for the date
                        // We can do this by fetching from the service or manually merging
                        // For simplicity and correctness, let's fetch all tasks again
                        this.calendarService.fetchScheduledTasks().subscribe(res => {
                            const allTasks = res.tasks.filter(t => this.isSameDate(new Date(t.assigned_date), selectedDate));
                            this.viewState.setOptimizedTasks(allTasks);
                        });
                    },
                    error: (err) => {
                        console.error('Failed to save optimized tasks:', err);
                        // Fallback: just show new tasks (this might hide old ones temporarily in the view)
                        this.viewState.setOptimizedTasks(tasksWithDates as any[]);
                    }
                });

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
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        // Calculate start window based on sleep end and startFromNow
        let startWindow = this.sleepEnd;
        if (this.startFromNow) {
            const now = new Date();
            const currentHours = now.getHours().toString().padStart(2, '0');
            const currentMinutes = now.getMinutes().toString().padStart(2, '0');
            const currentTime = `${currentHours}:${currentMinutes}`;

            // Simple string comparison works for HH:MM format
            if (currentTime > startWindow) {
                startWindow = currentTime;
            }
        }

        this.calendarService.smartOptimize(
            this.tasks,
            undefined, // We already have events loaded
            todayEvents.length > 0 ? todayEvents : undefined,
            startWindow,     // Start of available time (sleep end or now)
            this.sleepStart  // End of available time (sleep start)
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
