import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface CalendarEvent {
    title: string;
    start_time: string;
    end_time: string;
}

export interface CalendarTokens {
    token: string;
    refresh_token: string;
    token_uri: string;
    client_id: string;
    client_secret: string;
    scopes: string[];
}

export interface ScheduledTask {
    task: any;
    start_time: string;
    end_time: string;
    gap_index: number;
    fit_score: number;
    explanation?: string;  // AI explanation for placement
    date?: Date;
}

export interface ScheduleResponse {
    schedule: {
        scheduled_tasks: ScheduledTask[];
        unscheduled_tasks: any[];
        explanation: string;
        success: boolean;
    };
    gaps_found: any[];
    events: CalendarEvent[];
    parsed_tasks?: any[];  // Tasks extracted from natural language
    warning?: string;
}

export interface AnalyzeResponse {
    proposals: {
        task_name: string;
        estimated_duration_minutes: number;
        assigned_date: string;
        assigned_start_time: string;
        assigned_end_time: string;
        slot_id: string;
        reasoning: string;
    }[];
    free_slots: any[];
    events: CalendarEvent[];
    target_date: string;
}

@Injectable({
    providedIn: 'root'
})
export class CalendarService {
    private apiUrl = environment.apiUrl;

    constructor(private http: HttpClient) { }

    getTodayEvents(tokens: any): Observable<{ events: CalendarEvent[] }> {
        return this.http.post<{ events: CalendarEvent[] }>(
            `${this.apiUrl}/events/today`,
            { tokens }
        );
    }

    analyze(naturalInput: string, tokens?: any, timezone?: string, sleepStart?: string, sleepEnd?: string, startFromNow?: boolean, targetDate?: string): Observable<AnalyzeResponse> {
        return this.http.post<AnalyzeResponse>(`${this.apiUrl}/analyze`, {
            natural_input: naturalInput,
            tokens,
            timezone,
            sleep_start: sleepStart,
            sleep_end: sleepEnd,
            start_from_now: startFromNow,
            target_date: targetDate
        });
    }

    commitSchedule(proposals: any[], tokens: any, timezone: string = 'UTC'): Observable<any> {
        return this.http.post(`${this.apiUrl}/commit-schedule`, {
            proposals,
            tokens,
            timezone
        });
    }

    getAuthUrl(redirectUri: string): Observable<{ auth_url: string }> {
        return this.http.post<{ auth_url: string }>(
            `${this.apiUrl}/calendar/auth-url`,
            { redirect_uri: redirectUri }
        );
    }

    exchangeToken(code: string, redirectUri: string): Observable<{ success: boolean; tokens: CalendarTokens }> {
        return this.http.post<{ success: boolean; tokens: CalendarTokens }>(
            `${this.apiUrl}/calendar/exchange-token`,
            { code, redirect_uri: redirectUri }
        );
    }

    getEvents(
        tokens: CalendarTokens,
        startDate?: string,
        endDate?: string
    ): Observable<{ events: CalendarEvent[] }> {
        return this.http.post<{ events: CalendarEvent[] }>(
            `${this.apiUrl}/calendar/events`,
            { tokens, start_date: startDate, end_date: endDate }
        );
    }

    getCalendarEvents(
        tokens: any,
        startDate: string,
        endDate: string
    ): Observable<{ events: any[] }> {
        return this.http.post<{ events: any[] }>(
            `${this.apiUrl}/calendar/events`,
            { tokens, start_date: startDate, end_date: endDate }
        );
    }

    smartOptimize(
        tasks: any[],
        calendarTokens?: CalendarTokens,
        events?: CalendarEvent[],
        startWindow: string = '09:00',
        endWindow: string = '17:00'
    ): Observable<ScheduleResponse> {
        return this.http.post<ScheduleResponse>(
            `${this.apiUrl}/smart-optimize`,
            {
                tasks,
                calendar_tokens: calendarTokens,
                events,
                start_window: startWindow,
                end_window: endWindow
            }
        );
    }

    smartOptimizeNatural(
        naturalInput: string,
        scope: 'today' | 'week',
        startWindow: string = '09:00',
        endWindow: string = '17:00',
        events?: CalendarEvent[]
    ): Observable<ScheduleResponse> {
        return this.http.post<ScheduleResponse>(
            `${this.apiUrl}/smart-optimize-natural`,
            {
                natural_input: naturalInput,
                scope,
                start_window: startWindow,
                end_window: endWindow,
                events: events || []
            }
        );
    }

    // Task Management Methods
    fetchTasks(): Observable<{ tasks: any[] }> {
        return this.http.get<{ tasks: any[] }>(`${this.apiUrl}/tasks`);
    }

    addTask(task: { title: string; duration_minutes: number; priority: string; deadline?: string }): Observable<any> {
        return this.http.post(`${this.apiUrl}/tasks`, task);
    }

    deleteTask(taskId: string): Observable<any> {
        return this.http.delete(`${this.apiUrl}/tasks/${taskId}`);
    }

    resetTasks(): Observable<{ success: boolean; deleted_count: number }> {
        return this.http.delete<{ success: boolean; deleted_count: number }>(`${this.apiUrl}/tasks/all`);
    }

    // Scheduled Tasks (Optimized Tasks) Methods
    fetchScheduledTasks(): Observable<{ tasks: any[] }> {
        return this.http.get<{ tasks: any[] }>(`${this.apiUrl}/scheduled-tasks`);
    }

    saveScheduledTasks(tasks: any[]): Observable<{ success: boolean; count: number }> {
        return this.http.post<{ success: boolean; count: number }>(`${this.apiUrl}/scheduled-tasks`, tasks);
    }

    resetScheduledTasks(): Observable<{ success: boolean; deleted_count: number }> {
        return this.http.delete<{ success: boolean; deleted_count: number }>(`${this.apiUrl}/scheduled-tasks/all`);
    }

    updateScheduledTask(
        taskId: string,
        updates: { assigned_date?: string; assigned_start_time?: string; assigned_end_time?: string }
    ): Observable<{ success: boolean; task: any }> {
        return this.http.patch<{ success: boolean; task: any }>(
            `${this.apiUrl}/scheduled-tasks/${taskId}`,
            updates
        );
    }
}
