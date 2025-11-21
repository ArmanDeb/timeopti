import { Component, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ClerkService } from './services/clerk.service';
import { HttpClient } from '@angular/common/http';
import { environment } from '../environments/environment';
import { AgendaService, AgendaRequest, Task } from './services/agenda.service';
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
  tasksInput: string = 'Write report (60m) [high]\nEmail team (30m) [medium]';
  optimizedResult: string = '';
  isLoadingAI: boolean = false;

  @ViewChild('userButton') userButton!: ElementRef;

  constructor(
    public clerkService: ClerkService,
    private http: HttpClient,
    private agendaService: AgendaService
  ) {
    this.fetchBackendMessage();
  }

  ngAfterViewInit() {
    this.clerkService.mountUserButton(this.userButton.nativeElement);
  }

  fetchBackendMessage() {
    this.http.get<{ message: string }>(`${environment.apiUrl}/`)
      .subscribe({
        next: (data) => this.backendMessage = data.message,
        error: (err) => this.backendMessage = 'Error connecting to backend'
      });
  }

  optimizeAgenda() {
    this.isLoadingAI = true;
    const tasks: Task[] = this.tasksInput.split('\n').map((line, index) => {
      // Very basic parsing for demo
      return {
        id: index.toString(),
        title: line,
        duration_minutes: 30, // Default
        priority: 'medium'
      };
    });

    const request: AgendaRequest = {
      tasks: tasks,
      start_time: '09:00',
      end_time: '17:00'
    };

    this.agendaService.optimizeAgenda(request).subscribe({
      next: (res) => {
        this.optimizedResult = res.optimized_agenda;
        this.isLoadingAI = false;
      },
      error: (err) => {
        console.error(err);
        this.optimizedResult = 'Error optimizing agenda.';
        this.isLoadingAI = false;
      }
    });
  }
}
