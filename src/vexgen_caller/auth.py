import utils.file_writer as writer
import os
import requests


def signup(email:str, password:str):
    url = os.getenv("VEXGEN_URL") + "auth/signup"
    if not email or not password:
        raise ValueError("Email and password must be provided for signup.")
    data = {"email": email, "password": password}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print("Signup successful.")
    except requests.exceptions.RequestException as e:   
        print(f"Signup failed: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        print(f"Signup failed: {str(e)}")
        
def login(email:str, password:str):
    url = os.getenv("VEXGEN_URL") + "auth/login"
    if not email or not password:
        raise ValueError("Email and password must be provided for login.")
    data = {"email": email, "password": password}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        
        # Get token from cookies
        token = response.cookies.get("access_token")
        refresh_token = response.cookies.get("refresh_token")
        writer.write_token_to_file(token, refresh_token, response.json().get("user_id"))
        
        print("Login successful.")
    except requests.exceptions.RequestException as e:   
        print(f"Login failed: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        print(f"Login failed: {str(e)}")
