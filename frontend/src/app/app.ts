import { Component, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ClerkService } from './services/clerk.service';

import { HttpClient } from '@angular/common/http';
import { environment } from '../environments/environment';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class AppComponent implements AfterViewInit {
  title = 'timeopti';
  backendMessage: string = 'Loading...';
  @ViewChild('userButton') userButton!: ElementRef;

  constructor(public clerkService: ClerkService, private http: HttpClient) {
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
}
