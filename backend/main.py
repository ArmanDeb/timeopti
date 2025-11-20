from fastapi import FastAPI, Depends
from auth import get_current_user

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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

@app.get("/")
def read_root():
    return {"message": "Hello World from TimeOpti Backend"}

@app.get("/protected")
def read_protected(user: dict = Depends(get_current_user)):
    return {"message": "You are authenticated", "user_id": user.get("sub")}
