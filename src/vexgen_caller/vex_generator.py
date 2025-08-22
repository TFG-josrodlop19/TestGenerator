import os
import requests
import json
import zipfile
from utils.file_writer import make_valid_file_path as sanitize_path


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
        
        # Check if response contains a file (zip)
        content_type = response.headers.get('content-type', '')
        if 'application/zip' in content_type:
            # Extract filename from content-disposition header
            content_disposition = response.headers.get('content-disposition')
            filename = 'vex.zip'
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            
            # Create directory structure
            folder_name = f"{owner}_{name}"
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

            general_vex_path = os.path.join(project_root, "generated_vex")
            
            download_path = sanitize_path(folder_name, general_vex_path) 
            
            # Create directory if it doesn't exist
            os.makedirs(download_path, exist_ok=True)

            # Full path for the zip file
            zip_path = os.path.join(download_path, filename)

            # Save the file
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            # Extract zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(download_path)
            print(f"VEX file downloaded to: {download_path}")

            # Remove the zip file after extraction
            os.remove(zip_path)
            
            # Remove vex.json file if it exists, only need extended_vex.json
            vex_json_path = os.path.join(download_path, "vex.json")
            if os.path.exists(vex_json_path):
                os.remove(vex_json_path)
            
        else:
            raise ValueError("Response does not contain a valid VEX file.")
    except requests.RequestException as e:
        print(f"Error generating VEX: {response.json().get('message', 'Unknown error')}")

def download_vex(vex_id: str):
    url = os.getenv("VEXGEN_URL") + f"/vex/download/{vex_id}"
    if not vex_id:
        raise ValueError("VEX ID must be provided for downloading VEX.")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("Vex download successful.")
        # print(response.json())
    except requests.RequestException as e:
        print(f"Error downloading VEX: {response.json().get('message', 'Unknown error')}")
        
        
def list_vex():
    # Get user ID from json file
    token_file = os.path.expanduser(os.getenv("VEXGEN_TOKEN_FILE"))
    if not os.path.exists(token_file):
        raise FileNotFoundError(f"Token file not found: {token_file}")
    with open(token_file, 'r') as f:
        token_data = json.load(f)
        user_id = token_data.get("user_id")
        if not user_id:
            raise ValueError("User ID must be provided or found in the token file.")
        
    url = os.getenv("VEXGEN_URL") + "/vex/user/" + user_id
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("Vex list successful.")
        print(response.json())
    except requests.RequestException as e:
        print(f"Error listing VEX: {response.json().get('message', 'Unknown error')}")