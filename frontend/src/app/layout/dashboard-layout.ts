import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ClerkService } from '../services/clerk.service';
import { ViewService } from '../services/view.service';

@Component({
    selector: 'app-dashboard-layout',
    standalone: true,
    imports: [CommonModule, RouterModule],
    templateUrl: './dashboard-layout.html',
})
export class DashboardLayoutComponent {
    isSidebarOpen = true;
    
    constructor(
        public clerkService: ClerkService,
        public viewService: ViewService
    ) { }

    toggleSidebar() {
        this.isSidebarOpen = !this.isSidebarOpen;
    }

    previousPeriod() {
        this.viewService.previousPeriod();
    }

    nextPeriod() {
        this.viewService.nextPeriod();
    }

    goToToday() {
        this.viewService.goToToday();
    }

    toggleViewMode() {
        const current = this.viewService.viewMode();
        this.viewService.setViewMode(current === 'Day' ? 'Week' : 'Day');
    }
}
