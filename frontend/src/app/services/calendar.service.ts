import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

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
    warning?: string;
}

@Injectable({
    providedIn: 'root'
})
export class CalendarService {
    private apiUrl = environment.apiUrl;

    constructor(private http: HttpClient) { }

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
}
