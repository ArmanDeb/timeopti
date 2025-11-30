import { Component, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { RouterOutlet, RouterLink, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ClerkService } from './core/services/clerk.service';
import { HttpClient } from '@angular/common/http';
import { environment } from '../environments/environment';
import { AgendaService, AgendaRequest, Task } from './core/services/agenda.service';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class AppComponent implements AfterViewInit {
  title = 'timeopti';
  backendMessage: string = 'Loading...';

  // AI Demo Data
  tasksInput: string = 'Write report (60m) [high]\\nEmail team (30m) [medium]';
  optimizedResult: string = '';
  isLoadingAI: boolean = false;

  @ViewChild('userButton') userButton!: ElementRef;

  constructor(
    public clerkService: ClerkService,
    private http: HttpClient,
    private agendaService: AgendaService,
    private router: Router
  ) {
    this.fetchBackendMessage();
  }

  ngAfterViewInit() {
    if (this.userButton) {
      try {
        this.clerkService.mountUserButton(this.userButton.nativeElement);
      } catch (e) {
        console.error('Error mounting user button:', e);
      }
    }
  }

  isAdminRoute(): boolean {
    return this.router.url.includes('/admin');
  }

  fetchBackendMessage() {
    this.http.get<{ message: string }>(`${environment.apiUrl}/`)
      .subscribe({
        next: (data) => this.backendMessage = data.message,
        error: (err) => this.backendMessage = 'Error connecting to backend'
      });
  }
}
