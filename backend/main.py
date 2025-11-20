from fastapi import FastAPI, Depends
from auth import get_current_user

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World from TimeOpti Backend"}

@app.get("/protected")
def read_protected(user: dict = Depends(get_current_user)):
    return {"message": "You are authenticated", "user_id": user.get("sub")}
