import { Injectable, inject } from '@angular/core';
import { Clerk } from '@clerk/clerk-js';
import { environment } from '../../../environments/environment';
import { CalendarAuthService } from './calendar-auth.service';

@Injectable({
    providedIn: 'root'
})
export class ClerkService {
    clerk: any;
    isLoaded = false;
    private calendarAuth = inject(CalendarAuthService);

    constructor() {
        this.clerk = new Clerk(environment.clerkPublishableKey);
        this.initialize();
    }

    async initialize() {
        try {
            await this.clerk.load();
            this.isLoaded = true;
            console.log('Clerk loaded');

            // Listen for auth changes
            this.clerk.addListener((resources: any) => {
                // If no user is present (logout), disconnect calendar
                if (!resources.user) {
                    console.log('👤 [CLERK] User signed out, cleaning up calendar session...');
                    this.calendarAuth.disconnect();
                }
            });

        } catch (error) {
            console.error('Error loading Clerk:', error);
        }
    }

    get user() {
        return this.clerk.user;
    }

    get session() {
        return this.clerk.session;
    }

    signIn() {
        this.clerk.openSignIn();
    }

    signOut() {
        this.calendarAuth.disconnect();
        this.clerk.signOut();
    }

    mountUserButton(node: HTMLDivElement) {
        if (this.isLoaded) {
            this.clerk.mountUserButton(node);
        } else {
            // Retry or wait
            setTimeout(() => this.mountUserButton(node), 100);
        }
    }
}
