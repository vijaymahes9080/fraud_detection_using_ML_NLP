import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Local database file path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "backend", "fraud_detection.db")

# Default local SQLite database URL
LOCAL_DATABASE_URL = f"sqlite:///{DB_PATH.replace('\\\\', '/').replace('\\', '/')}"

Base = declarative_base()

class ScanHistory(Base):
    """
    SQLAlchemy Database model to store details of scanned text, calls, and URLs.
    """
    __tablename__ = "scan_history"
    
    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String(50), nullable=False)               # SMS, Email, Call, URL, Scam
    input_content = Column(Text, nullable=False)                # Raw text or URL analyzed
    prediction = Column(String(50), nullable=False)             # Safe, Spam, Scam, Fraud, Phishing, Promotional
    risk_score = Column(Float, nullable=False)                  # Percentage (0.0 to 100.0)
    timestamp = Column(DateTime, default=datetime.utcnow)       # Scan timestamp
    db_mode = Column(String(50), default="Local (SQLite)")      # Mark whether scan saved locally or cloud

class AppConfig(Base):
    """
    SQLAlchemy Database model to store application configurations (like cloud DB URI).
    """
    __tablename__ = "app_config"
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)

class UserFeedback(Base):
    """
    SQLAlchemy Database model to store user feedback and model corrections.
    """
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_history_id = Column(Integer, nullable=False)
    channel = Column(String(50), nullable=False)
    input_content = Column(Text, nullable=False)
    original_prediction = Column(String(50), nullable=False)
    corrected_prediction = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


# Helper to initialize DB Engine based on Config (SQLite vs Cloud Database)
def get_db_engine():
    # Attempt to load cloud connection string from environment variable first
    cloud_url = os.getenv("DATABASE_URL")
    if cloud_url:
        print("Database Mode: Cloud database environment variable found.")
        try:
            return create_engine(cloud_url), "Cloud (PostgreSQL)"
        except Exception as e:
            print(f"Failed to connect to Cloud Database, falling back to local SQLite. Error: {e}")
            
    # Fallback to local SQLite
    return create_engine(LOCAL_DATABASE_URL, connect_args={"check_same_thread": False}), "Local (SQLite)"

# Initialize local engine for setup
engine, db_mode_str = get_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Creates tables in the database if they do not exist.
    """
    Base.metadata.create_all(bind=engine)
    print(f"Database tables initialized. Current mode: {db_mode_str}")

# Dependency to get db session in FastAPI endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
