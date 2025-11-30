import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ClerkService } from '../../core/services/clerk.service';

@Component({
  selector: 'app-pricing',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="min-h-screen bg-white text-gray-900 font-sans py-20">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 class="text-4xl font-bold text-center mb-16">Investissez dans votre temps.</h1>
        
        <div class="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          
          <!-- Free Plan -->
          <div class="bg-white p-8 rounded-2xl border border-gray-200 shadow-sm">
            <h3 class="text-xl font-bold mb-4">Gratuit</h3>
            <div class="text-4xl font-bold mb-6">0€</div>
            <ul class="space-y-4 mb-8 text-gray-500">
              <li class="flex items-center gap-2">✓ 5 optimisations / semaine</li>
              <li class="flex items-center gap-2">✓ Lecture seule</li>
            </ul>
            <button (click)="clerkService.signIn()" class="w-full btn btn-secondary">S'inscrire</button>
          </div>

          <!-- Pro Plan -->
          <div class="bg-white p-8 rounded-2xl border-2 border-primary shadow-lg relative overflow-hidden">
            <div class="absolute top-0 right-0 bg-primary text-white text-xs font-bold px-3 py-1 rounded-bl-lg">POPULAIRE</div>
            <h3 class="text-xl font-bold mb-4 text-primary">Pro</h3>
            <div class="text-4xl font-bold mb-6">9€<span class="text-base font-normal text-gray-400">/mois</span></div>
            <ul class="space-y-4 mb-8 text-gray-500">
              <li class="flex items-center gap-2">✓ Optimisations illimitées</li>
              <li class="flex items-center gap-2">✓ Export Google Calendar</li>
              <li class="flex items-center gap-2">✓ Support prioritaire</li>
            </ul>
            <button (click)="clerkService.signIn()" class="w-full btn btn-primary">Passer Pro</button>
          </div>

        </div>
      </div>
    </div>
  `
})
export class PricingComponent {
  constructor(public clerkService: ClerkService) { }
}





