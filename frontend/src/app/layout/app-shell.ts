import { Component, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ClerkService } from '../services/clerk.service';

@Component({
    selector: 'app-shell',
    standalone: true,
    imports: [CommonModule, RouterModule],
    templateUrl: './app-shell.html',
})
export class AppShellComponent implements AfterViewInit {
    @ViewChild('userButton') userButtonContainer!: ElementRef;

    constructor(public clerkService: ClerkService) { }

    ngAfterViewInit() {
        if (this.clerkService.clerk && this.userButtonContainer) {
            this.clerkService.clerk.mountUserButton(this.userButtonContainer.nativeElement);
        }
    }

    get isAdmin(): boolean {
        const user = this.clerkService.user;
        if (!user) return false;

        return true; // Temporary: Allow all users to see admin link for testing
        // user.publicMetadata?.role === 'admin' || 
        // user.emailAddresses?.some((e: any) => e.emailAddress?.endsWith('@timeopti.com') || e.emailAddress === 'admin@example.com');
    }
}
