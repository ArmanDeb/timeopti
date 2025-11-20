import { Injectable } from '@angular/core';
import { Clerk } from '@clerk/clerk-js';
import { environment } from '../../environments/environment';

@Injectable({
    providedIn: 'root'
})
export class ClerkService {
    clerk: any;
    isLoaded = false;

    constructor() {
        this.clerk = new Clerk(environment.clerkPublishableKey);
        this.initialize();
    }

    async initialize() {
        try {
            await this.clerk.load();
            this.isLoaded = true;
            console.log('Clerk loaded');
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
