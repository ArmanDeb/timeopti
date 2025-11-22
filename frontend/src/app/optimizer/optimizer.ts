import { Component, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CalendarService, CalendarEvent, ScheduleResponse } from '../services/calendar.service';
import { ViewService } from '../services/view.service';

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
    startWindow = '09:00';
    endWindow = '17:00';

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

    constructor(
        private calendarService: CalendarService,
        public viewService: ViewService
    ) {
        // Add sample data for demo
        this.addSampleData();
    }

    addSampleData() {
        this.tasks = [
            { id: '1', title: 'Write report', duration_minutes: 60, priority: 'high' },
            { id: '2', title: 'Email team', duration_minutes: 30, priority: 'medium' },
            { id: '3', title: 'Review docs', duration_minutes: 45, priority: 'low' }
        ];

        // Create events relative to today to ensure they appear
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(today.getDate() + 1);
        const yesterday = new Date(today);
        yesterday.setDate(today.getDate() - 1);

        this.events = [
            { id: '1', title: 'Team Meeting', start_time: '10:00', end_time: '11:00', date: today },
            { id: '2', title: 'Lunch Break', start_time: '12:00', end_time: '13:00', date: today },
            { id: '3', title: 'Project Sync', start_time: '14:00', end_time: '15:00', date: tomorrow },
            { id: '4', title: 'Client Call', start_time: '09:00', end_time: '10:00', date: yesterday }
        ];
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

    // Optimization
    optimizeSchedule() {
        if (this.tasks.length === 0) {
            this.error = 'Please add at least one task';
            return;
        }

        this.isOptimizing = true;
        this.error = null;

        // For now, optimization only runs for "today" in the backend
        // In a real implementation, we'd pass the date or range
        this.calendarService.smartOptimize(
            this.tasks,
            undefined, // No calendar tokens (manual events)
            this.events,
            this.startWindow,
            this.endWindow
        ).subscribe({
            next: (result) => {
                this.scheduleResult = result;
                this.isOptimizing = false;
                
                // Simulate assigning date to scheduled tasks (today)
                if (this.scheduleResult?.schedule.scheduled_tasks) {
                    this.scheduleResult.schedule.scheduled_tasks = this.scheduleResult.schedule.scheduled_tasks.map(t => ({
                        ...t,
                        date: this.viewService.currentDate()
                    }));
                }
            },
            error: (err) => {
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
}
