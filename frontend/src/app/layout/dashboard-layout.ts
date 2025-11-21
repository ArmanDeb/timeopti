import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ClerkService } from '../services/clerk.service';

@Component({
    selector: 'app-dashboard-layout',
    standalone: true,
    imports: [CommonModule, RouterModule],
    templateUrl: './dashboard-layout.html',
})
export class DashboardLayoutComponent {
    isSidebarOpen = true;
    currentDate: Date = new Date();
    viewMode: 'Day' | 'Week' | 'Month' = 'Week';

    constructor(public clerkService: ClerkService) { }

    toggleSidebar() {
        this.isSidebarOpen = !this.isSidebarOpen;
    }

    previousPeriod() {
        // Logic to go back based on viewMode (placeholder for now)
        console.log('Previous period');
    }

    nextPeriod() {
        // Logic to go forward based on viewMode (placeholder for now)
        console.log('Next period');
    }

    goToToday() {
        this.currentDate = new Date();
    }
}
