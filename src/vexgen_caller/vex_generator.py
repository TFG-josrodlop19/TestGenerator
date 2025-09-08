import os
import requests
import json
import zipfile
from utils.file_writer import make_valid_file_path as sanitize_path
from utils.request_helper import authenticated_request
from utils.classes import ArtifactInfoVex
import shutil

def generate_download_path(owner:str, name:str) -> str:
    folder_name = f"{owner}/{name}"
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    general_vex_path = os.path.join(project_root, "generated_vex")
    return sanitize_path(folder_name, general_vex_path)

def generate_vex(owner:str, name:str):
    url = os.getenv("VEXGEN_URL") + "vexgen/vex_tix/generate"
    if not owner or not name:
        raise ValueError("Owner, name and SBOM path must be provided for VEX generation.")
    
    # Get user ID from json file
    token_file = os.path.expanduser(os.getenv("VEXGEN_TOKEN_FILE"))
    if not os.path.exists(token_file):
        raise FileNotFoundError(f"Token file not found: {token_file}")
    with open(token_file, 'r') as f:
        token_data = json.load(f)
        token = token_data.get("token")
        refresh_token = token_data.get("refresh_token")
        user_id = token_data.get("user_id")
        if not user_id:
            raise ValueError("User ID must be provided or found in the token file.")
        if not token:
            raise ValueError("Token must be provided or found in the token file.")
        if not refresh_token:
            raise ValueError("Refresh token must be provided or found in the token file.")
        
    
    data = {
        "owner": owner,
        "name": name,
        "user_id": user_id
    }
    
    try:
        response = authenticated_request("POST", url, token, refresh_token, data)
        response.raise_for_status()
        print("Vex generation successful.")
        # Check if response contains a file (zip)
        content_type = response.headers.get('content-type', '')
        if 'application/zip' in content_type:
            # Extract filename from content-disposition header
            content_disposition = response.headers.get('content-disposition')
            filename = 'vex_tix_sbom.zip'
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            
            # Create directory structure
            download_path = generate_download_path(owner, name)

            if os.path.exists(download_path):
                # Directory exists, clear its contents
                shutil.rmtree(download_path)
            
            # Create directory
            os.makedirs(download_path, exist_ok=True)

            # Full path for the zip file
            zip_path = os.path.join(download_path, filename)

            # Save the file
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            # Extract zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(download_path)
            print(f"TIX file downloaded to: {download_path}")

            # Remove the zip file after extraction
            os.remove(zip_path)
            
            # Remove extrafiles to only get one tix
            tix_found = False
            for item in os.listdir(download_path):
                item_path = os.path.join(download_path, item)
                if os.path.isfile(item_path):
                    if not tix_found and item.startswith('tix'):
                        tix_found = True
                    else:
                        os.remove(item_path)            
        else:
            raise ValueError("Response does not contain a valid VEX file: " + response.json().get('message', 'Unknown error'))
    except requests.RequestException as e:
        print(f"Error generating TIX: {response.json().get('detail', 'Unknown error')}")



def open_tix_file(owner:str, name:str) -> str:
    generate_download_path(owner, name)

    tix_file = None
    # In case there are multiple tix files, take the first one
    for item in os.listdir(generate_download_path(owner, name)):
        if item.startswith("tix") and item.endswith(".json"):
            tix_file = item
            break

    if not tix_file:
        raise FileNotFoundError("TIX file not found in the expected directory.")

    tix_path = os.path.join(generate_download_path(owner, name), tix_file)
    if not os.path.exists(tix_path):
        raise FileNotFoundError(f"TIX file not found: {tix_path}")
    with open(tix_path, 'r') as f:
        tix_data = json.load(f)

    if not tix_data:
        raise ValueError("TIX data is empty or invalid.")

    statements = tix_data.get("statements", [])
    
    artifacts = set()
    for statement in statements:
        reachable_code = statement.get("reachable_code")
        
        # If reachable_code is present, there is a possible vulnerable artifact
        if reachable_code:
            for file in reachable_code:
                
                file_path = file.get("path_to_file")
                if file_path and file_path.endswith('.java'):
                    used_artifacts = file.get("used_artifacts", [])
                    for artifact in used_artifacts:
                        artifact_name = artifact.get("artifact_name")
                        used_in_lines = artifact.get("used_in_lines", [])
                        for line in used_in_lines:
                            artifact_data = ArtifactInfoVex(
                                file_path=file_path,
                                target_line=line,
                                target_name=artifact_name
                            )
                            artifacts.add(artifact_data)
    
    # Convert to JSON format
    artifacts_list = []
    for artifact in artifacts:
        artifacts_list.append({
            "file_path": os.path.abspath(artifact.file_path),
            "target_line": str(artifact.target_line),
            "target_name": artifact.target_name
        })
        
    print(artifacts_list)
    
    # Return as JSON to use it on spoon
    return json.dumps(artifacts_list, indent=2)