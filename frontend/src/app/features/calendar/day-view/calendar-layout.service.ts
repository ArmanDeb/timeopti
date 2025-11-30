import { Injectable } from '@angular/core';
import { ScheduledTask } from '../../../core/services/view-state.service';

export interface CalendarEvent {
    id: string;
    title: string;
    start_time: string;
    end_time: string;
}

export interface DisplayEvent {
    id: string;
    title: string;
    start: string;
    end: string;
    type: 'google' | 'ai';
    data: any; // Original event or task object
    top: string;
    height: string;
    left: string;
    width: string;
    durationMinutes: number;
    colIndex?: number;
}

@Injectable({
    providedIn: 'root'
})
export class CalendarLayoutService {
    private readonly DRAG_STEP_MINUTES = 15;

    constructor() { }

    calculateLayout(
        events: CalendarEvent[],
        optimizedTasks: ScheduledTask[],
        currentDate: Date
    ): DisplayEvent[] {
        const googleEvents = events.map(e => ({
            id: e.id,
            title: e.title,
            start: e.start_time,
            end: e.end_time,
            type: 'google' as const,
            data: e
        }));

        // Filter AI tasks to only show those for the currently selected date
        const year = currentDate.getFullYear();
        const month = String(currentDate.getMonth() + 1).padStart(2, '0');
        const day = String(currentDate.getDate()).padStart(2, '0');
        const currentDateStr = `${year}-${month}-${day}`;

        const aiTasks = optimizedTasks
            .map((t, i) => ({ task: t, originalIndex: i }))
            .filter(item => {
                const t = item.task;
                if (!t.assigned_date) return false;
                const taskDateStr = t.assigned_date.split('T')[0].split(' ')[0];
                const matches = taskDateStr === currentDateStr;
                return matches;
            })
            .map((item, index) => {
                const t = item.task;
                const snappedStart = this.snapToStep(this.getMinutesFromTime(t.assigned_start_time));
                const snappedEndRaw = this.snapToStep(this.getMinutesFromTime(t.assigned_end_time));
                const snappedEnd = Math.max(snappedStart + this.DRAG_STEP_MINUTES, snappedEndRaw);
                const startTime = this.minutesToTime(snappedStart);
                const endTime = this.minutesToTime(snappedEnd);

                const baseId = t.id || t.slot_id || 'ai-task';
                const uniqueId = `${baseId}_${index}`;

                const normalizedTask = {
                    ...t,
                    assigned_start_time: startTime,
                    assigned_end_time: endTime,
                    id: baseId, // Keep original ID in data
                    _originalIndex: item.originalIndex // Store original index for updates
                };

                return {
                    id: uniqueId, // Use unique ID for display/drag
                    title: normalizedTask.task_name,
                    start: startTime,
                    end: endTime,
                    type: 'ai' as const,
                    data: normalizedTask
                };
            });

        const allItems = [...googleEvents, ...aiTasks];

        // 1. Convert times to minutes for easier calculation
        const itemsWithMinutes = allItems.map(item => {
            let startMin = this.getMinutesFromTime(item.start);
            let endMin = this.getMinutesFromTime(item.end);
            if (item.type === 'ai') {
                startMin = this.snapToStep(startMin);
                endMin = this.snapToStep(endMin);
            }
            const duration = endMin - startMin;
            // Visual end includes the minimum height (20px = 20min)
            const visualEndMin = Math.max(endMin, startMin + 20);

            return {
                ...item,
                startMin,
                endMin,
                visualEndMin,
                duration
            };
        }).sort((a, b) => a.startMin - b.startMin || (b.visualEndMin - b.startMin) - (a.visualEndMin - a.startMin));

        // 2. Group overlapping events
        const clusters: any[][] = [];
        let currentCluster: any[] = [];
        let clusterEnd = -1;

        for (const item of itemsWithMinutes) {
            if (currentCluster.length === 0) {
                currentCluster.push(item);
                clusterEnd = item.visualEndMin;
            } else {
                if (item.startMin < clusterEnd) {
                    // Overlaps with the current cluster (visually)
                    currentCluster.push(item);
                    clusterEnd = Math.max(clusterEnd, item.visualEndMin);
                } else {
                    // Starts after the current cluster ends
                    clusters.push(currentCluster);
                    currentCluster = [item];
                    clusterEnd = item.visualEndMin;
                }
            }
        }
        if (currentCluster.length > 0) {
            clusters.push(currentCluster);
        }

        // 3. Process each cluster to assign width and left position
        const displayEvents: DisplayEvent[] = [];

        for (const cluster of clusters) {
            for (const item of cluster) {
                // Calculate visual properties
                const top = `${item.startMin}px`; // 1 min = 1px
                const height = `${Math.max(20, item.duration)}px`; // Min height 20px
                const width = '100%';
                const left = '0%';

                displayEvents.push({
                    id: item.id,
                    title: item.title,
                    start: item.start,
                    end: item.end,
                    type: item.type,
                    data: item.data,
                    top,
                    height,
                    left,
                    width,
                    durationMinutes: item.duration
                });
            }
        }

        return displayEvents;
    }

    getMinutesFromTime(time: string): number {
        if (!time) return 0;

        if (time.includes('T')) {
            const match = time.match(/T(\d{2}):(\d{2})/);
            if (match) {
                return parseInt(match[1], 10) * 60 + parseInt(match[2], 10);
            }
            const date = new Date(time);
            if (!isNaN(date.getTime())) {
                return date.getHours() * 60 + date.getMinutes();
            }
        } else {
            const [h, m] = time.split(':').map(Number);
            return h * 60 + (m || 0);
        }
        return 0;
    }

    minutesToTime(totalMinutes: number): string {
        const minutes = Math.max(0, Math.min(1440, totalMinutes));
        const hrs = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;
    }

    snapToStep(minutes: number): number {
        const snapped = Math.round(minutes / this.DRAG_STEP_MINUTES) * this.DRAG_STEP_MINUTES;
        return Math.max(0, Math.min(1440, snapped));
    }

    getDurationMinutes(start: string, end: string): number {
        return this.getMinutesFromTime(end) - this.getMinutesFromTime(start);
    }
}
