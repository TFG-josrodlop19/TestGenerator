import os
import requests
import json


def generate_vex(owner:str, name:str, sbom_path:str):
    url = os.getenv("VEXGEN_URL") + "/vex/generate"
    if not owner or not name or not sbom_path:
        raise ValueError("Owner, name and SBOM path must be provided for VEX generation.")
    # Get user ID from json file
    token_file = os.path.expanduser(os.getenv("VEXGEN_TOKEN_FILE"))
    if not os.path.exists(token_file):
        raise FileNotFoundError(f"Token file not found: {token_file}")
    with open(token_file, 'r') as f:
        token_data = json.load(f)
        token = token_data.get("token")
        user_id = token_data.get("user_id")
        if not user_id:
            raise ValueError("User ID must be provided or found in the token file.")
        if not token:
            raise ValueError("Token must be provided or found in the token file.")
    data = {
        "owner": owner,
        "name": name,
        "sbom_path": sbom_path,
        "statements_group": "no_grouping",
        "user_id": user_id
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print("Vex generation successful.")
        # print(response.json())
    except requests.RequestException as e:
        print(f"Error generating VEX: {response.json().get('message', 'Unknown error')}")