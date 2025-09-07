import os
import json
from unicodedata import normalize
import string
from pathlib import Path
from utils.classes import TestStatus

def write_token_to_file(token: str, refresh_token: str, user_id: str):
    try:
        file_path = os.getenv("VEXGEN_TOKEN_FILE")
        
        # Expand user home directory (~)
        file_path = os.path.expanduser(file_path)
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # Create JSON data
        token_data = {
            "user_id": user_id,
            "token": token,
            "refresh_token": refresh_token
        }
        
        # Create/write to file (automatically creates if doesn't exist)
        with open(file_path, 'w') as file:
            json.dump(token_data, file, indent=2)
        os.chmod(file_path, 0o600)

    except Exception as e:
        print(f"Failed to write token to file: {e}")
        
def update_token_in_file(token: str):
    try:
        file_path = os.getenv("VEXGEN_TOKEN_FILE")
        
        file_path = os.path.expanduser(file_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Token file not found: {file_path}")
        
        with open(file_path, 'r') as file:
            token_data = json.load(file)
            token_data['token'] = token
            
        with open(file_path, 'w') as file:
            json.dump(token_data, file, indent=2)
    except Exception as e:
        print(f"Failed to update token in file: {e}")

def os_path_separators():
    seps = []
    for sep in os.path.sep, os.path.altsep:
        if sep:
            seps.append(sep)
    return seps

def sanitise_filesystem_name(potential_file_path_name):
    # Sort out unicode characters
    valid_filename = normalize('NFKD', potential_file_path_name).encode('ascii', 'ignore').decode('ascii')
    # Replace path separators with underscores
    for sep in os_path_separators():
        valid_filename = valid_filename.replace(sep, '_')
    # Ensure only valid characters
    valid_chars = "-_.() {0}{1}".format(string.ascii_letters, string.digits)
    valid_filename = "".join(ch for ch in valid_filename if ch in valid_chars)
    # Ensure at least one letter or number to ignore names such as '..'
    valid_chars = "{0}{1}".format(string.ascii_letters, string.digits)
    test_filename = "".join(ch for ch in potential_file_path_name if ch in valid_chars)
    if len(test_filename) == 0:
        # Replace empty file name or file path part with the following
        valid_filename = "(Empty Name)"
    return valid_filename

def path_split_into_list(path):
    # Gets all parts of the path as a list, excluding path separators
    parts = []
    while True:
        newpath, tail = os.path.split(path)
        if newpath == path:
            assert not tail
            if path and path not in os_path_separators():
                parts.append(path)
            break
        if tail and tail not in os_path_separators():
            parts.append(tail)
        path = newpath
    parts.reverse()
    return parts

def sanitise_filesystem_path(potential_file_path):
    # Splits up a path and sanitises the name of each part separately
    path_parts_list = path_split_into_list(potential_file_path)
    sanitised_path = ''
    for path_component in path_parts_list:
        sanitised_path = '{0}{1}{2}'.format(sanitised_path, sanitise_filesystem_name(path_component), os.path.sep)
    return sanitised_path

def check_if_path_is_under(parent_path, child_path):
    # Using the function to split paths into lists of component parts, check that one path is underneath another
    child_parts = path_split_into_list(child_path)
    parent_parts = path_split_into_list(parent_path)
    if len(parent_parts) > len(child_parts):
        return False
    return all(part1==part2 for part1, part2 in zip(child_parts, parent_parts))

def make_valid_file_path(path, root_path):
    if path:
        sanitised_path = sanitise_filesystem_path(path)
        complete_path = os.path.join(root_path, sanitised_path)
    else:
        complete_path = complete_path
    complete_path = os.path.abspath(complete_path)
    if check_if_path_is_under(root_path, complete_path):
        return complete_path
    else:
        return None
    
    
def resolve_path(path: str, project_root: str) -> Path:
    """
    Resuelve una ruta relativa o absoluta y la convierte a Path absoluto.
    Si la ruta es relativa, la resuelve desde PROJECT_ROOT.
    """
    path_obj = Path(path)
    if path_obj.is_absolute():
        return path_obj
    else:
        # Si es relativa, probar primero desde PROJECT_ROOT
        project_path = project_root / path
        if project_path.exists():
            return project_path.resolve()
        # Si no existe, probar desde el directorio actual
        current_path = Path.cwd() / path
        return current_path.resolve()
    
    
def generate_path_repo(owner:str, name:str) -> str:
    """
    Generates a valid and secure path for the repository from its owner and name.
    """
    
    folder_name = f"{owner}_{name}".lower()
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    repo_path = os.path.join(project_root, "OSS-Fuzz", "projects")
    return make_valid_file_path(folder_name, repo_path)


def generate_test_info_path(owner:str, name:str) -> str:
    folder_name = f"{owner}/{name}"
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    info_path = os.path.join(project_root, "tests_info")
    return make_valid_file_path(folder_name, info_path)

def write_test_info_to_json(owner:str, name:str, info:dict):
    info_path = generate_test_info_path(owner, name)
    
    os.makedirs(info_path, exist_ok=True)
    
    file_path = os.path.join(info_path, "tests_info.json")
    
    with open(file_path, "w") as f:
        json.dump(info, f, indent=4)


def update_test_status(owner: str, name: str, artifact_key: str, test_path: str, new_status: TestStatus):
    try:
        current_info = read_test_info_from_json(owner, name)
        
        if artifact_key in current_info:
            tests = current_info[artifact_key].get("tests", [])
            updated = False
            
            # Buscar y actualizar el test por su test_path
            for i, call_stack in enumerate(tests):
                if call_stack != []:
                    for j, test in enumerate(call_stack):
                        if test and test.get("test_path") == test_path:
                            current_info[artifact_key]["tests"][i][j]["test_status"] = new_status
                            updated = True
                            break
                if updated:
                    break
            
            if updated:
                write_test_info_to_json(owner, name, current_info)
                print(f"Updated test status for {test_path}: {new_status}")
            else:
                print(f"Test not found: {test_path}")
        else:
            print(f"Artifact not found: {artifact_key}")
            
    except Exception as e:
        print(f"Error updating test status: {e}")
        raise


def read_test_info_from_json(owner:str, name:str) -> dict:
    info_path = generate_test_info_path(owner, name)
    info_path = os.path.join(info_path, "tests_info.json")
    if not os.path.exists(info_path):
        raise FileNotFoundError(f"Info file does not exist: {info_path}")
    with open(info_path, 'r') as f:
        info = json.load(f)
    return info    