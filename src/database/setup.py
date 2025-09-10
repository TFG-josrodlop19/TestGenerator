import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import Base

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATABASE_NAME = os.getenv("DATABASE_NAME", "testgenerator.db")
DB_PATH = PROJECT_ROOT / DATABASE_NAME
DATABASE_URL = f"sqlite:///{DB_PATH}"

def setup_database():
    """
    Configure and initialize the complete database
    Returns Session, engine and Base for later use
    """
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
    
    print(f"✅ Base de datos configurada en: {DB_PATH}")
    
    return Session, engine, Base

