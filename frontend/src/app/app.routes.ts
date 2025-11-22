import { Routes } from '@angular/router';
import { LandingComponent } from './landing/landing';
import { PricingComponent } from './pricing/pricing.component';
import { LegalComponent } from './legal/legal.component';
import { AppShellComponent } from './layout/app-shell';
import { DashboardComponent } from './dashboard/dashboard.component';
import { AdminComponent } from './admin/admin';
import { authGuard } from './guards/auth.guard';
import { adminGuard } from './guards/admin.guard';

export const routes: Routes = [
    // Public Routes
    { path: '', component: LandingComponent },
    { path: 'pricing', component: PricingComponent },
    { path: 'legal/mentions', component: LegalComponent, data: { type: 'mentions' } },
    { path: 'legal/privacy', component: LegalComponent, data: { type: 'privacy' } },

    // Protected Routes (App Shell)
    {
        path: 'app',
        component: AppShellComponent,
        canActivate: [authGuard],
        children: [
            { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
            { path: 'dashboard', component: DashboardComponent },
            { path: 'admin', component: AdminComponent, canActivate: [adminGuard] }
        ]
    },

    // Redirect legacy
    { path: 'privacy', redirectTo: 'legal/privacy' },
    { path: 'terms', redirectTo: 'legal/mentions' },
    { path: '**', redirectTo: '' }
];
