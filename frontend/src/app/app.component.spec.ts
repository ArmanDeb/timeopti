import { TestBed } from '@angular/core/testing';
import { AppComponent } from './app';
import { ClerkService } from './core/services/clerk.service';
import { HttpClient } from '@angular/common/http';
import { AgendaService } from './core/services/agenda.service';
import { Router } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';

describe('AppComponent', () => {
    beforeEach(async () => {
        const clerkServiceMock = {
            mountUserButton: vi.fn(),
            initialize: vi.fn(),
            user: null,
            session: null
        };

        const httpClientMock = {
            get: vi.fn().mockReturnValue(of({ message: 'Mock backend' }))
        };

        const agendaServiceMock = {};

        const routerMock = {
            url: '/',
            events: of(null)
        };

        await TestBed.configureTestingModule({
            imports: [AppComponent],
            providers: [
                { provide: ClerkService, useValue: clerkServiceMock },
                { provide: HttpClient, useValue: httpClientMock },
                { provide: AgendaService, useValue: agendaServiceMock },
                { provide: Router, useValue: routerMock }
            ]
        }).compileComponents();
    });

    it('should create the app', () => {
        const fixture = TestBed.createComponent(AppComponent);
        const app = fixture.componentInstance;
        expect(app).toBeTruthy();
    });
});
