from fastapi import APIRouter, Depends
from app.core.security import get_current_user

router = APIRouter()

@router.get("/protected")
def read_protected(user: dict = Depends(get_current_user)):
    return {"message": "You are authenticated", "user_id": user.get("sub")}
