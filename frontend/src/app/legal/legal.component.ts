import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-legal',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="min-h-screen bg-white text-gray-900 font-sans py-20">
      <div class="max-w-3xl mx-auto px-4 prose prose-sm">
        <h1 class="text-3xl font-bold mb-8 capitalize">{{ type === 'mentions' ? 'Mentions Légales' : 'Politique de Confidentialité' }}</h1>
        
        <div *ngIf="type === 'mentions'">
          <p>Éditeur : TimeAgent SAS<br>Siège social : Paris, France<br>Contact : support@timeagent.app</p>
          <!-- Add more legal text -->
        </div>

        <div *ngIf="type === 'privacy'">
          <h2>1. Données collectées</h2>
          <p>Nous collectons uniquement les données nécessaires à l'optimisation de votre agenda via l'API Google Calendar. Ces données ne sont pas revendues.</p>
          <h2>2. Sous-traitants</h2>
          <p>Auth : Clerk<br>AI : OpenRouter</p>
        </div>
      </div>
    </div>
  `
})
export class LegalComponent {
  type: string = '';

  constructor(private route: ActivatedRoute) {
    this.route.data.subscribe(data => {
      this.type = data['type'];
    });
  }
}





