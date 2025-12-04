#!/usr/bin/env python3
"""
Test script for AI-powered natural language scheduling
"""

import requests
import json
from datetime import datetime

API_URL = "http://localhost:8001"

def test_natural_optimize(input_text: str):
    """Test the natural language optimization endpoint"""
    print(f"\n{'='*80}")
    print(f"🧪 Testing: '{input_text}'")
    print(f"{'='*80}\n")
    
    # Sample calendar events (simulating existing schedule)
    sample_events = [
        {"title": "Team Meeting", "start_time": "10:00", "end_time": "11:00"},
        {"title": "Lunch Break", "start_time": "13:00", "end_time": "14:00"},
        {"title": "Client Call", "start_time": "16:00", "end_time": "17:00"}
    ]
    
    payload = {
        "natural_input": input_text,
        "scope": "today",
        "start_window": "08:00",
        "end_window": "20:00",
        "events": sample_events
    }
    
    try:
        response = requests.post(
            f"{API_URL}/smart-optimize-natural",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ SUCCESS!\n")
            
            # Display parsed tasks
            if result.get('parsed_tasks'):
                print("📋 Parsed Tasks:")
                for task in result['parsed_tasks']:
                    print(f"  • {task['title']}")
                    print(f"    Duration: {task['duration_minutes']}min")
                    print(f"    Priority: {task['priority']}")
                    print(f"    Time Preference: {task.get('time_preference', 'any')}")
                    if task.get('reasoning'):
                        print(f"    Reasoning: {task['reasoning']}")
                    print()
            
            # Display schedule
            schedule = result['schedule']
            print(f"📅 Scheduled Tasks ({len(schedule['scheduled_tasks'])} tasks):")
            for st in schedule['scheduled_tasks']:
                task = st['task']
                print(f"\n  ⏰ {st['start_time']} - {st['end_time']}")
                print(f"     {task['title']} ({task['duration_minutes']}min)")
                print(f"     Priority: {task['priority']}")
                print(f"     Fit Score: {st['fit_score']:.2f}")
                if st.get('explanation'):
                    print(f"     💡 {st['explanation']}")
            
            # Display unscheduled
            if schedule['unscheduled_tasks']:
                print(f"\n⚠️  Unscheduled Tasks ({len(schedule['unscheduled_tasks'])}):")
                for task in schedule['unscheduled_tasks']:
                    print(f"  • {task['title']} ({task['duration_minutes']}min)")
            
            # Display AI explanation
            if schedule.get('explanation'):
                print(f"\n🤖 AI Explanation:")
                print(f"   {schedule['explanation']}")
            
        else:
            print(f"❌ ERROR {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

def main():
    print("\n" + "="*80)
    print("🤖 AI-Powered Natural Language Scheduler - Test Suite")
    print("="*80)
    
    test_cases = [
        "today I want to have breakfast and study",
        "I need to exercise and have lunch",
        "tomorrow I want to finish my project and visit a friend",
        "this week I have to go to the gym 3 times",
        "I need to have breakfast, study for 2 hours, and meet a friend for coffee"
    ]
    
    for test_input in test_cases:
        test_natural_optimize(test_input)
        input("\nPress Enter to continue to next test...")
    
    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()





