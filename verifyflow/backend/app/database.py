from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class QuestionnaireSession(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)

class ReferenceDocument(Base):
    __tablename__ = "reference_docs"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    filename = Column(String)
    parsed_text = Column(Text)

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    original_text = Column(Text)
    answer = Column(Text, nullable=True)
    citations = Column(JSON, default=list)
    confidence = Column(Integer, default=0)  # 0-100
    is_edited = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)