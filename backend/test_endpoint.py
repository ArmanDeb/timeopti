import sys
sys.path.insert(0, '/Users/arman/Documents/Projects/timeopti/backend')

from main import app
from app.services.ai_service import AgendaRequest, Task

# Test API call
request = AgendaRequest(
    tasks=[Task(id="1", title="Test task", duration_minutes=30, priority="high")],
    start_time="09:00",
    end_time="17:00"
)

from app.db.session import SessionLocal
db = SessionLocal()

try:
    from main import optimize_agenda
    result = optimize_agenda(request, db)
    print("Success:", result)
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
finally:
    db.close()
