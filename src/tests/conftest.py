import sys
from pathlib import Path
from dotenv import load_dotenv

import os
import pytest
load_dotenv()

current_dir = Path(__file__).parent
src_dir = current_dir.parent         
project_root = src_dir.parent        

sys.path.insert(0, str(src_dir))

from vexgen_caller.auth import login
from database.setup import setup_database

@pytest.fixture(scope="session", autouse=True)
def database():
    Session, engine, Base = setup_database()
    yield
    Base.metadata.drop_all(bind=engine)
    
@pytest.fixture(scope="session", autouse=True)
def auto_login():
    """Executes automatic login before any test runs."""
    # Testing credenctials
    test_email = os.getenv("TEST_EMAIL", "test@example.com")
    test_password = os.getenv("TEST_PASSWORD", "password")
    
    try:
        login(test_email, test_password)
    except Exception as e:
        print(f"Automatic login failed: {e}")
        
