import { Component, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ClerkService } from './services/clerk.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class AppComponent implements AfterViewInit {
  title = 'timeopti';
  @ViewChild('userButton') userButton!: ElementRef;

  constructor(public clerkService: ClerkService) { }

  ngAfterViewInit() {
    this.clerkService.mountUserButton(this.userButton.nativeElement);
  }
}
