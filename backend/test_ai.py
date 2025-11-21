import os
from dotenv import load_dotenv
from services.ai_service import AIService, AgendaRequest, Task

# Load env vars
load_dotenv()

def test_ai():
    print("Initializing AI Service...")
    service = AIService()
    
    tasks = [
        Task(id="1", title="Write code", duration_minutes=60, priority="high"),
        Task(id="2", title="Coffee break", duration_minutes=15, priority="medium")
    ]
    
    request = AgendaRequest(tasks=tasks, start_time="09:00", end_time="12:00")
    
    print("Sending request to OpenAI...")
    try:
        result = service.optimize_agenda(request)
        print("\n--- Result ---")
        print(result)
        print("--------------")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ai()
