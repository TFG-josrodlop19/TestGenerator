import requests
import os
from utils.file_writer import update_token_in_file

def authenticated_request(method: str, url:str, token:str, refresh_token:str, data:dict={}, refresh_retry=True) -> requests.Response:
    """
    Makes an authenticated HTTP request using the stored token.

    @param method: HTTP method (GET, POST, etc.)
    @param url: URL for the request
    @param token: Authentication token
    @param refresh_token: Refresh token (used for obtaining a new access token)
    @param data: Data to include in the request (optional)
    @param refresh_token: Only used in recursive calls to make a second try in case of token expiration (default: False)

    @return: response object
    """
    
    cookies = {
        "access_token": token
    }

    if not (method.upper() == "GET" or method.upper() == "POST"):
        raise ValueError("Only GET and POST methods are supported.")
    
    response = None
    
    if method.upper() == "GET":
        response = requests.get(url, cookies=cookies, params=data)
    elif method.upper() == "POST":
        response = requests.post(url, cookies=cookies, json=data)
        
    if response.status_code == 401 and refresh_retry:
        new_token  = refresh_token_vexgen(refresh_token)
        
        if new_token:
            response = authenticated_request(method, url, new_token, refresh_token, data, refresh_retry=False)
    return response
    
            

    
def refresh_token_vexgen(refresh_token:str) -> str:
    """
    Uses the refresh token to obtain a new access token. Also updates the token file.

    @param refresh_token: The refresh token

    Return: new access token
    """
    url = os.getenv("VEXGEN_URL") + "/auth/refresh_token"
    if not refresh_token:
        raise ValueError("Refresh token must be provided for refreshing the access token.")
    
    cookies = {
        "refresh_token": refresh_token
    }
    
    try:
        response = requests.post(url, cookies=cookies)
        response.raise_for_status()
        
        new_token = response.cookies.get("access_token")
        if not new_token or response.status_code == 200 and response.json().get("detail") == "token_invalid":
            raise ValueError("Please, login again")
        update_token_in_file(new_token)
        return new_token
        
    except requests.exceptions.RequestException as e:   
        print(f"Token refresh failed: {response.json().get('detail', 'Unknown error')}")
        raise ValueError(f"Token refresh failed: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        print(f"Token refresh failed: {str(e)}")
        return None