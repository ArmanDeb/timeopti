from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta, time

class FreeSlot(BaseModel):
    id: str
    start: str  # HH:MM
    end: str    # HH:MM
    duration_minutes: int

class TimeInterval(BaseModel):
    start: datetime
    end: datetime

def parse_time(t_str: str) -> time:
    return datetime.strptime(t_str, "%H:%M").time()

def time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute

def calculate_free_slots(
    events: List[dict],
    target_date: datetime,
    day_start: str = "00:00",
    day_end: str = "23:59",
    sleep_start: str = "23:00",
    sleep_end: str = "07:00",
    min_slot_minutes: int = 15,
    start_from_now: bool = False
) -> List[FreeSlot]:
    """
    Calculate free time slots for a specific day by subtracting events and sleep from the full day.
    
    events: List of dicts with 'start_time' and 'end_time' in HH:MM or ISO format
    target_date: datetime object for the day to calculate
    """
    
    # 1. Define the full day range
    base_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    start_dt = datetime.combine(base_date, parse_time(day_start))
    end_dt = datetime.combine(base_date, parse_time(day_end))

    # If start_from_now is True and target_date is today, adjust start_dt
    if start_from_now:
        now = datetime.now()
        # Check if target_date is today (ignoring time)
        if base_date.date() == now.date():
            # Round up to next 15 mins for cleaner slots
            # or just use current time. Let's use current time but ensure it's not past day_end
            if now > start_dt:
                start_dt = max(start_dt, now)
            
            # If now is already past end_dt, no free slots today
            if start_dt >= end_dt:
                return []
    
    # 2. Collect all busy intervals (events + sleep)
    busy_intervals: List[TimeInterval] = []
    
    # Add Sleep Intervals
    # Sleep is typically overnight, so we might have:
    # - Morning sleep: 00:00 to sleep_end (if sleep_end < sleep_start)
    # - Evening sleep: sleep_start to 23:59
    
    s_start = parse_time(sleep_start)
    s_end = parse_time(sleep_end)
    
    # Check if sleep wraps around midnight
    if s_start > s_end:
        # Evening sleep (e.g. 23:00 to 23:59)
        busy_intervals.append(TimeInterval(
            start=datetime.combine(base_date, s_start),
            end=datetime.combine(base_date, time(23, 59, 59))
        ))
        # Morning sleep (e.g. 00:00 to 07:00)
        busy_intervals.append(TimeInterval(
            start=datetime.combine(base_date, time(0, 0)),
            end=datetime.combine(base_date, s_end)
        ))
    else:
        # Sleep is within the day (unlikely for sleep, but possible for other blocks)
        busy_intervals.append(TimeInterval(
            start=datetime.combine(base_date, s_start),
            end=datetime.combine(base_date, s_end)
        ))

    # Add Events
    for event in events:
        try:
            # Handle ISO strings or HH:MM
            e_start = event.get('start_time')
            e_end = event.get('end_time')
            
            if not e_start or not e_end:
                continue
                
            # Parse start
            if 'T' in e_start:
                dt_start = datetime.fromisoformat(e_start.replace('Z', '+00:00')).replace(tzinfo=None)
            else:
                dt_start = datetime.combine(base_date, parse_time(e_start))
                
            # Parse end
            if 'T' in e_end:
                dt_end = datetime.fromisoformat(e_end.replace('Z', '+00:00')).replace(tzinfo=None)
            else:
                dt_end = datetime.combine(base_date, parse_time(e_end))
            
            # Normalize to target day only
            # If event is outside target day, clamp or ignore
            
            # Clamp to day start/end
            eff_start = max(start_dt, dt_start)
            eff_end = min(end_dt, dt_end)
            
            if eff_start < eff_end:
                busy_intervals.append(TimeInterval(start=eff_start, end=eff_end))
                
        except Exception as e:
            print(f"Skipping malformed event: {event} - {e}")
            continue

    # 3. Merge overlapping intervals
    if not busy_intervals:
        # Whole day is free
        duration = int((end_dt - start_dt).total_seconds() / 60)
        if duration >= min_slot_minutes:
            return [FreeSlot(
                id="slot_1",
                start=start_dt.strftime("%H:%M"),
                end=end_dt.strftime("%H:%M"),
                duration_minutes=duration
            )]
        return []
        
    # Sort by start time
    busy_intervals.sort(key=lambda x: x.start)
    
    merged: List[TimeInterval] = []
    current = busy_intervals[0]
    
    for next_int in busy_intervals[1:]:
        if next_int.start <= current.end:
            # Overlap or adjacent, merge
            current.end = max(current.end, next_int.end)
        else:
            merged.append(current)
            current = next_int
    merged.append(current)
    
    # 4. Invert to find free slots
    free_slots: List[FreeSlot] = []
    cursor = start_dt
    
    slot_counter = 1
    
    for busy in merged:
        # Free time before this busy block?
        if cursor < busy.start:
            duration = int((busy.start - cursor).total_seconds() / 60)
            if duration >= min_slot_minutes:
                free_slots.append(FreeSlot(
                    id=f"slot_{slot_counter}",
                    start=cursor.strftime("%H:%M"),
                    end=busy.start.strftime("%H:%M"),
                    duration_minutes=duration
                ))
                slot_counter += 1
        cursor = max(cursor, busy.end)
        
    # Check remaining time after last busy block
    if cursor < end_dt:
        duration = int((end_dt - cursor).total_seconds() / 60)
        if duration >= min_slot_minutes:
            free_slots.append(FreeSlot(
                id=f"slot_{slot_counter}",
                start=cursor.strftime("%H:%M"),
                end=end_dt.strftime("%H:%M"),
                duration_minutes=duration
            ))

    return free_slots





