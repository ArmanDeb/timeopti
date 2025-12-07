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
    private hasAttemptedAutoConnect = false;

    constructor() {
        this.clerk = new Clerk(environment.clerkPublishableKey);
        this.initialize();
    }

    async initialize() {
        try {
            await this.clerk.load();
            this.isLoaded = true;
            console.log('Clerk loaded');

            // If user is already logged in, try auto-connect
            if (this.clerk.user && !this.hasAttemptedAutoConnect) {
                this.attemptAutoConnect();
            }

            // Listen for auth changes
            this.clerk.addListener((resources: any) => {
                // If no user is present (logout), disconnect calendar
                if (!resources.user) {
                    console.log('👤 [CLERK] User signed out, cleaning up calendar session...');
                    this.calendarAuth.disconnect();
                    this.hasAttemptedAutoConnect = false;
                } else if (resources.user && !this.hasAttemptedAutoConnect) {
                    // User just logged in, try auto-connect
                    console.log('👤 [CLERK] User signed in, attempting auto-connect...');
                    this.attemptAutoConnect();
                }
            });

        } catch (error) {
            console.error('Error loading Clerk:', error);
        }
    }

    private async attemptAutoConnect() {
        if (this.hasAttemptedAutoConnect) return;
        this.hasAttemptedAutoConnect = true;

        try {
            const success = await this.calendarAuth.tryAutoConnectFromClerk();
            if (success) {
                console.log('✅ [CLERK] Calendar auto-connected successfully');
            } else {
                console.log('📅 [CLERK] Manual calendar connection required');
            }
        } catch (e) {
            console.error('❌ [CLERK] Auto-connect failed:', e);
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
