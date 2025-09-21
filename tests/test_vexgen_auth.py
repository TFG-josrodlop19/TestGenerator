import pytest
import os
import json
from src.vexgen_caller.auth import login

def test_prueba():
    assert True
    
def test_login():
    login("test@example.com", "password")
    token_file = os.path.expanduser(os.getenv("VEXGEN_TOKEN_FILE"))
    if not os.path.exists(token_file):
        raise FileNotFoundError(f"Token file not found: {token_file}")
    with open(token_file, 'r') as f:
        token_data = json.load(f)
        token = token_data.get("token")
        refresh_token = token_data.get("refresh_token")
        user_id = token_data.get("user_id")
        assert user_id is not None
        assert token is not None
        assert refresh_token is not None
    