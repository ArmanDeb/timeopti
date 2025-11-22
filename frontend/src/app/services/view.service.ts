import { Injectable, signal } from '@angular/core';

export type ViewMode = 'Day' | 'Week';

@Injectable({
    providedIn: 'root'
})
export class ViewService {
    viewMode = signal<ViewMode>('Day');
    currentDate = signal<Date>(new Date());

    setViewMode(mode: ViewMode) {
        this.viewMode.set(mode);
    }

    setDate(date: Date) {
        this.currentDate.set(date);
    }

    nextPeriod() {
        const current = this.currentDate();
        const mode = this.viewMode();
        const next = new Date(current);

        if (mode === 'Day') {
            next.setDate(current.getDate() + 1);
        } else {
            next.setDate(current.getDate() + 7);
        }
        this.currentDate.set(next);
    }

    previousPeriod() {
        const current = this.currentDate();
        const mode = this.viewMode();
        const prev = new Date(current);

        if (mode === 'Day') {
            prev.setDate(current.getDate() - 1);
        } else {
            prev.setDate(current.getDate() - 7);
        }
        this.currentDate.set(prev);
    }

    goToToday() {
        this.currentDate.set(new Date());
    }
}

