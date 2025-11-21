import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { ClerkService } from '../services/clerk.service';

export const authGuard: CanActivateFn = (route, state) => {
    const clerkService = inject(ClerkService);
    const router = inject(Router);

    if (clerkService.user) {
        return true;
    }

    // Redirect to home (landing page) if not authenticated
    return router.createUrlTree(['/']);
};
