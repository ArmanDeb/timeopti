import unittest
from datetime import datetime
from app.services.free_time_service import calculate_free_slots

class TestFreeTimeService(unittest.TestCase):
    
    def setUp(self):
        self.target_date = datetime(2023, 10, 27) # A random Friday

    def test_empty_day(self):
        """Test a day with no events, just sleep."""
        # Default sleep is 23:00-07:00. Day is 00:00-23:59.
        # So we expect free time from 07:00 to 23:00.
        slots = calculate_free_slots([], self.target_date)
        
        # Should be one big slot from 07:00 to 23:00 (16 hours = 960 mins)
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0].start, "07:00")
        self.assertEqual(slots[0].end, "23:00")
        self.assertEqual(slots[0].duration_minutes, 960)

    def test_events_splitting_day(self):
        """Test events that fragment the day."""
        events = [
            {"start_time": "09:00", "end_time": "10:00"}, # Meeting
            {"start_time": "12:00", "end_time": "13:00"}, # Lunch
        ]
        # Sleep 23:00-07:00
        # Expected Free:
        # 1. 07:00 - 09:00 (120m)
        # 2. 10:00 - 12:00 (120m)
        # 3. 13:00 - 23:00 (600m)
        
        slots = calculate_free_slots(events, self.target_date)
        self.assertEqual(len(slots), 3)
        
        self.assertEqual(slots[0].start, "07:00")
        self.assertEqual(slots[0].end, "09:00")
        
        self.assertEqual(slots[1].start, "10:00")
        self.assertEqual(slots[1].end, "12:00")
        
        self.assertEqual(slots[2].start, "13:00")
        self.assertEqual(slots[2].end, "23:00")

    def test_min_slot_filter(self):
        """Test that small slots are filtered out."""
        events = [
            {"start_time": "08:00", "end_time": "08:50"}, 
            # Gap 08:50-09:00 is 10 mins < 15 mins default
            {"start_time": "09:00", "end_time": "10:00"},
        ]
        
        slots = calculate_free_slots(events, self.target_date)
        
        # 07:00 - 08:00 (60m) -> Keep
        # 08:50 - 09:00 (10m) -> Discard
        # 10:00 - 23:00 (780m) -> Keep
        
        self.assertEqual(len(slots), 2)
        self.assertEqual(slots[0].start, "07:00")
        self.assertEqual(slots[0].end, "08:00")
        
        self.assertEqual(slots[1].start, "10:00")
        self.assertEqual(slots[1].end, "23:00")

    def test_overlapping_events(self):
        """Test that overlapping events merge correctly."""
        events = [
            {"start_time": "14:00", "end_time": "15:00"},
            {"start_time": "14:30", "end_time": "15:30"}, 
            # Effective busy: 14:00 - 15:30
        ]
        
        slots = calculate_free_slots(events, self.target_date)
        
        # Free: 07:00 - 14:00
        # Free: 15:30 - 23:00
        
        self.assertEqual(len(slots), 2)
        self.assertEqual(slots[0].end, "14:00")
        self.assertEqual(slots[1].start, "15:30")

if __name__ == '__main__':
    unittest.main()





