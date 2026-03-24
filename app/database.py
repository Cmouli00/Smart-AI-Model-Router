# database.py
import os

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# Replace with your actual Postgres credentials
DATABASE_URL = os.getenv("POSTGRES_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    prompt_preview = Column(String)
    complexity_tag = Column(String)
    model_used = Column(String)
    cost_estimate = Column(Float)
    savings_estimate = Column(Float)
    score = Column(Float, nullable=True) # For the LLM-as-a-Judge
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)