import { Injectable, signal } from '@angular/core';

export type DashboardState = 'onboarding' | 'input' | 'results';

export interface ScheduleResult {
  summary: string;
  items: TimelineItem[];
}

export interface TimelineItem {
  id: string;
  startTime: string;
  endTime: string;
  title: string;
  type: 'context' | 'ai';
  source?: string; // e.g., "Google Calendar" or "Goal: Finish API"
}

export interface ScheduledTask {
  task_name: string;
  estimated_duration_minutes: number;
  assigned_date: string;
  assigned_start_time: string;
  assigned_end_time: string;
  slot_id: string;
  reasoning: string;
}

@Injectable({
  providedIn: 'root'
})
export class ViewStateService {
  // Core state - start with onboarding by default
  state = signal<DashboardState>('onboarding');
  
  // Data for Input state
  inputText = signal<string>('');
  
  // Data for Results state
  results = signal<ScheduleResult | null>(null);
  
  // Shared optimized tasks (visible in both optimizer and week-view)
  optimizedTasks = signal<ScheduledTask[]>([]);

  setState(newState: DashboardState) {
    this.state.set(newState);
  }
  
  setOptimizedTasks(tasks: ScheduledTask[]) {
    this.optimizedTasks.set(tasks);
    console.log('ViewStateService: optimizedTasks updated', tasks);
  }
  
  clearOptimizedTasks() {
    this.optimizedTasks.set([]);
  }

  reset() {
    this.state.set('onboarding');
    this.inputText.set('');
    this.results.set(null);
  }

  // Mock data for now, to be replaced by real backend call
  simulateOptimization(input: string) {
    // Here we would call the backend
    const mockResults: ScheduleResult = {
      summary: '3 tâches placées, 2h de Deep Work trouvées',
      items: [
        {
          id: '1',
          startTime: '09:00',
          endTime: '10:00',
          title: 'Daily Meeting',
          type: 'context',
          source: 'Google Calendar'
        },
        {
          id: '2',
          startTime: '10:00',
          endTime: '11:30',
          title: 'Finir l\'API FastAPI',
          type: 'ai',
          source: 'Objectif: Dev'
        },
        {
          id: '3',
          startTime: '12:00',
          endTime: '13:00',
          title: 'Déjeuner',
          type: 'context',
          source: 'Google Calendar'
        },
        {
          id: '4',
          startTime: '14:00',
          endTime: '14:45',
          title: 'Sport',
          type: 'ai',
          source: 'Objectif: Santé'
        }
      ]
    };
    
    this.results.set(mockResults);
    this.setState('results');
  }
}

