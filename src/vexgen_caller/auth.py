import utils.file_writer as writer
import os
import requests


def signup(email:str, password:str):
    url = os.getenv("VEXGEN_URL") + "/auth/signup"
    if not email or not password:
        raise ValueError("Email and password must be provided for signup.")
    data = {"email": email, "password": password}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:   
        print(f"Signup failed: {response.json().get('detail')[0].get('msg', 'Unknown error')}")
        
def login(email:str, password:str):
    url = os.getenv("VEXGEN_URL") + "/auth/login"
    if not email or not password:
        raise ValueError("Email and password must be provided for login.")
    data = {"email": email, "password": password}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print(response.json().get("access_token"))
        writer.write_token_to_file(response.json().get("access_token"))
    except requests.exceptions.RequestException as e:   
        print(f"Login failed: {response.json().get('detail')[0].get('msg', 'Unknown error')}")
