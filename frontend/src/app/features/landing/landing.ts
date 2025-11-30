import { Component, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ClerkService } from '../../core/services/clerk.service';

@Component({
    selector: 'app-landing',
    standalone: true,
    imports: [CommonModule, RouterModule],
    templateUrl: './landing.html',
    styleUrl: './landing.css'
})
export class LandingComponent implements AfterViewInit {
    @ViewChild('userButton') userButton!: ElementRef;

    constructor(public clerkService: ClerkService) { }

    ngAfterViewInit() {
        if (this.userButton) {
            this.clerkService.mountUserButton(this.userButton.nativeElement);
        }
    }

    scrollToSection(sectionId: string) {
        const element = document.getElementById(sectionId);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    }
}
