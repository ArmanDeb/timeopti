import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';

export interface Task {
    id: string;
    title: string;
    duration_minutes: number;
    priority: 'high' | 'medium' | 'low';
    deadline?: string;
}

export interface AgendaRequest {
    tasks: Task[];
    start_time: string;
    end_time: string;
}

export interface Event {
    title: string;
    start_time: string;
    end_time: string;
}

export interface Gap {
    start_time: string;
    end_time: string;
    duration_minutes: number;
}

export interface GapRequest {
    events: Event[];
    start_window: string;
    end_window: string;
}

export interface PriorityRequest {
    tasks: Task[];
}

@Injectable({
    providedIn: 'root'
})
export class AgendaService {

    constructor(private http: HttpClient) { }

    optimizeAgenda(request: AgendaRequest): Observable<{ optimized_agenda: string }> {
        return this.http.post<{ optimized_agenda: string }>(`${environment.apiUrl}/optimize`, request);
    }

    analyzeGaps(request: GapRequest): Observable<{ gaps: Gap[] }> {
        return this.http.post<{ gaps: Gap[] }>(`${environment.apiUrl}/analyze/gaps`, request);
    }

    analyzePriorities(request: PriorityRequest): Observable<{ priorities: string }> {
        return this.http.post<{ priorities: string }>(`${environment.apiUrl}/analyze/priorities`, request);
    }
}
