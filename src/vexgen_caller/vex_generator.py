import os
import requests
import json
import zipfile
from utils.file_writer import make_valid_file_path as sanitize_path
from utils.classes import ArtifactInfoVex

def generate_download_path(owner:str, name:str) -> str:
    folder_name = f"{owner}/{name}"
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    general_vex_path = os.path.join(project_root, "generated_vex")
    return sanitize_path(folder_name, general_vex_path)

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
            download_path = generate_download_path(owner, name)

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



def open_vex_file(owner:str, name:str) -> str:
    vex_path = os.path.join(generate_download_path(owner, name), "extended_vex.json")
    if not os.path.exists(vex_path):
        raise FileNotFoundError(f"VEX file not found: {vex_path}")
    with open(vex_path, 'r') as f:
        vex_data = json.load(f)
        
    if not vex_data:
        raise ValueError("VEX data is empty or invalid.")
    
    extended_statements = vex_data.get("extended_statements", [])
    
    artifacts = set()
    for statement in extended_statements:
        reachable_code = statement.get("reachable_code")
        
        # If reachable_code is present, there is a possible vulnerable artifact
        if reachable_code:
            for file in reachable_code:
                
                file_path = file.get("path_to_file")
                if file_path:  #and file_path.endswith('.java'):
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
            "file_path": artifact.file_path,
            "target_line": artifact.target_line,
            "target_name": artifact.target_name
        })
    
    # Return as JSON to use it on spoon
    return json.dumps(artifacts_list, indent=2)