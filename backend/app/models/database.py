from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    access_token = Column(String)
    refresh_token = Column(String)
    token_expiry = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    flags = relationship("EmailFlag", back_populates="user")
    flag_history = relationship("FlagHistory", back_populates="user")

class EmailFlag(Base):
    __tablename__ = "email_flags"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    flag_name = Column(String)
    flag_criteria = Column(String)  # Search query for this flag
    label_id = Column(String)  # Gmail label ID
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="flags")
    history = relationship("FlagHistory", back_populates="flag")

class FlagHistory(Base):
    __tablename__ = "flag_history"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    flag_id = Column(String, ForeignKey("email_flags.id"))
    message_id = Column(String)  # Gmail message ID
    action = Column(String)  # "applied" or "removed"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="flag_history")
    flag = relationship("EmailFlag", back_populates="history") 