import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';

@Component({
    selector: 'app-legal',
    standalone: true,
    imports: [CommonModule, RouterModule],
    templateUrl: './legal.html',
    styleUrl: './legal.css'
})
export class LegalComponent implements OnInit {
    title: string = '';
    type: 'privacy' | 'terms' = 'privacy';
    lastUpdated: string = new Date().toLocaleDateString();

    constructor(private route: ActivatedRoute) { }

    ngOnInit() {
        this.route.data.subscribe(data => {
            this.type = data['type'];
            this.title = this.type === 'privacy' ? 'Privacy Policy' : 'Terms of Service';
        });
    }
}
