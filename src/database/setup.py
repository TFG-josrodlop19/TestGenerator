import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from database.models import Base

# Global variables for database
engine = None
Session = None

def setup_database():
    """
    Configure and initialize the complete database
    Returns Session, engine and Base for later use
    """
    DATABASE_DIRECTORY = Path(__file__).parent.parent.parent / "database"
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    DB_PATH = DATABASE_DIRECTORY / DATABASE_NAME
    DATABASE_URL = f"sqlite:///{DB_PATH}"

    os.makedirs(DATABASE_DIRECTORY, exist_ok=True)

    global engine, Session
    
    # Create engine
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    # Thread-safe scoped session
    Session = scoped_session(session_factory)
    
    # Create database
    Base.metadata.create_all(bind=engine)

    
    return Session, engine, Base

def get_engine():
    """Get the database engine"""
    if engine is None:
        raise ValueError("Database is not initialized.")
    return engine

def get_session():
    """Get a new database session"""
    if Session is None:
        raise ValueError("Database is not initialized.")
    return Session()  # Return a new session instance

