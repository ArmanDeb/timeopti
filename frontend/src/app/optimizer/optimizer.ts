import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CalendarService, CalendarEvent, ScheduleResponse } from '../services/calendar.service';

interface Task {
    id: string;
    title: string;
    duration_minutes: number;
    priority: 'high' | 'medium' | 'low';
    deadline?: string;
}

interface CalendarEventInput extends CalendarEvent {
    id: string;
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

    constructor(private calendarService: CalendarService) {
        // Add sample data for demo
        this.addSampleData();
    }

    addSampleData() {
        this.tasks = [
            { id: '1', title: 'Write report', duration_minutes: 60, priority: 'high' },
            { id: '2', title: 'Email team', duration_minutes: 30, priority: 'medium' },
            { id: '3', title: 'Review docs', duration_minutes: 45, priority: 'low' }
        ];

        this.events = [
            { id: '1', title: 'Team Meeting', start_time: '10:00', end_time: '11:00' },
            { id: '2', title: 'Lunch Break', start_time: '12:00', end_time: '13:00' }
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
            end_time: this.newEvent.end_time
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
    currentDate: Date = new Date();
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
}
