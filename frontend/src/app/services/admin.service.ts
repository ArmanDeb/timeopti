import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { Observable } from 'rxjs';

export interface AdminStats {
    total_users: number;
    total_logs: number;
    total_recommendations: number;
    endpoint_stats: {
        endpoint: string;
        count: number;
        avg_duration_ms: number;
        total_cost: number;
        total_tokens: number;
    }[];
}

export interface AdminLog {
    id: string;
    user_id: string | null;
    endpoint: string;
    duration_ms: number;
    error: string | null;
    created_at: string;
    tokens_used?: number;
    model?: string;
    cost?: number;
}

export interface AdminUser {
    id: string;
    email: string;
    clerk_user_id: string;
    is_admin: boolean;
    created_at: string;
    total_logs: number;
    total_recommendations: number;
}

export interface AdminRecommendation {
    id: string;
    user_id: string | null;
    recommendation_text: string;
    tasks_count: number;
    created_at: string;
}

@Injectable({
    providedIn: 'root'
})
export class AdminService {

    constructor(private http: HttpClient) { }

    getStats(): Observable<AdminStats> {
        return this.http.get<AdminStats>(`${environment.apiUrl}/admin/stats`);
    }

    getLogs(limit: number = 50): Observable<{ logs: AdminLog[] }> {
        return this.http.get<{ logs: AdminLog[] }>(`${environment.apiUrl}/admin/logs?limit=${limit}`);
    }

    getUsers(): Observable<{ users: AdminUser[] }> {
        return this.http.get<{ users: AdminUser[] }>(`${environment.apiUrl}/admin/users`);
    }

    getRecommendations(limit: number = 50): Observable<{ recommendations: AdminRecommendation[] }> {
        return this.http.get<{ recommendations: AdminRecommendation[] }>(`${environment.apiUrl}/admin/recommendations?limit=${limit}`);
    }
}
