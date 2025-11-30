import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON, Float, Uuid
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

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
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    scheduled_tasks = relationship("ScheduledTask", back_populates="user", cascade="all, delete-orphan")


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

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    priority = Column(String, nullable=False, default='medium')  # 'high', 'medium', 'low'
    deadline = Column(String, nullable=True)  # Optional deadline date string
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tasks")

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=True)
    task_name = Column(String, nullable=False)
    estimated_duration_minutes = Column(Integer, nullable=False)
    assigned_date = Column(String, nullable=False)  # YYYY-MM-DD format
    assigned_start_time = Column(String, nullable=False)  # HH:MM format
    assigned_end_time = Column(String, nullable=False)  # HH:MM format
    slot_id = Column(String, nullable=True)
    reasoning = Column(Text, nullable=True)  # AI explanation for placement
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="scheduled_tasks")
