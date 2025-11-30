from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine, Base
from app.api.v1.router import api_router
from app.core.exceptions import TimeOptiException

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TimeOpti API")

# Configure CORS
origins = [
    "http://localhost:4200",
    "https://timeopti.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(TimeOptiException)
async def timeopti_exception_handler(request: Request, exc: TimeOptiException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )

@app.get("/")
def read_root():
    return {"message": "Hello World from TimeOpti Backend"}

# Include API router
app.include_router(api_router)
