import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { ViewStateService } from '../../core/services/view-state.service';
import { CalendarAuthService } from '../../core/services/calendar-auth.service';
import { DayViewComponent } from '../calendar/day-view/day-view.component';
import { OptimizerComponent } from '../optimizer/optimizer';

@Component({
    selector: 'app-dashboard',
    standalone: true,
    imports: [CommonModule, DayViewComponent, OptimizerComponent],
    templateUrl: './dashboard.component.html',
    styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit {
    showTaskPanel = false;

    constructor(
        public viewState: ViewStateService,
        private calendarAuth: CalendarAuthService,
        private route: ActivatedRoute
    ) {
        // Check if calendar is already connected
        if (this.calendarAuth.connected()) {
            this.viewState.setState('input');
        }
    }

    ngOnInit() {
        // Handle OAuth callback
        this.route.queryParams.subscribe(params => {
            const code = params['code'];
            if (code) {
                console.log('🔗 [DASHBOARD] OAuth code detected, exchanging for tokens...');
                const redirectUri = window.location.origin + '/app/dashboard';
                this.calendarAuth.exchangeCodeForTokens(code, redirectUri);
            }
        });
    }

    connectCalendar() {
        this.calendarAuth.connect();
        // connect() handles the redirect internally, so we don't need to subscribe
        // The state will be updated when the user returns from OAuth
    }

    toggleTaskPanel() {
        this.showTaskPanel = !this.showTaskPanel;
    }
}
