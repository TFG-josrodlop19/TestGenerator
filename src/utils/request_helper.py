import requests

def get_request(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return (response.status_code, response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error in GET request {url}: {e}")
    
def post_request(url, data):
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return (response.status_code, response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error in POST request {url}: {e}")
        return (None, {"detail": [{"msg": str(e)}]})