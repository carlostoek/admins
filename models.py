#database/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    is_in_free_channel = Column(Boolean, default=False)
    join_date = Column(DateTime, default=datetime.datetime.utcnow)
    subscriptions = relationship("Subscription", back_populates="user")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="subscriptions")
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"))
    plan = relationship("SubscriptionPlan")
    
class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    duration_days = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    is_permanent = Column(Boolean, default=False)

class Token(Base):
    __tablename__ = "tokens"
    
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"))
    plan = relationship("SubscriptionPlan")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_used = Column(Boolean, default=False)
    used_by = Column(Integer, nullable=True)
    
class ScheduledMessage(Base):
    __tablename__ = "scheduled_messages"
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(String, nullable=False)
    text = Column(Text, nullable=True)
    media_type = Column(String, nullable=True)  # photo, video, file, etc.
    media_id = Column(String, nullable=True)
    is_protected = Column(Boolean, default=False)
    has_buttons = Column(Boolean, default=False)
    buttons_json = Column(Text, nullable=True)
    scheduled_time = Column(DateTime, nullable=False)
    is_recurring = Column(Boolean, default=False)
    recurring_pattern = Column(String, nullable=True)  # daily, weekly, etc.
    created_by = Column(Integer, ForeignKey("users.id"))