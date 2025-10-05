import sys
from pathlib import Path
from dotenv import load_dotenv

import os
import pytest
load_dotenv()

project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from src.vexgen_caller.auth import login

@pytest.fixture(scope="session", autouse=True)
def auto_login():
    """Executes automatic login before any test runs."""
    # Credenciales para testing (puedes configurarlas como env vars)
    test_email = os.getenv("TEST_EMAIL", "test@example.com")
    test_password = os.getenv("TEST_PASSWORD", "password")
    
    try:
        login(test_email, test_password)
    except Exception as e:
        print(f"Automatic login failed: {e}")