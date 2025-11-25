import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AdminService, AdminStats, AdminLog, AdminUser, AdminRecommendation } from '../services/admin.service';

@Component({
    selector: 'app-admin',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './admin.html',
    styleUrl: './admin.css'
})
export class AdminComponent implements OnInit {
    stats: AdminStats | null = null;
    logs: AdminLog[] = [];
    users: AdminUser[] = [];
    recommendations: AdminRecommendation[] = [];

    loading = {
        stats: false,
        logs: false,
        users: false,
        recommendations: false
    };

    activeTab: 'overview' | 'logs' | 'users' | 'recommendations' = 'overview';

    constructor(private adminService: AdminService) { }

    ngOnInit() {
        this.loadStats();
        this.loadLogs();
        this.loadUsers();
        this.loadRecommendations();
    }

    loadStats() {
        this.loading.stats = true;
        this.adminService.getStats().subscribe({
            next: (data) => {
                this.stats = data;
                this.loading.stats = false;
            },
            error: (err) => {
                console.error('Error loading stats:', err);
                this.loading.stats = false;
            }
        });
    }

    loadLogs() {
        this.loading.logs = true;
        this.adminService.getLogs().subscribe({
            next: (data) => {
                this.logs = data.logs;
                this.loading.logs = false;
            },
            error: (err) => {
                console.error('Error loading logs:', err);
                this.loading.logs = false;
            }
        });
    }

    loadUsers() {
        this.loading.users = true;
        this.adminService.getUsers().subscribe({
            next: (data) => {
                this.users = data.users;
                this.loading.users = false;
            },
            error: (err) => {
                console.error('Error loading users:', err);
                this.loading.users = false;
            }
        });
    }

    loadRecommendations() {
        this.loading.recommendations = true;
        this.adminService.getRecommendations().subscribe({
            next: (data) => {
                this.recommendations = data.recommendations;
                this.loading.recommendations = false;
            },
            error: (err) => {
                console.error('Error loading recommendations:', err);
                this.loading.recommendations = false;
            }
        });
    }

    setTab(tab: 'overview' | 'logs' | 'users' | 'recommendations') {
        this.activeTab = tab;
    }

    formatDate(dateString: string): string {
        const date = new Date(dateString);
        return date.toLocaleString();
    }

    refresh() {
        this.loadStats();
        this.loadLogs();
        this.loadUsers();
        this.loadRecommendations();
    }

    getTotalCost(): number {
        if (!this.stats) return 0;
        return this.stats.endpoint_stats.reduce((acc, curr) => acc + (curr.total_cost || 0), 0);
    }

    getTotalTokens(): number {
        if (!this.stats) return 0;
        return this.stats.endpoint_stats.reduce((acc, curr) => acc + (curr.total_tokens || 0), 0);
    }
}
