from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    sessions = relationship("QuestionnaireSession", back_populates="owner")

class QuestionnaireSession(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="sessions")
    questions = relationship("Question", back_populates="session")
    reference_docs = relationship("ReferenceDocument", back_populates="session")

class ReferenceDocument(Base):
    __tablename__ = "reference_docs"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    filename = Column(String)
    parsed_text = Column(Text)
    session = relationship("QuestionnaireSession", back_populates="reference_docs")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    original_text = Column(Text)
    answer = Column(Text, nullable=True)
    citations = Column(JSON, default=list)
    confidence = Column(Integer, default=0)
    is_edited = Column(Boolean, default=False)
    session = relationship("QuestionnaireSession", back_populates="questions")