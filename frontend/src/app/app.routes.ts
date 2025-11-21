import { Routes } from '@angular/router';
import { AdminComponent } from './admin/admin';
import { OptimizerComponent } from './optimizer/optimizer';
import { LandingComponent } from './landing/landing';
import { LegalComponent } from './legal/legal';
import { DashboardLayoutComponent } from './layout/dashboard-layout';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
    { path: '', component: LandingComponent },
    { path: 'privacy', component: LegalComponent, data: { type: 'privacy' } },
    { path: 'terms', component: LegalComponent, data: { type: 'terms' } },
    {
        path: '',
        component: DashboardLayoutComponent,
        canActivate: [authGuard],
        children: [
            { path: 'app', component: OptimizerComponent },
            { path: 'admin', component: AdminComponent }
        ]
    }
];
