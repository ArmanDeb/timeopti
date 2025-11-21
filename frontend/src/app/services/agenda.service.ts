import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
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

@Injectable({
    providedIn: 'root'
})
export class AgendaService {

    constructor(private http: HttpClient) { }

    optimizeAgenda(request: AgendaRequest): Observable<{ optimized_agenda: string }> {
        return this.http.post<{ optimized_agenda: string }>(`${environment.apiUrl}/optimize`, request);
    }
}
