from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.all_models import User, AILog, Recommendation

router = APIRouter()

@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    """Get overall system statistics"""
    total_users = db.query(User).count()
    total_logs = db.query(AILog).count()
    total_recommendations = db.query(Recommendation).count()
    
    endpoint_stats = db.query(
        AILog.endpoint,
        func.count(AILog.id).label('count'),
        func.avg(AILog.duration_ms).label('avg_duration'),
        func.sum(AILog.cost).label('total_cost'),
        func.sum(AILog.tokens_used).label('total_tokens')
    ).group_by(AILog.endpoint).all()
    
    return {
        "total_users": total_users,
        "total_logs": total_logs,
        "total_recommendations": total_recommendations,
        "endpoint_stats": [
            {
                "endpoint": stat.endpoint,
                "count": stat.count,
                "avg_duration_ms": round(stat.avg_duration, 2) if stat.avg_duration else 0,
                "total_cost": round(stat.total_cost, 4) if stat.total_cost else 0,
                "total_tokens": stat.total_tokens if stat.total_tokens else 0
            }
            for stat in endpoint_stats
        ]
    }

@router.get("/logs")
def get_admin_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent AI logs"""
    logs = db.query(AILog).order_by(AILog.created_at.desc()).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "endpoint": log.endpoint,
                "duration_ms": log.duration_ms,
                "tokens_used": log.tokens_used,
                "model": log.model,
                "cost": log.cost,
                "error": log.error,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    }

@router.get("/users")
def get_admin_users(db: Session = Depends(get_db)):
    """Get all users with usage statistics"""
    users = db.query(User).all()
    
    result = []
    for user in users:
        # log_count = db.query(AILog).filter(AILog.user_id == user.id).count()
        # rec_count = db.query(Recommendation).filter(Recommendation.user_id == user.id).count()
        
        result.append({
            "id": str(user.id),
            "email": user.email,
            "clerk_id": user.clerk_user_id,
            "created_at": user.created_at.isoformat() if user.created_at else None
        })
    
    return {"users": result}
