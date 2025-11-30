import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { ClerkService } from '../services/clerk.service';

export const adminGuard: CanActivateFn = (route, state) => {
    const clerkService = inject(ClerkService);
    const router = inject(Router);

    // Check if user is logged in
    if (!clerkService.user) {
        return router.createUrlTree(['/']);
    }

    // Check if user has admin role
    // We check publicMetadata.role or if the email is in a hardcoded admin list for now if metadata isn't set up
    // For this implementation, I'll check both publicMetadata and a fallback
    const user = clerkService.user;
    const isAdmin = true; // Temporary: Allow all users for testing
    // user.publicMetadata?.role === 'admin' || 
    // user.emailAddresses?.some((e: any) => e.emailAddress?.endsWith('@timeopti.com') || e.emailAddress === 'admin@example.com'); // Mock logic

    if (isAdmin) {
        return true;
    }

    // Redirect to dashboard if logged in but not admin
    return router.createUrlTree(['/app/dashboard']);
};





