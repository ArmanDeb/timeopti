import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON, Float, Uuid
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    clerk_user_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    calendar_tokens = Column(JSON, nullable=True)  # Store Google Calendar OAuth tokens
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ai_logs = relationship("AILog", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")


class AILog(Base):
    __tablename__ = "ai_logs"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=True)
    endpoint = Column(String, nullable=False)  # /optimize, /analyze/gaps, etc.
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    model = Column(String, nullable=True)
    cost = Column(Float, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="ai_logs")
    recommendation = relationship("Recommendation", back_populates="log", uselist=False)

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=True)
    log_id = Column(Uuid, ForeignKey("ai_logs.id"), nullable=True)
    recommendation_text = Column(Text, nullable=False)
    tasks_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="recommendations")
    log = relationship("AILog", back_populates="recommendation")
