import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { ClerkService } from '../services/clerk.service';

export const authGuard: CanActivateFn = async (route, state) => {
    const clerkService = inject(ClerkService);
    const router = inject(Router);

    console.log('Auth Guard - User (initial):', clerkService.user);
    console.log('Auth Guard - Attempting to access:', state.url);

    // Wait for Clerk to initialize if not already loaded
    if (!clerkService.user && clerkService.clerk) {
        console.log('Auth Guard - Waiting for Clerk to load user...');
        try {
            // Wait up to 3 seconds for Clerk to load the user
            await new Promise<void>((resolve) => {
                let attempts = 0;
                const maxAttempts = 30; // 3 seconds (30 * 100ms)
                
                const checkUser = setInterval(() => {
                    attempts++;
                    if (clerkService.user || attempts >= maxAttempts) {
                        clearInterval(checkUser);
                        resolve();
                    }
                }, 100);
            });
        } catch (error) {
            console.error('Auth Guard - Error waiting for Clerk:', error);
        }
    }

    console.log('Auth Guard - User (after wait):', clerkService.user);

    if (clerkService.user) {
        console.log('Auth Guard - User authenticated, allowing access');
        return true;
    }

    // Redirect to home (landing page) if not authenticated
    console.log('Auth Guard - User not authenticated, redirecting to home');
    return router.createUrlTree(['/']);
};
